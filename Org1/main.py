import asyncio
import os
import json
import sys
import pandas as pd
import torch
import onnx
from onnx import helper, TensorProto

from Org1.data_generators import CSV_Generator1
from Org1.data_generators import CSV_Generator2
from Org1.hash_utils import publish_hash, calculate_poseidon_hash
from Org1.operations.slice_model import SliceModel
from Org1.operations.dicing_model import DicingModel
from Org1.operations.rollup_model import RollUpModel
from Org1.models.olap_cube import OLAPCube
from Org1.ezkl_workflow.generate_proof import generate_proof


output_dir = os.path.join('Org1', 'output')
os.makedirs(output_dir, exist_ok=True)

def load_contract_address(contract_name):
    # Load the contract address from the configuration file
    project_root = os.path.dirname(os.path.dirname(__file__))
    config_path = os.path.join(project_root, 'Blockchain', 'contract_addresses.json')
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
        output_file = "GHGe1.csv"
        CSV_Generator1.generate_CSV_1(2000, 1, output_file) # CSV_Generator1.py
        print("File generated with Generator 1.")
    elif generator_choice == "2":
        output_file="GHGe2.csv"
        CSV_Generator2.generate_CSV_2(2000, 1, output_file) # CSV_Generator2.py
        print("File generated with Generator 2.")
    else:
        print("Invalid choice. Returning to previous menu.")

    #file_path = os.path.join("Org1", 'data', 'uploaded', output_file)
    
    #update_metadata(file_path)

def CLI_publish_hash():
    # Make the user select a file to publish with CLI in data/uploaded directory
    uploaded_files_dir = os.path.join('Org1', 'data', 'uploaded')
    files = os.listdir(uploaded_files_dir)
    if not files:
        print("\nNo files available in the uploaded directory.")
        return
    print("\nAvailable files:")
    for idx, file in enumerate(files):
        print(f"[{idx + 1}] {file}")
    file_index = int(input("Select a file to publish by index: ")) - 1
    if file_index < 0 or file_index >= len(files):
        print("Invalid index selected.")
        return
    file_path = os.path.join(uploaded_files_dir, files[file_index])

    print("\n")
    hash = op_publish_hash(file_path) # MAIN.py

    # Save the hash in "published_hash.json" to share it with the customer
    published_hash_path = os.path.join('Shared', 'published_hash.json')
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

# This function decodes the operations from the JSON format into a list of OLAP operation models
def decode_operations(operations, columns_to_remove_idx):
    decoded_ops = []
    if "Dicing" in operations:
        for dicing_args in operations["Dicing"]:
            decoded_ops.append(DicingModel(dicing_args))
    if "Rollup" in operations:
        decoded_ops.append(RollUpModel(columns_to_remove_idx))
    return decoded_ops

# This function applies a sequence of OLAP operations to a data tensor using an OLAP cube object:
# - cube instance of OLAPCube from olap_cube.py -> tell how to apply OLAP operations to the data
# - tensor_data: the data tensor to be processed
# - operations: a list of OLAP operations to be applied
def apply_olap_operations(cube, tensor_data, operations):
    result_tensor = tensor_data
    for operation in operations:
        result_tensor = cube.execute_model(operation, result_tensor)
    print("OLAP operations applied successfully.")
    return result_tensor


