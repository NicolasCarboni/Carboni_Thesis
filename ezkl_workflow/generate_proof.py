import os
os.environ["RUST_LOG"] = "trace" # !RUST_LOG=trace
import json
from ezkl import ezkl
import asyncio

async def generate_proof(output_dir, model_onnx_path, input_json_path, logrows):
    # Generazione delle impostazioni usando ezkl
    settings_filename = os.path.join(output_dir, 'settings.json')
    compiled_filename = os.path.join(output_dir, 'circuit.compiled')
    
    res = ezkl.gen_settings(model_onnx_path, settings_filename)
    assert res == True

    try:
        print(f"Attempting to get SRS with logrows={logrows}")
        srs_path = await ezkl.get_srs(settings_filename, logrows=logrows)
        print(f"SRS path: {srs_path}")
        assert srs_path == True
    except Exception as e:
        print(f"Error during SRS generation: {e}")
        raise

    res = await ezkl.calibrate_settings(input_json_path, model_onnx_path, settings_filename, "resources")
    assert res == True
    print(f"calibrate_settings: {res}")

    ezkl.compile_circuit(model_onnx_path, compiled_filename, settings_filename)

    # Verifica dell'esistenza dei file necessari
    assert os.path.exists(settings_filename)
    assert os.path.exists(input_json_path)
    assert os.path.exists(model_onnx_path)

    # Setup della prova con ezkl
    vk_path = os.path.join(output_dir, 'test.vk')
    pk_path = os.path.join(output_dir, 'test.pk')
    res = ezkl.setup(compiled_filename, vk_path, pk_path)
    assert res == True
    print(f"setup: {res}")

    witness_path = os.path.join(output_dir, "witness.json")
    try:
        # Generazione del testimone
        res = await ezkl.gen_witness(input_json_path, compiled_filename, witness_path)
        if res:
            print("Witness file was successfully generated")
    except Exception as e:
        print(f"An error occurred: {e}")

    proof_path = os.path.join(output_dir, 'test.pf')
    try:
        # Generazione della prova
        proof = ezkl.prove(witness_path, compiled_filename, pk_path, proof_path, "single")
        if proof:
            print("Proof file was successfully generated")
    except Exception as e:
        print(f"An error occurred: {e}")

    try:
        # Verifica della prova
        res = ezkl.verify(proof_path, settings_filename, vk_path)
        if res:
            print("The proof was successfully verified")
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
