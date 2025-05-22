import os
import json
import pandas as pd
import torch
import onnx
from ezkl import ezkl
import time
import sys
from models.olap_cube import OLAPCube
from operations.slicing_model import SlicingModel
from operations.dicing_model import DicingModel
from operations.roll_up_model import RollUpModel
import asyncio
from ezkl_workflow.generate_proof import generate_proof
from hash_utils import verify_dataset_hash, verify_query_allowed, publish_hash
from data_generators.CSV_Generator1 import generate_CSV_1
from data_generators.CSV_Generator2 import generate_CSV_2

output_dir = './output'
os.makedirs(output_dir, exist_ok=True)

def load_contract_address(contract_name):
    """Load the contract address from the configuration file."""
    config_path = os.path.join(os.path.dirname(__file__), 'config', 'contract_addresses.json')
    with open(config_path, 'r') as f:
        contract_addresses = json.load(f)
    return contract_addresses.get(contract_name)

# Load the DataFactModel contract address dynamically
data_fact_model_address = load_contract_address("DataFactModel")
if not data_fact_model_address:
    print("DataFactModel address not found in configuration.")
    sys.exit(1)

def op_generate_file():
    print("\nSelect a generator to use:")
    print("[1] Generator 1")
    print("[2] Generator 2")
    generator_choice = input("Enter your choice (1 or 2): ")

    if generator_choice == "1":
        generate_CSV_1(1000, 1, output_file="GHGe1.csv") # CSV_Generator1.py
        print("File generated with Generator 1.")
    elif generator_choice == "2":
        generate_CSV_2(1000, 1, output_file="GHGe2.csv") # CSV_Generator2.py
        print("File generated with Generator 2.")
    else:
        print("Invalid choice. Returning to previous menu.")
    

def CLI_publish_hash():
    # Make the user select a file to publish with CLI
    uploaded_files_dir = os.path.join('data', 'uploaded')
    files = os.listdir(uploaded_files_dir)
    if not files:
        print("No files available in the uploaded directory.")
        return
    print("Available files:")
    for idx, file in enumerate(files):
        print(f"[{idx + 1}] {file}")
    file_index = int(input("Select a file to publish by index: ")) - 1
    if file_index < 0 or file_index >= len(files):
        print("Invalid index selected.")
        return
    file_path = os.path.join(uploaded_files_dir, files[file_index])

    hash = op_publish_hash(file_path) # MAIN.py

    # Save the hash in "published_hash.json" to share it with the customer
    published_hash_path = os.path.join('data', 'published_hash.json')
    os.makedirs(os.path.dirname(published_hash_path), exist_ok=True)  # Ensure the directory exists

    # Create the file if it doesn't exist
    if not os.path.exists(published_hash_path):
        with open(published_hash_path, 'w') as f:
            json.dump({}, f, indent=4)

    # Read the existing published hashes
    with open(published_hash_path, 'r') as f:
        published_hashes = json.load(f)
    # Add or update the hash for the selected file
    published_hashes[files[file_index]] = hash
    # Write the updated hashes back to the file
    with open(published_hash_path, 'w') as f:
        json.dump(published_hashes, f, indent=4)

    print(f"Hash for {files[file_index]} published successfully.")

def op_publish_hash(file_path):
    return publish_hash(file_path) # HASH_UTILS.py

# ??
def op_verify_dataset_hash():
    try:
        published_hash_path = os.path.join('data', 'published_hash.json')
        if not os.path.exists(published_hash_path):
            print("\nNo published hashes found.")
            return

        with open(published_hash_path, 'r') as f:
            published_hashes = json.load(f)

        if not published_hashes:
            print("\nNo hashes available in the published file.")
            return

        print("\nAvailable published hashes:")
        for idx, (file_name, hash_value) in enumerate(published_hashes.items()):
            print(f"[{idx + 1}] File: {file_name} - Hash: {hash_value}")

        file_index = int(input("Select a file to verify by index: ")) - 1
        if file_index < 0 or file_index >= len(published_hashes):
            print("Invalid index selected.")
            return

        selected_file = list(published_hashes.keys())[file_index]
        selected_hash = published_hashes[selected_file]

        file_path = os.path.join('data', 'uploaded', selected_file)

        verify_dataset_hash(file_path)
        print(f"Hash for {selected_file} verified successfully ({selected_hash}).")
    except Exception as e:
        print(f"Failed to verify hash: {e}")

