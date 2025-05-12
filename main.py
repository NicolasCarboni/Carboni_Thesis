import os
import json
import pandas as pd
import torch
import onnx
import time
import psutil
from models.olap_cube import OLAPCube
from operations.slicing_model import SlicingModel
from operations.dicing_model import DicingModel
from operations.roll_up_model import RollUpModel
import asyncio
from ezkl_workflow.generate_proof import generate_proof
from hash_utils import verify_dataset_hash, verify_query_allowed, publish_hash


output_dir = './output'
os.makedirs(output_dir, exist_ok=True)

def load_contract_address(contract_name):
    """Load the contract address from the configuration file."""
    config_path = os.path.join(os.path.dirname(__file__), 'config', 'contract_addresses.json')
    with open(config_path, 'r') as f:
        contract_addresses = json.load(f)
    return contract_addresses.get(contract_name)

def apply_olap_operations(cube, tensor_data, operations):
    result_tensor = tensor_data
    for operation in operations:
        result_tensor = cube.execute_model(operation, result_tensor)
    return result_tensor

def perform_query(file_path):
    df = pd.read_csv(file_path)
    df = df.dropna()
    # Initialize the OLAP cube and transform the data into a tensor
    cube = OLAPCube(df)
    tensor_data = cube.to_tensor()

    # Define the list of OLAP operations to apply
    operations = [
        SlicingModel({14: 1, 21: 12, 27: 0}),  # Slicing operation
        DicingModel({2: 2, 21: [3, 4], 27: 4})  # Dicing operation
    ]

    # Apply the operations to the tensor data
    final_tensor = apply_olap_operations(cube, tensor_data, operations)

    # Export the model in ONNX format
    final_operation = operations[-1]  # Last applied operation
    final_operation.to(torch.device("cpu"))
    final_operation.eval()

    model_onnx_path = os.path.join(output_dir, 'model.onnx')
    torch.onnx.export(final_operation, tensor_data, model_onnx_path, export_params=True, opset_version=11,
                      do_constant_folding=True, input_names=['input'], output_names=['output'])

    onnx_model = onnx.load(model_onnx_path)
    onnx.checker.check_model(onnx_model)
    print(onnx.helper.printable_graph(onnx_model.graph))

    d = ((tensor_data).detach().numpy()).reshape([-1])
    data = dict(
        input_shapes=[tensor_data.shape],
        input_data=[d.tolist()],
        output_data=[final_tensor.detach().numpy().reshape([-1]).tolist()]
    )
    input_json_path = os.path.join(output_dir, 'input.json')
    with open(input_json_path, 'w') as f:
        json.dump(data, f)


async def main():

    file_path = "completed_sales_dataset.csv"

        # Load the DataFactModel contract address dynamically
    data_fact_model_address = load_contract_address("DataFactModel")
    if not data_fact_model_address:
        print("DataFactModel address not found in configuration.")
        return  # Exit if the address is not found

    # _______________________________________________________________________________________

    while True:
        print("\nSelect an option:")
        print("1. Login as Data Owner")
        print("2. Login as Customer")
        print("3. Exit")
        choice = input("Enter your choice (1, 2, or 3): ")

        if choice == "1":  # --------------------------------------DATA OWNER
            print("You selected: Login as DATA OWNER")
            print("\nSelect an option:")
            print("1. Publish Hash")
            print("2. Verify Hash")
            sub_choice = input("Enter your choice (1 or 2): ")

            if sub_choice == "1":  # PUBLISH HASH
                try:
                    publish_hash(file_path)
                    print("Hash published successfully.")
                except Exception as e:
                    print(f"Failed to publish hash: {e}")

            elif sub_choice == "2":  # VERIFY HASH
                try:
                    verify_dataset_hash(file_path)
                    print("Hash verified successfully.")
                except ValueError as e:
                    print(f"Hash verification failed: {e}")
            else:
                print("Invalid choice. Returning to main menu.")

        elif choice == "2":  # -------------------------------------CUSTOMER
            print("You selected: Login as CUSTOMER")
            print("\nSelect an option:")
            print("1. Verify Hash")
            print("2. Perform Query")
            sub_choice = input("Enter your choice (1 or 2): ")

            if sub_choice == "1":  # VERIFY HASH
                try:
                    verify_dataset_hash(file_path)
                    print("Hash verified successfully.")
                except ValueError as e:
                    print(f"Hash verification failed: {e}")

            elif sub_choice == "2":  # PERFORM QUERY
                try:
                    # Perform query logic
                    query_dimensions = ["Category", "Production Cost", "City", "Product Name"]
                    is_query_allowed = verify_query_allowed(query_dimensions, data_fact_model_address)
                    if not is_query_allowed:
                        print("Query contains disallowed dimensions.")
                        continue
                    print("Query is allowed. Proceeding with query execution...")
                    perform_query(file_path)
                    # await generate_proof(output_dir, model_onnx_path, input_json_path, logrows=16)
                    print("Query executed successfully.")
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
