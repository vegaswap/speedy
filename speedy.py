"""
speedy bot
uniswap v2
        
"""

import requests
import json
import pymongo
import os
import logging
import toml
import time
import binascii

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

AddressLike = Union[Address, ChecksumAddress, ENS]

from appconf import *
from consts import *

log_dir = wdir + "/logs"
#os.path.join(os.path.normpath(os.getcwd() + os.sep + os.pardir), 'logs')

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(log_dir + "/speedy.log"),
        logging.StreamHandler()
    ]
)

AddressLike = Union[Address, ChecksumAddress, ENS]

class Speedy(UniswapBot):

    def __init__(self):
        logging.info("init bot")

        config = toml.load(wdir + "/config.toml")
        self.max_slippage = config["MAX_SLIPPAGE"]
        td = config["TOKEN_DECIMALS"]
        self.TOKEN_DECIMALS = 10**td
        r = config["LIVE_RUN"]
        self.target_token = config["TARGET_TOKEN_ADDRESS"]
        if r == 0:
            self.LIVE_RUN = False
        elif r== 1:
            self.LIVE_RUN = True

        #self.gasprice = 484029841099 #484 gwei
        self.gas = Wei(250000)

        logging.info(f"max_slippage {self.max_slippage}")

        self.setup_conn()

        #medium_gas_price_strategy
        self.w3.eth.setGasPriceStrategy(fast_gas_price_strategy) 
                
        self.init_setup_contracts()
        
        # automatically approve for trading
        # max_approval is to allow the contract to exchange on your behalf
        # max_approval_check checks that current approval is above a reasonable number
        # cannot check for max_approval each time because it decreases with each trade
        # self.max_approval_hex = f"0x{64 * 'f'}"
        # self.max_approval_int = int(self.max_approval_hex, 16)
        # self.max_approval_check_hex = f"0x{15 * '0'}{49 * 'f'}"
        # self.max_approval_check_int = int(self.max_approval_check_hex, 16)        

        #self.pair_addr = self.get_pair_contract_weth(self.target_token)
        #self.pair_contract = self.get_pair_contract_weth(self.pair_addr)
        self.init_pair_contract(self.target_token)
        print ("self.pair_addr ",self.pair_addr)
        self.pairsn = self.get_pairsn()
        self.pairs = list()
        #self.store_last_pairs()
        self.reserves_show()



    def show(self):
        self.balance = self.get_eth_balance()
        balance_float = self.balance/10**18
        logging.info(f"ETH balance: {balance_float}")

        self.token_balance = self.get_token_balance(self.target_token)
        logging.info(f"Token balance {str(self.token_balance)}")

        #TODO call function
        buy_qty_nominal = 100
        buy_qty = buy_qty_nominal*self.TOKEN_DECIMALS
        est_price_total = self.getAmountsIn(buy_qty)
        est_price = est_price_total/buy_qty_nominal
        est_price_float = est_price/WETH_FACTOR
        eth_needed = est_price_total

        logging.info(f"est_price_total {est_price_total}")
        logging.info(f"est_price {est_price}")
        logging.info(f"est_price per token {est_price_float}")
        logging.info(f"need ETH {eth_needed} {eth_needed/WETH_FACTOR}")

        max_can_buy = balance_float/est_price_float
        logging.info(f"max can buy {max_can_buy}")

    def trade_action(self, BUY_QTY):
        """ the main loop or action performed by the bot"""
        BUY_QTY = 4500
        self.trade(BUY_QTY)
        #self.show()


    def trade(self, BUY_QTY):
        # just one time transactions
        self.balance = self.get_eth_balance()
        balance_float = self.balance/10**18
        logging.info(f"ETH balance: {balance_float}")

        self.token_balance = self.get_token_balance(self.target_token)
        logging.info(f"Token balance {str(self.token_balance)}")        

        self.buy_tokens(self.target_token, BUY_QTY)

    def reserves_show(self):
        #reserve0,reserve1,blockts = self.pair_contract.functions.getReserves().call()
        [reserve0,reserve1,blockts] = self.get_reserves(self.pair_contract)
        #reserve0, uint112 reserve1, uint32 blockTimesta
        dec0 = 10**18
        dec1 = 10**9
        reserves_eth = reserve0/dec0
        reserves_token = reserve1/dec1
        ETH_USD = 450
        reserves_eth_usd = reserves_eth*ETH_USD
        total_reserves = reserves_token + reserves_eth_usd 
        print ("reserves eth $",reserves_eth_usd)
        print ("reserves token ",reserves_token)
        print ("total_reserves ",total_reserves)

    def init_setup_tokens(self):
        #initial setup of tokens
            
        self.pairsn = self.get_pairsn()
        logging.info(f"uniswap pairsn {self.pairsn}")
        
        self.pairs = list()
        self.store_last_pairs()

    def store_last_pairs(self):
        """ check last pairs """
        logging.info(f"** last pairs created. total {self.pairsn} **")
        
        #for i in range(self.pairsn-n,self.pairsn-1):
        n = self.pairsn
        for i in range(n-10,n-1):
            a = self.get_pair(i)
            logging.info(f"pair {i} => {a}")   
            self.pairs.append(a)

        with open('pairs.json','w') as f:
            f.write(json.dumps(self.pairs))
  
    # def buy_tokens(self, token, buy_qty_nominal):
    #     recipient = self.myaddr
        
    #     buy_qty = buy_qty_nominal*self.TOKEN_DECIMALS
    #     logging.info (f"tokens to BUY {buy_qty}")

    #     est_price_total = self.getAmountsIn(buy_qty)
    #     est_price = est_price_total/buy_qty_nominal
    #     est_price_float = est_price/WETH_FACTOR
    #     eth_needed = est_price_total

    #     logging.info(f"est_price_total {est_price_total}")
    #     logging.info(f"est_price {est_price}")
    #     logging.info(f"est_price per token {est_price_float}")
    #     logging.info(f"need ETH {eth_needed} {eth_needed/WETH_FACTOR}")

    #     eth_balance = self.get_eth_balance()
    #     logging.info(f"got ETH {eth_balance/WETH_FACTOR}")

    #     if eth_needed > eth_balance:
    #         logging.info("not enough balance")

    #     else:
    #         logging.info("do trade")
            
    #         #ADD SLIPPAGE
    #         slip = int(self.max_slippage * buy_qty)
    #         adjusted_qty = buy_qty - slip

    #         amount_out_min = adjusted_qty
    #         logging.info(f"amount_out_min {amount_out_min}")

    #         route = [WETH, token]

    #         #amountOut	uint	The amount of tokens to receive.
    #         # msg.value (amountInMax)	uint	
    #         # The maximum amount of ETH that can be required before the transaction reverts.

    #         # swaptx = self.router.functions.swapETHForExactTokens(
    #         #     amount_out_min,
    #         #     route,
    #         #     recipient,
    #         #     self._deadline(),
    #         # )
    #         print (f"swaptx {swaptx}")
        
            
    #         #gasprice = self.w3.eth.generateGasPrice()
            
    #         #logging.info(f"using gasprice {self.gasprice}")
            
    #         eth_qty = self.router.functions.getAmountsIn(
    #             buy_qty, route
    #         ).call()[0]
    #         msg_value = eth_qty
    #         logging.info(f"eth_qty {eth_qty}")
        
    #         txparams = self._get_tx_params(msg_value, self.gas)

    #         if self.LIVE_RUN:
    #             logging.info("live mode")

    #             txidh = self._build_and_send_tx(swaptx, txparams)
                
    #             txid = binascii.hexlify(txidh)

    #             logging.info(f"txid {txid}")
    #             tx = self.w3.eth.getTransaction(txid)
    #             # myContract = web3.eth.contract(address=contract_address, abi=contract_abi)
    #             # tx_hash = myContract.functions.myFunction().transact()
    #             # receipt = web3.eth.getTransactionReceipt(tx_hash)
    #             # myContract.events.myEvent().processReceipt(receipt)
    #             gas_price = tx.gasPrice
    #             gas_used = tx.gasUsed                
    #             transaction_cost = gas_price * gas_used
    #             logging.info(f"gas_price {gas_price} gas_used {gas_used} transaction_cost {transaction_cost}")
                
    #         else:
    #             logging.info("demo mode")
    #         #print (receipt)
                        
    #         #self.w3.eth.waitForTransactionReceipt(tx)
    #         #return self._build_and_send_tx(tx,params)



########################################
#minl = pair_contract.functions.MINIMUM_LIQUIDITY().call()
#print ("minl " ,minl)
# p1 = pair_contract.functions.price0CumulativeLast().call()
# p2 = pair_contract.functions.price1CumulativeLast().call()
# print ("price1 ",p1)
# print ("price2 ",p2)    