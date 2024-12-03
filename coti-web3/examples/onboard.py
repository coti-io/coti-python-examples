from dotenv import load_dotenv

from eth_account import Account
from web3.utils.coti import CotiNetwork, generate_or_recover_aes, init_web3

from utils import (
    get_account_private_key,
    set_account_encryption_key
)


# Script onboards a EOA into the network, meaning, creates a AES key unique to that user,
# and that key will be used to encrypt all data sent back to the wallet
# mandatory script for any operation done in a contract that requires
# encrypt/decrypt (which is basically all new precompiles operations introduced)
def main():
    eoa, web3 = init()

    generate_or_recover_aes(web3, eoa)
    env_value = set_account_encryption_key(eoa.aes_key)

    if env_value[0] is not True:
        raise Exception('encryption key not saved in .env!')
    
    print(env_value)


def init():
    load_dotenv()  # loading .env
    eoa_private_key = get_account_private_key()  # Get EOA Private key for execution
    eoa = Account.from_key(eoa_private_key)  # Get EOA
    web3 = init_web3(CotiNetwork.TESTNET)  # Init connection to node
    return eoa, web3


if __name__ == "__main__":
    main()
