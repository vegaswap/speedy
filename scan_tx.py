"""
scan uniswap for transactions
"""

import toml
import web3
from web3 import Web3, HTTPProvider, WebsocketProvider

router_address = "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D"

secrets = toml.load("./secrets.toml")
privateKey = secrets["PRIVATEKEY"]
INFURA_KEY = secrets["INFURA_KEY"]                
INFURA_URL = "https://mainnet.infura.io/v3/" + INFURA_KEY
w3 = Web3(HTTPProvider(INFURA_URL))

lblock = w3.eth.getBlock('latest')

txs = lblock['transactions']
print (f"block {lblock['number']}  #tx {len(txs)}")
for tx in txs: 
    txh = tx.hex()
    z = w3.eth.getTransaction(txh)
    if z['to'] == router_address:
        print ("to uniswap ", txh[:])
    elif z['from'] == router_address:
        print ("from uniswap ", txh[:])
    # else:
    #     print (txh[:5])
