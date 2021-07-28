import os
import toml
import web3
from web3 import Web3, HTTPProvider, WebsocketProvider
import json
import requests
import logging

from web3 import Web3, HTTPProvider, WebsocketProvider
from web3.eth import Contract
from web3.contract import ContractFunction
from web3.types import (
    TxParams,
    Wei,
    Address,
    ChecksumAddress,
    ENS,
    Nonce,
    HexBytes,
)
from typing import List, Any, Optional, Callable, Union, Tuple, Dict


AddressLike = Union[Address, ChecksumAddress, ENS]

from ethwrap.contract_utils import addr_to_str, str_to_addr

from ethwrap.coingecko import CoinGeckoAPI
cg = CoinGeckoAPI()    


BASE_URL = "https://api.ethplorer.io/"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("./logs/manager.log"),
        logging.StreamHandler()
    ]
)

_netid_to_name = {1: "mainnet", 4: "rinkeby", 56: "bsc"}

class Manager:
    """ manager of web3 and transactions """

    def __init__(self):
        #print ("init manager")
        self.setup_conn()

    def setup_conn(self):
        #self.ETHPLORER_KEY = get_ethplorer_key()
        secrets = get_secrets()
        self.privateKey = secrets["PRIVATEKEY"]
        #INFURA_KEY = secrets["INFURA_KEY"]                
        #INFURA_URL = "https://mainnet.infura.io/v3/" + INFURA_KEY
        PROVIDER_URL = "https://bsc-dataseed.binance.org/"
        self.w3 = Web3(HTTPProvider(PROVIDER_URL))

        self.acct = self.w3.eth.account.privateKeyToAccount(self.privateKey)
        self.myaddr = Web3.toChecksumAddress(self.acct.address) #(self.acct.address).lower()
        self.last_nonce: Nonce = self.w3.eth.getTransactionCount(self.myaddr)
        logging.debug(f"lastnonce {self.last_nonce}")
        logging.info(f"using address {self.myaddr}")

        self.base_dir = get_base_dir()

        self.last_nonce: Nonce = self.w3.eth.getTransactionCount(self.myaddr)

        netid = int(self.w3.net.version)
        if netid in _netid_to_name:
            self.network = _netid_to_name[netid]
        else:
            raise Exception(f"Unknown netid: {netid}")

    def get_eth_balance(self) -> Wei:
        """Get the balance of ETH in a wallet."""
        ca = Web3.toChecksumAddress(self.myaddr)
        return self.w3.eth.getBalance(ca)

    def get_eth_usd(self):
        return float(cg.get_coins_markets("USD",page=0)[1]['current_price'])

    def load_abi(self, bdir, name: str) -> str:
        path = bdir + "/abi/"
        with open(os.path.abspath(path + f"{name}.abi")) as f:
            abi: str = json.load(f)
        return abi

    def load_abi_json(self, bdir, name: str) -> str:
        #path = f"{os.path.dirname(os.path.abspath(__file__))}/abi/"
        #path = f"{os.path.dirname(bdir)}/abi/"
        path = bdir + "/abi/"
        with open(os.path.abspath(path + f"{name}.json")) as f:
            abi: str = json.load(f)["abi"]
        return abi

    def load_contract(self, abi_name: str, address: AddressLike) -> Contract:
        return self.w3.eth.contract(address=address, abi=self.load_abi_json(self.base_dir, abi_name))

    def erc20_contract(self, token_addr: AddressLike) -> Contract:
        return self.w3.eth.contract(address=token_addr, abi=self.load_abi(self.base_dir, "erc20"))

    def get_token_balance(self, token: AddressLike, address) -> int:
        """Get the balance of a token in a wallet."""
        #_validate_address(token)
        #if addr_to_str(token) == ETH_ADDRESS:
        #    return self.get_eth_balance()
        erc20 = self.erc20_contract(token)
        balance: int = erc20.functions.balanceOf(address).call()
        return balance

    def get_my_token_balance(self, token: AddressLike) -> int:
        """Get the balance of a token in a wallet."""
        #_validate_address(token)
        #if addr_to_str(token) == ETH_ADDRESS:
        #    return self.get_eth_balance()
        return self.get_token_balance(token, self.myaddr)


    def get_tx_params(self, value: Wei, gas: Wei) -> TxParams:
        """Get generic transaction parameters."""
        #extra_unconfirmed = 6
        #TODO
        #gas = self.get_gas()
        
        txcount = self.w3.eth.getTransactionCount(self.myaddr)
        #TMP bug fix if unconfirmed pending
        #https://ethereum.stackexchange.com/questions/27256/error-replacement-transaction-underpriced
        #txcount += extra_unconfirmed
        return {
            "from": addr_to_str(self.myaddr),
            "value": value,
            "gas": gas,
            "nonce": max(
                self.last_nonce, txcount
            )
        }

    def build_tx(self, function, tx_params):
        tx = function.buildTransaction(tx_params)
        # gasPrice = self.w3.eth.generateGasPrice()
        # logging.info(f"gasPrice {gasPrice}")
        # fee=self.gas*gasPrice
        gp = tx['gasPrice']
        # total_fee = tx_params['gas']*gp
        # total_fee_float = total_fee/WETH_FACTOR
        # total_fee_usd = total_fee_float*self.eth_usd
        # logging.info(f"transaction {tx}")
        # logging.info(f"total_fee {total_fee} {total_fee_float} {total_fee_usd}")
        signed_txn = self.w3.eth.account.sign_transaction(
            tx, private_key=self.privateKey
        )
        return signed_txn

    def get_token_info(self, tokenaddress):
        url = BASE_URL + "getTokenInfo/%s?apiKey=%s"%(tokenaddress, self.ETHPLORER_KEY)
        r = json.loads(requests.get(url).content)
        return r


def get_base_dir():
    bdir = os.environ["HOME"] + "/" + ".ethwrap"
    return bdir

def get_secrets():
    bdir = get_base_dir()
    secrets_path = bdir + "/" + "secrets.toml"
    secrets = toml.load(secrets_path)
    return secrets

def get_infura_url():
    secrets = get_secrets()
    INFURA_KEY = secrets["INFURA_KEY"]                
    INFURA_URL = "https://mainnet.infura.io/v3/" + INFURA_KEY
    return INFURA_URL

def get_ethplorer_key():
    secrets = get_secrets()
    ETHPLORER_KEY = secrets["ETHPLORER_KEY"]
    return ETHPLORER_KEY

def get_w3():
    INFURA_URL = get_infura_url()
    w3 = Web3(HTTPProvider(INFURA_URL))
    return w3

def get_account(w3):
    secrets = get_secrets()
    privateKey = secrets["PRIVATEKEY"]
    return w3.eth.account.privateKeyToAccount(privateKey)
