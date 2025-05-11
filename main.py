import os
import pandas as pd
import torch
import onnx
import json
import time
import psutil
from models.olap_cube import OLAPCube
from operations.slicing_model import SlicingModel
from operations.dicing_model import DicingModel
from operations.roll_up_model import RollUpModel
import asyncio
import ezkl
from ezkl_workflow.generate_proof import generate_proof
from hash_utils import verify_dataset_hash, verify_query_allowed, publish_hash

def apply_olap_operations(cube, tensor_data, operations):
    result_tensor = tensor_data
    for operation in operations:
        result_tensor = cube.execute_model(operation, result_tensor)
    return result_tensor

async def main():
    output_dir = './output'
    os.makedirs(output_dir, exist_ok=True)

    file_path = "completed_sales_dataset.csv"
    
    publish_hash(file_path)  # Publish the hash of the dataset

    
    try:
        # Verifica l'hash del dataset prima di procedere
        verify_dataset_hash(file_path)
    except ValueError as e:
        print(e)
        print("Process terminated due to hash verification failure.")
        return  # Arresta l'esecuzione se la verifica fallisce


    """
    
    # Misurazione iniziale del tempo e della memoria
    start_time = time.time()
    process = psutil.Process(os.getpid())
    start_memory = process.memory_info().rss

    output_dir = './output'
    os.makedirs(output_dir, exist_ok=True)

    file_path = "completed_sales_dataset.csv"
    
    try:
        # Verifica l'hash del dataset prima di procedere
        verify_dataset_hash(file_path)
    except ValueError as e:
        print(e)
        print("Process terminated due to hash verification failure.")
        return  # Arresta l'esecuzione se la verifica fallisce
    
    # Misura il tempo e la memoria dopo la verifica dell'hash
    hash_verification_time = time.time()
    hash_verification_memory = process.memory_info().rss

    # Indirizzo del contratto DataFactModel
    data_fact_model_address = "0x870fc72A4BA55CeBD84a5D0517463FFbAb47a891"  # Aggiorna con l'indirizzo corretto

    # Dimensioni della query da verificare
    query_dimensions = ["Category", "Production Cost", "City", "Product Name"]

    try:
        # Verifica se la query è ammessa
        is_query_allowed = verify_query_allowed(query_dimensions, data_fact_model_address)
        if not is_query_allowed:
            print("Query contains disallowed dimensions")
            return  # Arresta l'esecuzione se la verifica fallisce
    except Exception as e:
        print(e)
        print("Failed to verify query dimensions")
        return  # Arresta l'esecuzione in caso di errore
    
    # Misura il tempo e la memoria dopo la verifica delle query
    query_verification_time = time.time()
    query_verification_memory = process.memory_info().rss

    df = pd.read_csv(file_path)
    df = df.dropna()
    # Inizializza il cubo OLAP e trasforma i dati in un tensor
    cube = OLAPCube(df)
    tensor_data = cube.to_tensor()

    # Definisci una lista di operazioni OLAP da applicare
    operations = [
        SlicingModel({14: 1, 21: 12, 27: 0}),  # Slicing operation
        DicingModel({2: 2, 21: [3, 4], 27: 4})  # Dicing operation
    ]

    # Applica le operazioni al tensor dei dati
    final_tensor = apply_olap_operations(cube, tensor_data, operations)

    # Misura il tempo e la memoria dopo le operazioni OLAP
    olap_operations_time = time.time()
    olap_operations_memory = process.memory_info().rss

    # Esportazione del modello in formato ONNX
    final_operation = operations[-1]  # Prendi l'ultima operazione applicata
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

    await generate_proof(output_dir, model_onnx_path, input_json_path, logrows=17)

    # Misura il tempo e la memoria dopo la generazione della prova
    end_time = time.time()
    end_memory = process.memory_info().rss

    # Calcola l'overhead
    total_time = end_time - start_time
    total_memory = end_memory - start_memory
    hash_verification_duration = hash_verification_time - start_time
    hash_verification_memory_usage = hash_verification_memory - start_memory
    query_verification_duration = query_verification_time - hash_verification_time
    query_verification_memory_usage = query_verification_memory - hash_verification_memory
    olap_operations_duration = olap_operations_time - query_verification_time
    olap_operations_memory_usage = olap_operations_memory - query_verification_memory

    # Stampa i risultati
    print(f"Total Time: {total_time:.2f} seconds")
    print(f"Total Memory Usage: {total_memory / 1024 / 1024:.2f} MB")
    print(f"Hash Verification Time: {hash_verification_duration:.2f} seconds")
    print(f"Hash Verification Memory Usage: {hash_verification_memory_usage / 1024 / 1024:.2f} MB")
    print(f"Query Verification Time: {query_verification_duration:.2f} seconds")
    print(f"Query Verification Memory Usage: {query_verification_memory_usage / 1024 / 1024:.2f} MB")
    print(f"OLAP Operations Time: {olap_operations_duration:.2f} seconds")
    print(f"OLAP Operations Memory Usage: {olap_operations_memory_usage / 1024 / 1024:.2f} MB")
    """

if __name__ == "__main__":
    asyncio.run(main())
