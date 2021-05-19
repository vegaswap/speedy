"""
tradetool
"""

import requests
import json
import pymongo
import os
import logging
import toml
import time

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

from token_addresses import *
from contract_utils import *

from unibot import UniswapBot
import ethplorer

from coingecko import CoinGeckoAPI
cg = CoinGeckoAPI()    

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

class Tradetool(Uniwrap):

    def __init__(self):
        logging.info("init bot")

        config = toml.load("config.toml")
        self.max_slippage = config["MAX_SLIPPAGE"]
        td = config["TOKEN_DECIMALS"]
        self.TOKEN_DECIMALS = td
        r = config["LIVE_RUN"]
        if r == 0:
            self.LIVE_RUN = False
        elif r== 1:
            self.LIVE_RUN = True
            logging.info("LIVE_RUN")
        

        self.target_token_symbol = config["TARGET_TOKEN"]
        logging.info(f"{self.target_token_symbol}")
        #token_dict = self.get_token_dict()
        #self.target_token = token_dict[self.target_token_symbol]

        logging.info(f"max_slippage {self.max_slippage}")

        self.setup_conn()
                
        self.init_setup_contracts()
        
        self.pair_contract = self.get_pair_contract_weth(self.target_token)
        self.pairsn = self.get_pairsn()
        #self.store_last_pairs()
        pool_info = self.get_pool_info(self.target_token)
        logging.info(f"{pool_info}")
        p = pool_info["price_float"]

        b = self.get_balance_info(self.target_token)
        eth_usd = b['eth_usd']
        price_usd = p*eth_usd
        token_balance_usd = round(b['token_balance_nom']*price_usd,0)        
        
        self.show_balance_info()
        
        reserves_eth = pool_info['reserves_eth']
        reserves_token = pool_info['reserves_token']
        
        logging.info(f"reserves_eth: {reserves_eth}")
        logging.info(f"reserves_token: {reserves_token}")
                
        #buy_qty_nominal = 1000
        #self.buy_and_info(buy_qty_nominal)
        
        #est_price_usd = est_price_float*self.eth_usd 
        #tb = self.token_balance/self.TOKEN_DECIMALS
        #tb_usd = tb*est_price_usd
        #logging.info(f"Token balance {str(self.token_balance)} {tb} {tb_usd}")
        # logging.info(f"price for {buy_qty_nominal}: {est_price} {est_price_float} {est_price_usd}")

        # eth_bal_use = self.eth_balance * (1 - 0.1)
        # max_buy_tokens = int(eth_bal_use/est_price)
        # logging.info(f"max_buy_tokens {max_buy_tokens}")
  
        BUY_QTY_NOM = 50
        logging.info("buy tokens")
        #self.buy_tokens(self.target_token, BUY_QTY_NOM)


        #SELL WIP
        # SELL_QTY_NOM = 160        

        # approved = self.check_approval(self.target_token)        
        
        # if approved < SELL_QTY_NOM:
        #     logging.info(f"need to approve {approved}")
        #     self.approve(self.target_token, SELL_QTY_NOM)
        #     approved = self.check_approval(self.target_token)

        # else:
        #     logging.info(f"approvd {approved}")
        #     self.sell_tokens(self.target_token, SELL_QTY_NOM)


if __name__=='__main__':
    logging.info("start tradetool")
    bot = Tradetool()
    