# This function applies a sequence of OLAP operations to a data tensor using an OLAP cube object:
# - cube instance of OLAPCube from olap_cube.py -> tell how to apply OLAP operations to the data
# - tensor_data: the data tensor to be processed
# - operations: a list of OLAP operations to be applied
def apply_olap_operations(cube, tensor_data, operations):
    result_tensor = tensor_data
    for operation in operations:
        result_tensor = cube.execute_model(operation, result_tensor)
    return result_tensor

async def op_perform_query(file_path, selected_file):
    df = pd.read_csv(file_path)
    df = df.dropna() # Drop rows with NaN values

    # Initialize the OLAP cube and transform the data into a tensor
    cube = OLAPCube(df)
    tensor_data = cube.to_tensor()

    print(f"DataFrame after dropping NaN values: \n {df}")
    print(f"cube: {cube}")

    # Define the list of OLAP operations to apply
    """
    operations = [
        # SlicingModel and DicingModel are subclasses of OLAPOperation
        # {14: 1, 21: 12, 27: 0} is a dictionary where the keys are column indices and the values are the values to filter by
        SlicingModel({14: 1, 21: 12, 27: 0}),  # Slicing operation: select rows where column 14 is ==1, ...
        DicingModel({2: 2, 21: [3, 4], 27: 4})  # Dicing operation
    ]
    """

    operations = [
        SlicingModel({2:0})
    ]

    # Apply the operations to the tensor data
    final_tensor = apply_olap_operations(cube, tensor_data, operations)

    print(f"Iniital tensor:\n{tensor_data}")
    print(f"Final tensor:\n{final_tensor}")


    # Export the model in ONNX format
    # Selects the last operation in your OLAP pipeline. This is the model you want to export
    final_operation = operations[-1]  
    # ONNX export requires the model and the input tensor to be on the same device (usually CPU for interoperability), we move the model to CPU
    final_operation.to(torch.device("cpu"))
    # Sets the model to evaluation mode
    final_operation.eval()

    model_onnx_path = os.path.join(output_dir, 'model.onnx')
    torch.onnx.export(final_operation,               # model being run
                      tensor_data,                   # model input (or a tuple for multiple inputs)
                      model_onnx_path,               # where to save the model (can be a file or file-like object)
                      export_params=True,            # store the trained parameter weights inside the model file
                      opset_version=11,              # the ONNX version to export the model to
                      do_constant_folding=True,      # whether to execute constant folding for optimization
                      input_names=['input'],         # the model's input names
                      output_names=['output'])       # the model's output names

    onnx_model = onnx.load(model_onnx_path)
    onnx.checker.check_model(onnx_model)
    # print(onnx.helper.printable_graph(onnx_model.graph))

    # Take PyTorch tensor - detach it from any computation graph - convert it to a NumPy array - flatten it to 1D 
    d = ((tensor_data).detach().numpy()).reshape([-1])
    # Create a dictionary "data"
    data = dict(
        input_shapes=[tensor_data.shape], # shape = how many elements along each axis
        input_data=[d.tolist()],
        output_data=[final_tensor.detach().numpy().reshape([-1]).tolist()]
    )
    input_json_path = os.path.join(output_dir, 'input.json')
    with open(input_json_path, 'w') as f:
        json.dump(data, f) # serialize the data dictionary to a JSON file

    #await generate_proof(output_dir, model_onnx_path, input_json_path, logrows=17)
    await generate_proof(output_dir, model_onnx_path, input_json_path, logrows=15)

    # Remove rows from final_tensor that are all zeros
    non_zero_rows = ~torch.all(final_tensor == 0, dim=1)
    final_tensor = final_tensor[non_zero_rows]

    # Save the final tensor as a CSV file after the query
    final_df = pd.DataFrame(final_tensor.detach().numpy())
    print(f"Final DataFrame:\n{final_df}")

    final_decoded_df = cube.decode_categorical_columns()
    print(f"Final Decoded DataFrame:\n{final_decoded_df}")

    mod_selected_file = "mod_" + selected_file
    csv_output_path = os.path.join('data', 'modified', mod_selected_file)
    os.makedirs(os.path.dirname(csv_output_path), exist_ok=True)
    final_df.to_csv(csv_output_path, index=False)
    print(f"Query result saved to {csv_output_path}")

