import os
os.environ["RUST_LOG"] = "trace" # !RUST_LOG=trace
import json
from ezkl import ezkl
import asyncio

async def generate_proof(output_dir, model_onnx_path, input_json_path, logrows):
    # input_json_path for a file with: input shape, input data, output data

    # Generazione delle impostazioni usando ezkl
    settings_filename = os.path.join('Shared', 'proof', 'settings.json')
    os.makedirs(os.path.dirname(settings_filename), exist_ok=True)
    compiled_filename = os.path.join(output_dir, 'circuit.compiled')
    
    # ezkl.gen_settings() -> Generate a settings file analyzing the ONNX model, to create the zero-knowledge proof circuit
    # The file contains all the necessary configuration parameters (like input/output shapes, precision, and circuit options)
    res = ezkl.gen_settings(model_onnx_path, settings_filename)
    assert res == True # file successfully generated
    print(f"EZKL Generate settings: {res}")

    # SRS (Structured Reference System) is a set of cryptographic parameters used in zk-SNARKs to generate and verify proofs
    # cd ~/.ezkl/srs/
    # ezkl.get_srs() -> library to generate or download the SRS file needed for zero-knowledge proofs
    #   logrows: Security parameter that determines the size of the SRS (the number of rows is 2^logrows)
    try:
        print(f"Attempting to get SRS with logrows={logrows}")
        res = await ezkl.get_srs(settings_filename, logrows=logrows)
        assert res == True
        print(f"EZKL Get SRS: {res}")
    except Exception as e:
        print(f"Error during SRS generation: {e}")
        raise

    # ezkl.calibrate_settings() -> analyze the input data and model to adjust parameters (like scaling, precision, and ranges) in your settings.json 
    #   to ensure the circuit will work correctly and efficiently for your specific data
    # "resources" argument specifies the directory where ezkl will store calibration resources and temporary files generated during the calibration process
    res = await ezkl.calibrate_settings(input_json_path, model_onnx_path, settings_filename, "resources")
    assert res == True
    print(f"EZKL Calibrate settings: {res}")

    # This function compiles your ONNX model and the calibrated settings into a zero-knowledge proof circuit
    # This step is essential before running setup, witness, or proof generation
    res = ezkl.compile_circuit(model_onnx_path, compiled_filename, settings_filename)
    assert res == True
    print(f"EZKL Compile circuit: {res}")

    # Verifica dell'esistenza dei file necessari
    assert os.path.exists(settings_filename)
    assert os.path.exists(input_json_path)
    assert os.path.exists(model_onnx_path)

    # Setup della prova con ezkl
    pk_path = os.path.join(output_dir, 'test.pk') # Proving Key (to generate the proof)
    vk_path = os.path.join('Shared', 'proof', 'test.vk') # Verifying Key (to verify the proof)
    # ezkl.setup() -> This function generates the proving and verifying keys needed for the zero-knowledge proof
    res = ezkl.setup(compiled_filename, vk_path, pk_path)
    assert res == True
    print(f"EZKL Setup: {res}")

    witness_path = os.path.join(output_dir, "witness.json")
    try:
        # Witness generation needed to create the proof
        # Witness is a JSON file that contains the input data and intermediate values computed by the circuit
        res = await ezkl.gen_witness(input_json_path, compiled_filename, witness_path)
        if res:
            print("EZKL Witness Generation successful")
    except Exception as e:
        print(f"An error occurred: {e}")

    proof_path = os.path.join('Shared', 'proof', 'test.pf')
    try:
        # Proof generation
        # "single" indicates that we are generating a single proof for the circuit
        res = ezkl.prove(witness_path, compiled_filename, pk_path, proof_path, "single")
        # should also include "public.json" with the hash of the input data
        if res:
            print("EZKL Proof Generation successful")
    except Exception as e:
        print(f"An error occurred: {e}")

    
if __name__ == "__main__":
    import sys
    if len(sys.argv) != 5:
        print("Usage: python generate_proof.py <output_dir> <model_onnx_path> <input_json_path> <logrows>")
        sys.exit(1)

    output_dir = sys.argv[1]
    model_onnx_path = sys.argv[2]
    input_json_path = sys.argv[3]
    logrows = int(sys.argv[4])
    asyncio.run(generate_proof(output_dir, model_onnx_path, input_json_path, logrows))
