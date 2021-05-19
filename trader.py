"""
basic trader
"""
#import sys
#sys.path.append('/Users/ben/projects/ethwrap')

import requests
import json
import pymongo
import os
import logging
import toml
import time
import pymongo

from uniwrap import Uniwrap
from consts import *    
import ethplorer
import ethwrap.token_addresses as token_addresses

from web3.types import Wei


class Balances(Uniwrap):

    def __init__(self):
        super().__init__()
        logging.info("init bot")


b = Balances()
print (b.myaddr)
print ("eth balance ",b.get_eth_balance())

gas = Wei(25000)
tx_params = b.get_tx_params(0, gas)
#print (tx_params)

tb = b.get_my_token_balance(token_addresses.RMPL)
print ("token balance ",tb)

#print ("#pairs ", b.get_pairsn())


#pair_addr = b.get_pair_address_ETH(token_addresses.RMPL)
pctr = b.get_pair_contract_token(token_addresses.RMPL)
print ("info ",b.pair_info(pctr))
rev = b.get_reserves(pctr)
print ("reserves ",rev)

[reserves_eth, reserves_token] = b.get_reserves_info(pctr)
print ("get_reserves_info ",reserves_eth, reserves_token)

print ("get_balance_info ",b.get_balance_info(token_addresses.RMPL))

p = b.get_price_buy(token_addresses.RMPL, 9)
print (p)

bp = b.get_price_buy_float(token_addresses.RMPL, 9)
print (bp)

sp = b.get_price_sell_float(token_addresses.RMPL, 9)
print (sp)

spread = round((bp - sp)/sp,6)
print (f"{spread*100}%")

pi = b.get_pool_info_pair(pctr)
print (pi)

gas = b.getGas()
gasGwei = web3.fromWei(gas, 'gwei')
print (gas)
print (gasGwei)

# amount = b.approved_amount(token_addresses.RMPL)
# print (amount)

# decimals = 9
#b.sell_tokens(token_addresses.RMPL, amount, decimals)