# This function makes the user select a file to query with CLI
async def CLI_perform_query():
    published_hash_path = os.path.join('data', 'published_hash.json')

    if not os.path.exists(published_hash_path):
        print("\nNo published hashes file found.")
        return
    
    with open(published_hash_path, 'r') as f:
        published_hashes = json.load(f)
    if not published_hashes:
        print("\nNo hashes available in the published file.")
        return
    
    print("\nAvailable published hashes:")
    for idx, (file_name, hash_value) in enumerate(published_hashes.items()):
        print(f"[{idx + 1}] File: {file_name} - Hash: {hash_value}")
    file_index = int(input("Select a file to query by index: ")) - 1
    if file_index < 0 or file_index >= len(published_hashes):
        print("Invalid index selected.")
        return
    
    selected_file = list(published_hashes.keys())[file_index]
    file_path = os.path.join('data', 'uploaded', selected_file)

    await op_prepare_query(file_path, selected_file) # MAIN.py

async def op_prepare_query(file_path, selected_file): 
    query_dimensions = ["Category", "Production Cost", "City", "Product Name"]

    is_query_allowed = verify_query_allowed(query_dimensions, data_fact_model_address) # HASH_UTILS.py

    if not is_query_allowed:
        print("Query contains disallowed dimensions.")
        return
    print("Query is allowed. Proceeding with query execution...")

    try:
        await op_perform_query(file_path, selected_file) # MAIN.py
        print("Query executed successfully.")
    except Exception as e:
        print(f"Failed to perform query: {e}")
        return    

async def main():

    while True:
        print("\nSelect an option:")
        print("[1] Login as Organization 1")
        print("[2] Login as Organization 2")
        print("[3] Exit")
        choice = input("Enter your choice (1, 2, or 3): ")

        if choice == "1":  # -------------------------------------- ORG 1
            print("You selected: Login as ORG 1")
            print("\nSelect an option:")
            print("[1] Upload File")
            print("[2] Publish Hash")
            sub_choice = input("Enter your choice (1, 2, or 3): ")

            if sub_choice == "1":  # UPLOAD FILE
                op_generate_file()

            elif sub_choice == "2":  # PUBLISH HASH
                CLI_publish_hash()

            else:
                print("Invalid choice. Returning to main menu.")

        elif choice == "2":  # ------------------------------------- ORG 2
            print("You selected: Login as ORG 2")
            print("\nSelect an option:")
            print("[1] Perform Query")
            sub_choice = input("Enter your choice (1 or 2): ")

            if sub_choice == "1":  # PERFORM QUERY
                try:
                    await CLI_perform_query()
                except Exception as e:
                    print(f"Failed to perform query: {e}")

            else:
                print("Invalid choice. Returning to main menu.")

        elif choice == "3":  # -------------------------------------EXIT
            print("Exiting the program.")
            break

        else:
            print("Invalid choice. Please select a valid option.")

if __name__ == "__main__":
    asyncio.run(main())
