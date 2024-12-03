import importlib.resources
import json

from dotenv import load_dotenv
from eth_account import Account
from web3 import Web3
from web3.utils.coti import CotiNetwork, init_web3

from utils import (
    exec_func_via_transaction,
    get_account_encryption_key,
    get_account_private_key,
    make_sure_tx_didnt_fail,
    validate_minimum_balance
)


# script deploys the confidential erc20 contract
# that is possible to transfer funds in an encrypted manner
# pending enhancements: approval, allowance, mint in encrypted manner and gas estimations
def main():
    eoa, web3 = init()

    gas_limit = 10000000
    gas_price_gwei = 30
    token_name = "My Confidential Token"
    token_symbol = "CTOK"

    tx_params = {'gas_limit': gas_limit, 'gas_price_gwei': gas_price_gwei}
    deployed_contract = deploy(web3, eoa, token_name, token_symbol)
    view_functions(deployed_contract, eoa)
    testing_functions(web3, eoa, deployed_contract, tx_params)


def init():
    load_dotenv()  # loading .env
    eoa_private_key = get_account_private_key()  # Get EOA Private key for execution
    account_encryption_key = get_account_encryption_key()  # Get Hex key used to encrypt on network
    eoa = Account.from_key(eoa_private_key, { 'aes_key': account_encryption_key })
    web3 = init_web3(CotiNetwork.TESTNET)  # Init connection to node
    validate_minimum_balance(web3, eoa.address)  # validate minimum balance
    return eoa, web3


def deploy(web3: Web3, eoa: Account, name, symbol):
    kwargs = {
        'name_': name,
        'symbol_': symbol
    }
    resource = importlib.resources.files('artifacts') / 'contracts' / 'PrivateToken.sol' / 'PrivateToken.json'

    with open(resource, 'r') as file:
        data = json.load(file)
    
    PrivateToken = web3.eth.contract(abi=data['abi'], bytecode=data['bytecode'])

    tx = PrivateToken.constructor(**kwargs).build_transaction({
        'from': eoa.address,
        'nonce': web3.eth.get_transaction_count(eoa.address)
    })

    signed_tx = web3.eth.account.sign_transaction(tx, eoa._private_key)

    tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)

    tx_receipt = web3.eth.wait_for_transaction_receipt(tx_hash)

    deployed_contract = web3.eth.contract(address=tx_receipt.contractAddress, abi=data['abi'])

    print('contract address: ', deployed_contract.address)

    return deployed_contract


def testing_functions(web3: Web3, eoa: Account, deployed_contract, tx_params):
    # Generate a new Ethereum account for Alice
    alice_address = Account.create()
    plaintext_integer = 5

    test_mint(web3, eoa, deployed_contract, tx_params)
    account_balance_at_first = get_account_balance(eoa, deployed_contract)
    account_balance_at_end = test_transfer_input_text(web3, eoa, account_balance_at_first, alice_address,
                                                      deployed_contract, plaintext_integer, tx_params)

    print('account balance at first: ', account_balance_at_first, ' account balance at end:', account_balance_at_end)


def test_mint(web3: Web3, eoa: Account, deployed_contract, tx_params):
    print("************* Minting 500000000 to my address *************")
    kwargs = {'account': eoa.address, 'amount': 500000000}
    tx_receipt = mint(web3, eoa, deployed_contract, kwargs, tx_params)
    print(tx_receipt)
    make_sure_tx_didnt_fail(tx_receipt)


def test_transfer_input_text(web3, eoa, account_balance_before, alice_address, deployed_contract, plaintext_integer, tx_params):
    print("************* Transfer IT ", plaintext_integer, " to Alice *************")
    kwargs = {'to': alice_address.address, 'value': (5, bytes(65))}
    tx_receipt = transfer_encrypted(web3, eoa, deployed_contract, kwargs, tx_params)
    print(tx_receipt)
    make_sure_tx_didnt_fail(tx_receipt)
    account_balance_after = get_account_balance(eoa, deployed_contract)
    assert account_balance_before - plaintext_integer == account_balance_after
    return account_balance_after


def view_functions(deployed_contract, eoa):
    print("************* View functions *************")
    name = deployed_contract.functions.name().call({'from': eoa.address})
    print("Function call result name:", name)
    symbol = deployed_contract.functions.symbol().call({'from': eoa.address})
    print("Function call result symbol:", symbol)
    decimals = deployed_contract.functions.decimals().call({'from': eoa.address})
    print("Function call result decimals:", decimals)


def get_account_balance(eoa, deployed_contract):
    cipher_text_balance = deployed_contract.functions.balanceOf(eoa.address).call({'from': eoa.address})
    account_balance = eoa.decrypt_value(cipher_text_balance)
    return account_balance


def transfer_encrypted(web3, eoa, deployed_contract, kwargs, tx_params):
    plaintext_integer = kwargs['value'][0]
    func_selector = deployed_contract.functions.transfer(**kwargs).selector
    input_text = eoa.encrypt_value(plaintext_integer, deployed_contract.address, func_selector)
    kwargs['value'] = input_text
    func = deployed_contract.functions.transfer(**kwargs)
    return exec_func_via_transaction(web3, eoa, func, tx_params)


def mint(web3, eoa, deployed_contract, kwargs, tx_params):
    func = deployed_contract.functions.mint(**kwargs)
    return exec_func_via_transaction(web3, eoa, func, tx_params)

if __name__ == "__main__":
    main()