"""
monitor tool
"""

import requests
import json
import pymongo
import os
import logging
import toml
import time
import pymongo

from typing import List, Any, Optional, Callable, Union, Tuple, Dict
from web3 import Web3, HTTPProvider
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
from web3.gas_strategies.time_based import medium_gas_price_strategy, fast_gas_price_strategy

import token_addresses
from contract_utils import *

from unibot import UniswapBot
from consts import *
import ethplorer

AddressLike = Union[Address, ChecksumAddress, ENS]

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("./logs/speedy.log"),
        logging.StreamHandler()
    ]
)

AddressLike = Union[Address, ChecksumAddress, ENS]

class Balances(UniswapBot):

    def __init__(self):
        logging.info("init bot")
        config = toml.load("config.toml")
        self.max_slippage = config["MAX_SLIPPAGE"]
        td = config["TOKEN_DECIMALS"]
        self.target_token_symbol = config["TARGET_TOKEN"]
        token_dict = self.get_token_dict()
        self.target_token = token_dict[self.target_token_symbol]
        print (self.target_token)
        self.TOKEN_DECIMALS = 10**td        
        logging.info(f"max_slippage {self.max_slippage}")
        self.setup_conn()
        self.init_setup_contracts()

    def show(self):        
        pool_info = self.get_pool_info(self.target_token)
        logging.info(f"{pool_info}")
        p = pool_info["price_float"]

        b = self.get_balance_info(self.target_token)
        price_usd = p*b['eth_usd']
        token_balance_usd = round(b['token_balance_nom']*price_usd,0)        
        #[eth_balance, eth_balance_float, eth_usd, eth_balance_usd, decimals, token_balance, token_balance_nom, token_balance_usd] 
        logging.info(f"eth_balance_float {round(b['eth_balance_float'],2)}")
        logging.info(f"Token balance {str(b['token_balance'])}")
        logging.info(f"Token balance {str(b['token_balance_nom'])}")
        logging.info(f"token_balance $: {token_balance_usd}")
        logging.info(f"eth_balance $:  {b['eth_balance_usd']}")

        #p = get_price_buy
        logging.info(f"price {p} {price_usd}")
        
    def pool_info(self, token_address):
        info = self.get_pool_info(token_address)
        return info

    def pool_infoR(self, token_address):
        info = self.get_pool_info_pairR(token_address)
        return info

    def loop(self):
        while True:
            self.show()
            time.sleep(10.0)


if __name__=='__main__':    
    mon = Balances()    
    mon.loop()
    #mon.pool_infoR(token_addresses.SUSHI_ETH)
    