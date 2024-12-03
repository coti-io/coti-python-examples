import os

from dotenv import load_dotenv

from coti.crypto_utils import (
    build_input_text,
    build_string_input_text,
    decrypt_rsa,
    decrypt_string,
    decrypt_uint,
    generate_rsa_keypair,
    recover_user_key,
    sign
)
from eth_account import Account
from eth_account.signers.local import LocalAccount
from web3 import HTTPProvider, Web3

RPC_URL = 'https://testnet.coti.io/rpc'
ONBOARD_CONTRACT_ADDRESS = '0x60eA13A5f263f77f7a2832cfEeF1729B1688477c'
ONBOARD_CONTRACT_ABI = [
    {
        "anonymous": False,
        "inputs": [
            {
                "indexed": True,
                "internalType": "address",
                "name": "_from",
                "type": "address"
            },
            {
                "indexed": False,
                "internalType": "bytes",
                "name": "userKey1",
                "type": "bytes"
            },
            {
                "indexed": False,
                "internalType": "bytes",
                "name": "userKey2",
                "type": "bytes"
            }
        ],
        "name": "AccountOnboarded",
        "type": "event"
    },
    {
        "inputs": [
            {
                "internalType": "bytes",
                "name": "publicKey",
                "type": "bytes"
            },
            {
                "internalType": "bytes",
                "name": "signedEK",
                "type": "bytes"
            }
        ],
        "name": "onboardAccount",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    }
]
CONTRACT_ADDRESS = '0xc0ffee254729296a45a3885639AC7E10F9d54979'
FUNCTION_SELECTOR = '0x11223344'

PRIVATE_KEY = "0xdcf84e9a64a972abb45a63ba9588e5841e26c81b0c9886fc3c98aeb82fcb4fd8"

def onboard(w3: Web3, account: LocalAccount):
    account_onboard_contract = w3.eth.contract(address=ONBOARD_CONTRACT_ADDRESS, abi=ONBOARD_CONTRACT_ABI)

    [rsa_private_key, rsa_public_key] = generate_rsa_keypair()

    signature = sign(rsa_public_key, account.key)

    tx = account_onboard_contract.functions.onboardAccount(rsa_public_key, signature).build_transaction({
        'from': account.address,
        'chainId': w3.eth.chain_id,
        'nonce': w3.eth.get_transaction_count(account.address),
        'gas': 15000000,
        'gasPrice': w3.to_wei(30, 'gwei')
    })

    signed_tx = w3.eth.account.sign_transaction(tx, account.key)

    tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)

    tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

    user_key_events = account_onboard_contract.events.AccountOnboarded().process_receipt(tx_receipt)

    key_0_share = user_key_events[0].args.userKey1
    key_1_share = user_key_events[0].args.userKey2

    return recover_user_key(rsa_private_key, key_0_share, key_1_share).hex()

def encrypt_decrypt_uint(plaintext: int, account: LocalAccount, user_key: str):
    print(f'Encrypting uint: {plaintext}')

    input_text = build_input_text(plaintext, user_key, account.address, CONTRACT_ADDRESS, FUNCTION_SELECTOR, account.key)

    print(f'Encrypted value: {input_text["ciphertext"]} \n')
    print(f'Decrypting uint: {input_text["ciphertext"]}')

    clear_text = decrypt_uint(input_text["ciphertext"], user_key)

    print(f'Decrypted value: {clear_text} \n')

    if clear_text != plaintext:
        raise RuntimeError("Decrypted number does not match plaintext")

def encrypt_decrypt_string(plaintext: str, account: LocalAccount, user_key: str):
    print(f'Encrypting string: {plaintext}')

    input_text = build_string_input_text(plaintext, user_key, account.address, CONTRACT_ADDRESS, FUNCTION_SELECTOR, account.key)

    print(f'Encrypted value: {input_text["ciphertext"]["value"]} \n')
    print(f'Decrypting string: {input_text["ciphertext"]["value"]}')

    clear_text = decrypt_string(input_text["ciphertext"], user_key)

    print(f'Decrypted value: {clear_text} \n')

    if clear_text != plaintext:
        raise RuntimeError("Decrypted string does not match plaintext")

if __name__ == '__main__':
    load_dotenv()

    w3 = Web3(HTTPProvider(RPC_URL))
    account = Account.from_key(os.getenv('ACCOUNT_PRIVATE_KEY'))

    user_key = onboard(w3, account)

    encrypt_decrypt_uint(123, account, user_key)
    encrypt_decrypt_string("Hello, World!", account, user_key)