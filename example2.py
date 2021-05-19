"""
example sell for testing

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
from contract_utils import *
from unibot import UniswapBot 

#TODO lower gas?

bot = UniswapBot()
bot.setup_conn()                
bot.init_setup_contracts()
qty = 150*10**9
RMPL = "0xE17f017475a709De58E976081eB916081ff4c9d5"
print ("approve")
bot.approve(RMPL, qty)

