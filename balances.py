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
        
        self.setup_conn()
                
        self.init_setup_contracts()
        self.pairsn = self.get_pairsn()
        
        pool_info = self.get_pool_info(self.target_token)
        logging.info(f"pool_info: {pool_info}")
        p = pool_info["price_float"]

        b = self.get_balance_info(self.target_token)
        #price_usd = p*b['eth_usd']
        #token_balance_usd = round(b['token_balance_nom']*price_usd,0)        
        #[eth_balance, eth_balance_float, eth_usd, eth_balance_usd, decimals, token_balance, token_balance_nom, token_balance_usd] 
        logging.info(f"eth_balance_float {round(b['eth_balance_float'],2)}")
        logging.info(f"Token balance {str(b['token_balance'])}")
        logging.info(f"Token balance {str(b['token_balance_nom'])}")
        #logging.info(f"token_balance $: {token_balance_usd}")
        logging.info(f"eth_balance $:  {b['eth_balance_usd']}")

        #p = get_price_buy
        logging.info(f"price {round(p,6)}   {round(price_usd,3)} $")
        
        logging.info(f"max_slippage {self.max_slippage}")
        # self.eth_balance = self.get_eth_balance()
        # balance_float = self.eth_balance/WETH_FACTOR
        # logging.info(f"ETH balance: {balance_float}")        

        # self.token_balance = self.get_token_balance(self.target_token)
        # logging.info(f"Token balance {str(self.token_balance)}")

        # token_info = ethplorer.get_info(self.target_token)
        # dec = int(token_info['decimals'])
        # print (dec)
        # logging.info(f"Token balance {str(self.token_balance/(10**dec))}")
        
        #self.init_pair_contract(target_token)

    def pool_info(self, token_address):
        info = self.get_pool_info(token_address)
        return info

    def pool_infoR(self, token_address):
        info = self.get_pool_info_pairR(token_address)
        return info


if __name__=='__main__':    
    mon = Balances()    
    #mon.pool_infoR(token_addresses.SUSHI_ETH)
    