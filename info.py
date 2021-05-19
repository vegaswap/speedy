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

AddressLike = Union[Address, ChecksumAddress, ENS]

WETH_DECIMALS = 18
WETH_FACTOR = 10**WETH_DECIMALS

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("./logs/speedy.log"),
        logging.StreamHandler()
    ]
)

AddressLike = Union[Address, ChecksumAddress, ENS]

class Info(UniswapBot):

    def __init__(self):
        logging.info("init bot")

        config = toml.load("config.toml")
        self.max_slippage = config["MAX_SLIPPAGE"]
        td = config["TOKEN_DECIMALS"]
        self.TOKEN_DECIMALS = 10**td
        
        self.target_token = token_addresses.RMPL

        logging.info(f"max_slippage {self.max_slippage}")

        self.setup_conn()                
        self.init_setup_contracts()
        self.pairsn = self.get_pairsn()
        self.pairs = list()            
        self.eth_balance = self.get_eth_balance()
        balance_float = self.eth_balance/WETH_FACTOR
        logging.info(f"ETH balance: {balance_float}")

        self.token_balance = self.get_token_balance(self.target_token)
        logging.info(f"Token balance {str(self.token_balance)}")
        
        #self.init_pair_contract(target_token)

    def pool_info(self, token_address):
        #logging.info(f"info for {target_token}")
        info = self.get_pool_info(token_address)
        return info

    def pool_infoR(self, token_address):
        #logging.info(f"info for {target_token}")        
        info = self.get_pool_info_pairR(token_address)
        return info


if __name__=='__main__':    
    mon = Info()
    
    mon.pool_infoR(token_addresses.SUSHI_ETH)
    #pair = "0x0d4a11d5eeaac28ec3f61d100daf4d40471f1852"
    #p = Web3.toChecksumAddress(pair)
    #mon.show_all(p)
