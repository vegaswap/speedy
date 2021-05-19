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

factory_address_v2 = str_to_addr("0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f")
factory_contract = _load_contract(
    abi_name="UniswapV2Factory", address=factory_address_v2,
)
router_address: AddressLike = str_to_addr(
    "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D"
)
# https://uniswap.org/docs/v2/smart-contracts/router02/
router = _load_contract(
    abi_name="UniswapV2Router02", address=router_address,
)

RMPL = "0xE17f017475a709De58E976081eB916081ff4c9d5"
WETH = "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"

pair_addr = factory_contract.functions.getPair(WETH, RMPL).call()

pair_contract = _load_contract(abi_name="UniswapV2Pair", address=pair_addr)

reserve0,reserve1,blockts = pair_contract.functions.getReserves().call()

print (reserve0,reserve1)

#route = [WETH, token]
route = [RMPL, WETH]
qty_nom = 100
qty = qty_nom*(10**9)
price = router.functions.getAmountsIn(qty, route).call()[0]
price_inv = 1/price
ETHUSD = 368
price_usd = price_inv*ETHUSD
print ("price, price_usd ",price, price_usd)

deadline = int(time.time()) + 10 * 60

# amountIn	uint	The amount of input tokens to send.
# amountOutMin	uint	The minimum amount of output tokens that must be received for the transaction not to revert.

amountIn = qty
cost = price_inv*qty
#amountOutMin = int(cost * (1-0.02))

WETH_F = 10**18
amountOutMinX = 0.22
amountOutMin = int(amountOutMinX*WETH_F)

recipient = myaddr
print (f"amountIn: {amountIn} amountOutMin: {amountOutMin}")
swaptx = router.functions.swapExactTokensForETH(amountIn, amountOutMin, route, recipient, deadline)

print (swaptx)

msg_value = 0

txcount = w3.eth.getTransactionCount(myaddr)
last_nonce = w3.eth.getTransactionCount(myaddr)
tx_params = {
    "from": addr_to_str(myaddr),
    "value": msg_value,
    "gas": gas,
    "nonce": max(
        last_nonce, txcount
    ),
}

print (tx_params)
#txparams = _get_tx_params(msg_value, gas)

print ("buildTransaction")
start = time.time()
transaction = swaptx.buildTransaction(tx_params)
done = time.time()
elapsed = done - start
print("buildTransaction ",elapsed)

print ("sign_transaction")
signed_txn = w3.eth.account.sign_transaction(
    transaction, private_key=privateKey
)
print (signed_txn)

#TODO approval?

#approved = self.check_approval(self.target_token)        
print ("load erc20 contract")
erc20_contract = w3.eth.contract(address=RMPL, abi=load_abi("erc20"))        

approved_amount = erc20_contract.functions.allowance(myaddr, router_address).call()

print (f"approved_amount {approved_amount}")

bot = UniswapBot()
bot.approve(RMPL, qty)

#APPROVE AMOUNT * DECIMALS

# to_approve = qty
# function = erc20_contract.functions.approve(router_address, to_approve)
# logging.info(f"Approving token: {token}...")
# txparams = _get_tx_params(0, self.gas)
# tx = self._build_and_send_tx(function, txparams)
# self.w3.eth.waitForTransactionReceipt(tx, timeout=6000)
# txparams = self._get_tx_params(0, self.gas)
#         tx = self._build_and_send_tx(function, txparams)
#         self.w3.eth.waitForTransactionReceipt(tx, timeout=6000)

# start = time.time()
# receipt = w3.eth.sendRawTransaction(signed_txn.rawTransaction)
# done = time.time()
# elapsed = done - start
# print("elapsed ",elapsed)
# print ("receipt ",receipt)


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