async def op_perform_query(selected_file, operations, columns_to_remove_idx):
    decoded_operations = decode_operations(operations, columns_to_remove_idx)

    file_path = os.path.join('Org1', 'data', 'uploaded', selected_file)

    data_hash = calculate_poseidon_hash(file_path)

    # dataframe is a bidimensional data structure with rows and columns
    df = pd.read_csv(file_path)
    df.columns = df.columns.str.strip() # Remove leading and trailing whitespace from column names
    df = df.dropna() # Drop rows with NaN values

    print(f"Initial DataFrame: \n {df}")

    # Initialize the OLAP cube and transform the data into a tensor
    cube = OLAPCube(df)
    # save the mappings (categorical values - indexes) to a JSON file in Shared folder
    cube.save_category_mappings(os.path.join("Shared", "cat_map.json")) 
    tensor_data = cube.to_tensor()

    #print(f"DataFrame after dropping NaN values: \n {df}") # categorical columns are already encoded as integers
    #print(f"OLAP cube: {cube}")

    # Apply the operations to the tensor data 
    final_tensor = apply_olap_operations(cube, tensor_data, decoded_operations)

    print("test 0")

    #print(f"Inital tensor:\n{tensor_data}")
    #print(f"Final tensor:\n{final_tensor}")

    # Export the model in ONNX format
    # Selects the last operation, which represents the final transformation of the tensor data
    final_operation = decoded_operations[-1]  
    # ONNX export requires the model and the input tensor to be on the same device (usually CPU for interoperability), we move the model to CPU
    # "device" specifies where (on which hardware) the model will be run, in this case on CPU
    final_operation.to(torch.device("cpu"))
    # Sets the model to evaluation mode (alternative to train mode) to disable dropout and batch normalization layers
    final_operation.eval()

    print("test 10")

    model_onnx_path = os.path.join(output_dir, 'model.onnx')
    # to export the model torch.nn.Module to ONNX format
    torch.onnx.export(final_operation,               # model to be exported, nn.Module subclass
                      tensor_data,                   # example input used to trace the computation graph of the model
                      model_onnx_path,               # where to save the model
                      export_params=True,            # store the trained parameter weights inside the model file
                      opset_version=11,              # the ONNX version to export the model to
                      do_constant_folding=True,      # enables optimization by evaluating constant expressions at export time
                      input_names=['input'],         # the model's input names
                      output_names=['output'])       # the model's output names

    print("test 20")

    # load the ONNX model from the file to the python object onnx_model
    onnx_model = onnx.load(model_onnx_path)
    graph = onnx_model.graph

    print("test 30")
    
    # Run a validation check to ensure the model is well-formed and valid according to the ONNX specification
    onnx.checker.check_model(onnx_model)
    # print(onnx.helper.printable_graph(onnx_model.graph))

    print("test 40")
    
    # Create a Flatten node to flatten the input tensor to 1D
    flatten_node = helper.make_node(
        'Flatten',
        inputs=['input'],
        outputs=['input_flat'],
        name='FlattenInput'
    )
    graph.node.append(flatten_node)    

    print("test 50")


    # Add the Poseidon node
    poseidon_node = helper.make_node(
        'Poseidon',
        inputs=['input_flat'],
        outputs=['poseidon_hash'],
        name='PoseidonHash'
    )
    graph.node.append(poseidon_node)

    print("test 60")

    # Add the hash as a model output
    poseidon_output = helper.make_tensor_value_info(
        'poseidon_hash',
        TensorProto.INT64,  # or .FLOAT ? (to do)
        [1]
    )
    graph.output.append(poseidon_output)

    print("test 70")

    # Save the modified model
    onnx.save(onnx_model, model_onnx_path)

    print("test 75")

    #onnx.checker.check_model(onnx_model)

    print("test 80")

    # Prepare the input (input shape, input data, output data) for the proof generation in a dictionary format
    data = dict(
        input_shapes=[tensor_data.shape], # shape = how many elements along each axis
        # Take PyTorch tensor - detach it from any computation graph - convert it to a NumPy array - flatten it to 1D - list
        input_data=[(tensor_data).detach().numpy().tolist()],
        output_data=[final_tensor.detach().numpy().reshape([-1]).tolist()]
    )
    input_json_path = os.path.join(output_dir, 'input.json')
    with open(input_json_path, 'w') as f:
        json.dump(data, f) # serialize the data dictionary to a JSON file

    #await generate_proof(output_dir, model_onnx_path, input_json_path, logrows=17)
    await generate_proof(output_dir, model_onnx_path, input_json_path, logrows=18)

    return final_tensor, columns_to_remove_idx


async def main():

    while True:
        print("\n\nORG 1 (data provider) select an option:")
        print("[1] Upload (Generate) File")
        print("[2] Publish Hash")
        print("[3] Update file")
        print("[0] Exit")
        sub_choice = input("Enter your choice (1, 2, 3, or 0): ")

        if sub_choice == "1":  # UPLOAD FILE
            op_generate_file()

        elif sub_choice == "2":  # PUBLISH HASH
            CLI_publish_hash()

        elif sub_choice == "3":  # UPDATE FILE
            print("Update file functionality is not implemented yet.")
            #CLI_update_file()

        elif sub_choice == "0":
            print("Exiting.")
            break

        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    asyncio.run(main())