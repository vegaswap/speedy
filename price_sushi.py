"""
SUSHI

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

SUSHI_FACTORY = "0xC0AEe478e3658e2610c5F7A4A2E1777cE9e4f2Ac"
SUSHI_ROUTER = "0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F"

_netid_to_name = {1: "mainnet", 4: "rinkeby"}

config = toml.load("config.toml")
max_slippage = 0.01
td = config["TOKEN_DECIMALS"]
TOKEN_DECIMALS = td
LIVE_RUN = False

target_token_symbol = config["TARGET_TOKEN"]

secrets = toml.load("secrets.toml")
privateKey = secrets["PRIVATEKEY"]
INFURA_KEY = secrets["INFURA_KEY"]                
INFURA_URL = "https://mainnet.infura.io/v3/" + INFURA_KEY
w3 = Web3(HTTPProvider(INFURA_URL))
block = w3.eth.getBlock('latest')
#ts = block['timestamp']
print ('last block ',block['number'])

gas = Wei(250000)
w3.eth.setGasPriceStrategy(fast_gas_price_strategy) 

acct = w3.eth.account.privateKeyToAccount(privateKey)
myaddr = Web3.toChecksumAddress(acct.address) #(self.acct.address).lower()
last_nonce: Nonce = w3.eth.getTransactionCount(myaddr)

netid = int(w3.net.version)
if netid in _netid_to_name:
    network = _netid_to_name[netid]

def _load_contract(abi_name, address) -> Contract:
    return w3.eth.contract(address=address, abi=load_abi_json(abi_name))


factory_address_v2 = str_to_addr(SUSHI_FACTORY)
factory_contract = _load_contract(
    abi_name="UniswapV2Factory", address=factory_address_v2,
)
router_address: AddressLike = str_to_addr(
    SUSHI_ROUTER
)
# https://uniswap.org/docs/v2/smart-contracts/router02/
router = _load_contract(
    abi_name="UniswapV2Router02", address=router_address,
)

SUSHI = "0x6B3595068778DD592e39A122f4f5a5cF09C90fE2"
WETH = "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"

pair_addr = factory_contract.functions.getPair(WETH, SUSHI).call()
pair_contract = _load_contract(abi_name="UniswapV2Pair", address=pair_addr)
route = [SUSHI, WETH]
print ('**** GET PRICE ', route)
qty_nom = 100
qty = qty_nom*(10**9)
price = router.functions.getAmountsIn(qty, route).call()[0]
price_inv = 1/price
ETHUSD = 368
price_usd = price_inv*ETHUSD
print ("price, price_usd ",price, price_usd)


#reserve0,reserve1,blockts = pair_contract.functions.getReserves().call()
#print (reserve0,reserve1)
