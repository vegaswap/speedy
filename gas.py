#https://github.com/ethereum/web3.py/issues/894

import json
import requests
from web3 import Web3, HTTPProvider

from web3 import Web3, middleware
from web3.gas_strategies.time_based import medium_gas_price_strategy

w3 = Web3()
w3.eth.setGasPriceStrategy(medium_gas_price_strategy)

gasprice = web3.eth.generateGasPrice()
print (f"gasprice {gasprice}")

#w3.middleware_onion.add(middleware.time_based_cache_middleware)
#w3.middleware_onion.add(middleware.latest_block_based_cache_middleware)
#w3.middleware_onion.add(middleware.simple_cache_middleware)

etherscan_ApiKeyToken="DYBBRKBGT76MEBPTE57HYIGR7MVJGY1B5A"

base_url = "https://api.etherscan.io/"

def est_confirm_time(gas):
    url = base_url + "api?module=gastracker&action=gasestimate&gasprice=%i&apikey=%s"%(gas,etherscan_ApiKeyToken)
    x = requests.get(url)
    return int(json.loads(x.content)["result"])

def gas_oracle():
    url = base_url + "api?module=gastracker&action=gasoracle&apikey=%s"%(YourApiKeyToken)
    x = requests.get(url)
    return int(json.loads(x.content)["result"])

#gas=99990000000
#ctime = est_confirm_time(gas)
#gas_eth = Web3.fromWei(gas, 'ether')
#gas_eth = Web3.fromWei(gas, 'ether')
#ETH_USD = 450
#gas_usd = gas_eth * ETH_USD
#print (f"ctime {ctime} ... {gas_eth} {gas_usd}")

#web3.gas_strategies.time_based.fast_gas_price_strategy
