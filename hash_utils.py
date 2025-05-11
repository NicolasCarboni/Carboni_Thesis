import os
import json
import hashlib
import logging
from web3 import Web3

logging.basicConfig(level=logging.INFO)

# Load contract addresses from configuration file
CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'config', 'contract_addresses.json')
with open(CONFIG_PATH, 'r') as f:
    contract_addresses = json.load(f)

CONTRACT_ADDRESS = contract_addresses.get("HashStorage")
DATA_FACT_MODEL_ADDRESS = contract_addresses.get("DataFactModel")

CONTRACT_ABI_SET_HASH = json.loads('''
[
    {
        "constant": false,
        "inputs": [
            {
                "name": "newHash",
                "type": "bytes32"
            }
        ],
        "name": "setHash",
        "outputs": [],
        "payable": false,
        "stateMutability": "nonpayable",
        "type": "function"
    }
]
''')
CONTRACT_ABI_GET_HASH = json.loads('''
[
    {
        "constant": true,
        "inputs": [],
        "name": "getHash",
        "outputs": [
            {
                "name": "",
                "type": "bytes32"
            }
        ],
        "payable": false,
        "stateMutability": "view",
        "type": "function"
    }
]
''')
CONTRACT_ABI_QUERY_ALLOWED = json.loads('''
[
    {
        "constant": true,
        "inputs": [
            {
                "name": "queryDimensions",
                "type": "string[]"
            }
        ],
        "name": "isQueryAllowed",
        "outputs": [
            {
                "name": "",
                "type": "bool"
            }
        ],
        "payable": false,
        "stateMutability": "view",
        "type": "function"
    }
]
''')

def setup_web3():
    web3 = Web3(Web3.HTTPProvider("http://127.0.0.1:8545"))
    if not web3.is_connected():
        logging.error("Failed to connect to the blockchain.")
        raise ConnectionError("Failed to connect to the blockchain.")
    return web3

def get_contract(web3, address, abi):
    return web3.eth.contract(address=address, abi=abi)

def calculate_file_hash(file_path):
    """Calculate the SHA-256 hash of a file."""
    hasher = hashlib.sha256()
    try:
        with open(file_path, 'rb') as f:
            buf = f.read()
            hasher.update(buf)
    except FileNotFoundError:
        logging.error(f"File not found: {file_path}")
        raise
    return hasher.hexdigest()

def get_stored_hash(web3, contract):
    return contract.functions.getHash().call()

def publish_hash(file_path):
    calculated_hash = calculate_file_hash(file_path)
    bytes32_hash = Web3.to_bytes(hexstr=calculated_hash)

    web3 = setup_web3()
    contract = get_contract(web3, CONTRACT_ADDRESS, CONTRACT_ABI_SET_HASH)

    account = web3.eth.accounts[0]

    try:
        tx_hash = contract.functions.setHash(bytes32_hash).transact({'from': account})
        web3.eth.wait_for_transaction_receipt(tx_hash)
        logging.info(f"Hash {calculated_hash} has been published to the blockchain.")
    except Exception as e:
        logging.error(f"Failed to publish hash: {e}")
        raise

def verify_dataset_hash(file_path):
    calculated_hash = calculate_file_hash(file_path)
    bytes32_hash = Web3.to_bytes(hexstr=calculated_hash)

    web3 = setup_web3()
    contract = get_contract(web3, CONTRACT_ADDRESS, CONTRACT_ABI_GET_HASH)

    stored_hash = get_stored_hash(web3, contract)

    logging.info(f"Calculated hash: {bytes32_hash}")
    logging.info(f"Stored hash: {stored_hash}")

    if bytes32_hash == stored_hash:
        logging.info("Hash verification successful. The dataset is authentic.")
    else:
        logging.error("Hash verification failed. The dataset has been tampered with.")
        raise ValueError("Hash verification failed. The dataset has been tampered with.")

def verify_query_allowed(query_dimensions, contract_address):
    web3 = setup_web3()
    contract = get_contract(web3, contract_address, CONTRACT_ABI_QUERY_ALLOWED)

    try:
        is_allowed = contract.functions.isQueryAllowed(query_dimensions).call()
        logging.info(f"Query allowed: {is_allowed}")
        return is_allowed
    except Exception as e:
        logging.error(f"Failed to verify query: {e}")
        raise
