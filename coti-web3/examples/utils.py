import os

import dotenv
from eth_account import Account

def get_working_directory():
    repo_name = 'coti-web3'
    working_dir = os.getcwd()
    working_dir = working_dir[:working_dir.find(repo_name) + len(repo_name)]
    return working_dir

def create_eoa():
    account = Account.create()
    hex_val = account._private_key.hex()
    dotenv.set_key(get_working_directory() + '/.env', 'ACCOUNT_PRIVATE_KEY', hex_val)
    return hex_val

def get_account_private_key():
    account_private_key = os.getenv('ACCOUNT_PRIVATE_KEY')
    if account_private_key is None:
        print('So you dont have an account yet, dont worry... lets create one right now!')
        account_private_key = create_eoa()
        print('Creation done!')
    if account_private_key.startswith('0x'):
        account_private_key = account_private_key[2:]
    return account_private_key

def set_account_encryption_key(val):
    return dotenv.set_key(get_working_directory() + "/.env", "ACCOUNT_ENCRYPTION_KEY", val)

def get_account_encryption_key():
    set_hex_account_encryption = os.getenv('ACCOUNT_ENCRYPTION_KEY')
    if set_hex_account_encryption is None:
        raise Exception('Account is not onboarded - there is no user key in network, execute onboard_account.py')
    return set_hex_account_encryption

def validate_minimum_balance(web3, address):
    balance = web3.eth.get_balance(address)

    if balance > 0:
        return
    
    raise Exception(
        "Not enough balance!, head to discord faucet and get some..." \
        "https://faucet.coti.io, ask the BOT:" \
        "testnet " + address
    )

def is_gas_units_estimation_valid(web3, tx):
    estimate_gas = web3.eth.estimate_gas(tx)
    if tx['gas'] >= estimate_gas:
        return True, estimate_gas
    return False, estimate_gas

def validate_gas_estimation(web3, tx):
    valid, gas_estimate = is_gas_units_estimation_valid(web3, tx)
    if valid is False:
        raise Exception('not enough gas for tx (provided: ' + str(tx.get('gas')) + ' needed by estimation: ' + str(
            gas_estimate) + ')')

def exec_func_via_transaction(web3, eoa, func, tx_params):
    sender_address = eoa.address
    gas_limit = tx_params['gas_limit']
    gas_price_gwei = tx_params['gas_price_gwei']
    tx = func.build_transaction({
        'from': sender_address,
        'chainId': web3.eth.chain_id,
        'nonce': web3.eth.get_transaction_count(sender_address),
        'gas': gas_limit,
        'gasPrice': web3.to_wei(gas_price_gwei, 'gwei')
    })
    tx_receipt = sign_and_send_tx(web3, eoa.key, tx)
    return tx_receipt

def sign_and_send_tx(web3, private_key, transaction):
    try:
        signed_tx = web3.eth.account.sign_transaction(transaction, private_key)
    except Exception as e:
        raise Exception(f"Failed to sign the transaction: {e}")
    try:
        tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)
    except Exception as e:
        raise Exception(f"Failed to send the transaction: {e}")
    try:
        tx_receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
    except Exception as e:
        raise Exception(f"Failed to wait for the transaction receipt: {e}")
    return tx_receipt

def make_sure_tx_didnt_fail(tx_receipt):
    assert tx_receipt.status == 1

def get_contract(web3, abi, bytecode, contract_address):
    deployed_contract = web3.eth.contract(address=contract_address, abi=abi, bytecode=bytecode)
    return deployed_contract