from dotenv import load_dotenv
from eth_account import Account
from web3.utils.coti import CotiNetwork, init_web3

from utils import (
    get_account_private_key,
    make_sure_tx_didnt_fail,
    sign_and_send_tx,
    validate_gas_estimation,
    validate_minimum_balance
)

def transfer_native(web3, eoa, recipient_address, amount_to_transfer_ether, native_gas_units):
    tx = {
        'from': eoa.address,
        'to': recipient_address,
        'value': web3.to_wei(amount_to_transfer_ether, 'ether'),  # Transaction value (0.1 Ether in this example)
        'nonce': web3.eth.get_transaction_count(eoa.address),
        'gas': native_gas_units,  # Gas limit for the transaction
        'gasPrice': web3.eth.gas_price,
        'chainId': web3.eth.chain_id
    }
    validate_gas_estimation(web3, tx)
    tx_receipt = sign_and_send_tx(web3, eoa.key, tx)
    return tx_receipt

# Script transfers native funds from wallet account to random one
def main():
    load_dotenv()  # loading .env
    eoa_private_key = get_account_private_key()  # Get EOA Private key for execution
    eoa = Account.from_key(eoa_private_key)
    web3 = init_web3(CotiNetwork.TESTNET)  # Init connection to node
    validate_minimum_balance(web3, eoa.address)  # validate minimum balance

    alice_address = Account.create()  # create some random address to transfer funds into
    amount_to_transfer_ether = 0.000000005
    num_of_gas_units = 21000

    tx_receipt = transfer_native(web3, eoa, alice_address.address, amount_to_transfer_ether, num_of_gas_units)
    print(tx_receipt)
    make_sure_tx_didnt_fail(tx_receipt)


if __name__ == "__main__":
    main()
