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

class SellTool(UniswapBot):

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
        self.pairsn = self.get_pairsn()
        
        # pool_info = self.get_pool_info(self.target_token)
        # logging.info(f"pool_info: {pool_info}")
        

        #self.show_balance_info()
        amount = self.approved_amount(self.target_token)
        logging.info(f"approved amount: {amount}")
        
        qty = -160 + 150*10**9
        RMPL = "0xE17f017475a709De58E976081eB916081ff4c9d5"
        print ("approve")
        self.approve(RMPL, qty)

        # amount = self.approved_amount(self.target_token)
        # logging.info(f"amount: {amount}")
        

    def pool_info(self, token_address):
        info = self.get_pool_info(token_address)
        return info

    def pool_infoR(self, token_address):
        info = self.get_pool_info_pairR(token_address)
        return info


if __name__=='__main__':    
    t = SellTool()    
    #mon.pool_infoR(token_addresses.SUSHI_ETH)
    

# case constants_1.TradeType.EXACT_INPUT:
    
# if (etherIn) {
#     'swapExactETHForTokens';
#     // (uint amountOutMin, address[] calldata path, address to, uint deadline)
#     args = [amountOut, path, to, deadline];
#     value = amountIn;
# }
# else if (etherOut) {
#     'swapExactTokensForETH';
#     // (uint amountIn, uint amountOutMin, address[] calldata path, address to, uint deadline)
#     args = [amountIn, amountOut, path, to, deadline];
#     value = ZERO_HEX;
# }

# var amountIn = toHex(trade.maximumAmountIn(options.allowedSlippage));
# var amountOut = toHex(trade.minimumAmountOut(options.allowedSlippage));


# self.router.functions.swapExactTokensForETH(
#     qty,
#     int((1 - self.max_slippage) * cost),
#     [input_token, self.get_weth_address()],
#     recipient,
#     self._deadline(),
# ),    