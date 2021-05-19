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
import ethplorer
from datetime import datetime

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
import ethplorer

from unibot import UniswapBot

from decimal import Decimal
from bson.decimal128 import Decimal128
from uniwrap import Uniwrap

AddressLike = Union[Address, ChecksumAddress, ENS]

WETH_DECIMALS = 18
WETH_FACTOR = 10**WETH_DECIMALS

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("./logs/monitor.log"),
        logging.StreamHandler()
    ]
)

AddressLike = Union[Address, ChecksumAddress, ENS]

class Monitor(Uniwrap):

    def __init__(self):
        super().__init__()
        logging.info("init monitor")

        # config = toml.load("config.toml")
        # td = config["TOKEN_DECIMALS"]
        # self.TOKEN_DECIMALS = 10**td
        # r = config["LIVE_RUN"]
        # if r == 0:
        #     self.LIVE_RUN = False
        # elif r== 1:
        #     self.LIVE_RUN = True

        # #self.target_token = config["TARGET_TOKEN"]
        
                
        self.pairsn = self.get_pairsn()
        # logging.info("UNISWAP INFO")
        # #logging.info(f"number of pairs: {self.pairsn}")
        # #self.store_last_pairs()
        # pa = "0x8427543aF82EC787eF8dAd29eB7B65358b95D125"
        # #self.store_token(pa)

    def store_token(self, pair_addr):
        self.pair_contract = self._load_contract(
            abi_name="UniswapV2Pair", address=pair_addr,
        )
        reserve0,reserve1,blockts = self.pair_contract.functions.getReserves().call()
        token_addr0 = self.pair_contract.functions.token0().call()
        token_addr1 = self.pair_contract.functions.token1().call()

        logging.info(f"token_addr0 {token_addr0}")
        logging.info(f"token_addr1 {token_addr1}")

    def show_all(self, pair_addr):
        #self.pair_contract = self.get_pair_contract_weth(token)
        
        pair_contract = self._load_contract(
            abi_name="UniswapV2Pair", address=pair_addr,
        )
        logging.info(f"*** info for {pair_addr} ***\n")

        token_addr0 = pair_contract.functions.token0().call()
        token_addr1 = pair_contract.functions.token1().call()
        dec0 = ethplorer.get_decimals(token_addr0)
        dec1 = ethplorer.get_decimals(token_addr1)
        logging.info(f"dec0 {dec0} dec1 {dec1}")        

        logging.info(f"token_addr0 $ {token_addr0}")
        logging.info(f"token_addr1 $ {token_addr1}")

        reserve0, reserve1, blockts = pair_contract.functions.getReserves().call()
        #logging.info(f"reserves token {reserves_token}")
        logging.info(f"reserve0 {reserve0}")
        logging.info(f"reserve1 {reserve1}")
        
        
        reserves_token = reserve0/(10**dec0)
        reserves_eth = reserve1/(10**dec1)
        ETH_USD = 450
        reserves_eth_usd = reserves_eth*ETH_USD
        total_reserves = reserves_token + reserves_eth_usd 
        logging.info(f"reserves eth $ {reserves_eth_usd}")
        logging.info(f"reserves token {reserves_token}")
        logging.info(f"total_reserves {total_reserves}")

        buy_qty_nominal = 100
        #buy_qty = buy_qty_nominal*self.TOKEN_DECIMALS
        route = [WETH, token_addr0]
        est_price_total = self.get_amounts_in(buy_qty_nominal, route)
        est_price = est_price_total/buy_qty_nominal
        est_price_float = est_price/WETH_FACTOR
        logging.info(f"price for {buy_qty_nominal}: {est_price} {est_price_float}")

        
    def store_last_pairs(self, ifrom, ito):
        logging.info(f"** total {self.pairsn}. ** \nlast pairs created.  **")
        
        #for i in range(self.pairsn-n,self.pairsn-1):
                
        for token_counter in range(ifrom,ito):
            a = self.get_pair(token_counter)
            logging.info(f"pair {token_counter} => {a}")   
            #self.pairs.append(a)

            cc = db.markets.find({"counter": token_counter}).count()
            if cc == 0: 
                #print (cc)
                
                time_created =  datetime.now()                
                d = {"address":a, "counter": token_counter, "time_created": time_created}
                logging.info("insert market " + str(d))
                db.markets.insert_one(d)
            else:
                print ("exists already")

        #with open('pairs.json','w') as f:
        #    f.write(json.dumps(self.pairs))

    def update_token_info(self):
        n = db.markets.count()
        start = 0
        for token_counter in range(start,n-1):
            #a = self.get_pair(token_counter)
            pa = db.markets.find_one({"counter": token_counter})
            token_addrs = [pa["token0"],pa["token1"]]
            for token_addr in token_addrs:
                info = self.get_token_info(token_addr)
                db.tokens.update({"address": token_addr, "token": info}, upsert=True)
            

    def update_tokens(self):
        n = db.markets.count()
        #k = 10
        
        print (f"\n*** tokens ***")
        #start = 895
        start = 2944
        #for token_counter in range(n-k,n):
        for token_counter in range(start,n-1):
            #a = self.get_pair(token_counter)
            pa = db.markets.find({"counter": token_counter})[0]
            logging.info(f"{pa}")
            a = pa['address']
            v = self.get_token_addresses(a)
            print (f">> {v}")
            newvalues = { "$set": v }

            db.markets.update_one({"counter": token_counter}, newvalues)
            # t = pa['time_created']
            # dt = t.strftime("%m/%d/%Y, %H:%M:%S")
            #logging.info(f"a {a} dt {dt}")       

    def show_pairs(self):
        n = db.markets.count()
        k = 10
        
        print (f"\n*** last {k} markets ***")
        #for token_counter in range(n-k,n):
        for token_counter in range(n-k,n-1):
            #a = self.get_pair(token_counter)
            pa = db.markets.find({"counter": token_counter})[0]
            a = pa['address']
            t = pa['time_created']
            dt = t.strftime("%m/%d/%Y, %H:%M:%S")
            logging.info(f"a {a} dt {dt}")   

    def update_markets_list(self):
        #1. check total number of existing markets
        #2. compare with DB
        #3. update delta
        n = self.pairsn
        #self.get_pairsn()
        stored = db.markets.find().count()
        new_markets = n - stored
        
        print (f"number of markets. existing {n} {stored}. update {new_markets}")

        #ifrom = stored-5
        
        if new_markets > 0:
            self.store_last_pairs(stored, n)
        else:
            print ("no new markets")
   
    def update_market_dynamic(self, k):
        n = db.markets.count()
            
        start = n-k
        for token_counter in range(start,n):
            pa = db.markets.find({"counter": token_counter})[0]
            print (pa)
            pair_addr = pa['address']
            # pair_contract = self._load_contract(
            #     abi_name="UniswapV2Pair", address=pair_addr,
            # )
            # logging.info(f"*** info for {pair_addr} ***\n")
            #pool_info = self.get_pool_info_pair(pa)
            try:
                pool_info = self.get_pool_info_pair(pair_addr)
                print (pool_info)
                    
                #token_addr0 = pair_contract.functions.token0().call()
                #v = { "price": price, "reserve0": r0f, "reserve1": r1f}
                newvalues = { "$set": pool_info }
                
                db.markets.update_one({"counter": token_counter}, newvalues)
            except Exception as e:
                logging.error(f"update error {e}")

    def get_token_info(self, token_addr):
        try:
            token_info = ethplorer.get_info(token_addr)
            #print (token_info)
            token_decimals = int(token_info["decimals"])
            token_symbol = token_info["symbol"]
            totalSupply = token_info["totalSupply"]
            name = token_info["name"]            
        except Exception as e:
            print ("no info for {pair_addr}")
            token_decimals, token_symbol, name, totalSupply = "NA", "NA", "NA", 0

        v = {"token_decimals": token_decimals, "token_symbol": token_symbol, "totalSupply": totalSupply, "name": name}
        return v

    def get_token_addresses(self, pair_addr):
        pair_contract = self.load_contract(
            abi_name="UniswapV2Pair", address=pair_addr,
        )                        
        token_addr0 = pair_contract.functions.token0().call()
        token_addr1 = pair_contract.functions.token1().call()

        v = { "token0": token_addr0, "token1": token_addr1}
            # "token_decimals0": token_decimals0, "token_symbol0": token_symbol0, "totalSupply0": totalSupply0, "name0": name0, \
            # "token_decimals1": token_decimals1, "token_symbol1": token_symbol1, "totalSupply1": totalSupply1, "name1": name1 
            
        return v

    def update_one_static(self, pair_addr):
        pair_contract = self.load_contract(
            abi_name="UniswapV2Pair", address=pair_addr,
        )                        
        token_addr0 = pair_contract.functions.token0().call()
        token_addr1 = pair_contract.functions.token1().call()

        token_info = ethplorer.get_info(token_addr0)
        try:
            print (token_info)
            token_decimals = int(token_info["decimals"])
            token_symbol = token_info["symbol"]
            totalSupply = token_info["totalSupply"]
            name = token_info["name"]
        except Exception as e:
            print ("no info for {pair_addr}")
            token_decimals, token_symbol, name, totalSupply = "NA", "NA", "NA", 0

        v = { "token0": token_addr0, "token1": token_addr1, "token_decimals": token_decimals, \
            "token_symbol": token_symbol, "totalSupply": totalSupply, "name": name }
        newvalues = { "$set": v }
        logging.info(f"newvalues {newvalues}")
        db.markets.update_one({"counter": token_counter}, newvalues)

    def update_market_static(self, k):
    #def update_market_info(self):
        n = db.markets.count()
            
        start = n-k
        logging.info(f"update market info {start} {n}")        
        for token_counter in range(start,n):
            pa = db.markets.find({"counter": token_counter})[0]
            pair_addr = pa['address']
            self.update_one_static(pair_addr)
            
            time.sleep(0.3)


    def update_loop(self):
        while True:
            self.update_markets_list()
            self.update_market_dynamic(20)
            time.sleep(10.0)

def show_details(db):
    markets = db.markets.find()
    print (len(markets))
    # num total pairs
    # num TOKENS
    # ETH pairs


if __name__=='__main__':
    cstr = "mongodb+srv://ben:GmWGdBL3gpEJU9g@mcaps-olf5s.mongodb.net/test?retryWrites=true&w=majority"
    import ssl
    mclient = pymongo.MongoClient(cstr,ssl_cert_reqs=ssl.CERT_NONE)
    db = mclient["speedy"]
    #show_details(db)
    
    mon = Monitor()
    mon.update_tokens()
    #mon.update_loop()

    #mon.update_markets_list()
    #mon.update_market_static(20)
    #mon.update_market_dynamic(10)

    #a = "0xd5fB669dB8F85C2bE391aDEFFE7E8C781995795b"    
    #mon.update_markets_loop()
    #mon.update_markets()
    #mon.update_market_info()
    #mon.show_all(a)
    #mon.show_pairs()

    


