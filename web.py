"""
mcaps web application
marketdata is fetched from coingecko stored in mongo and cached in redis
export PYTHONPATH="/Users/ben/mcaps/repos/assetdb"
"""

import sys
import os
import json
import pymongo
import redis
import flask
from flask import request, jsonify, url_for
from flask import render_template, redirect
from flask_cors import CORS, cross_origin
import time
import datetime
import os
import logging
import ssl

from speedy import *
from consts import * 
import token_addresses

app = flask.Flask(__name__,static_url_path='')

app.config.from_object('default_settings')

cors = CORS(app)

cstr = app.config["MONGO_CONN_STR"]
mclient = pymongo.MongoClient(cstr, ssl_cert_reqs=ssl.CERT_NONE)

#db = mclient[app.config["MONGO_DB"]]
db = mclient["speedy"]

bot = Speedy()

from decimal import Decimal
from bson.decimal128 import Decimal128

def listings(lastk):

    n = db.markets.count()
    token_counter = n
    l = list()
    
    x = n-lastk-1
    print (f"markets {n} {x}")
    eth_addr = "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"
    z = db.markets.find({"counter": {"$gt": x}, "token1": eth_addr}).sort([("counter", pymongo.DESCENDING)])

    for y in z:
        #print (y)
        try:
            ks = ['address', 'price', 'counter', 'token0', 'token1']
            d = {}
            for k in ks:
                d[k] = y[k]

            t = y['time_created']
            dt = t.strftime("%m/%d/%Y, %H:%M:%S")            
            d['time_created'] = dt
            #, 'reserve0', 'reserve1'
            r0d = y['reserves_eth']
            r1d = y['reserves_token']
            #/ETH_DECIMALS
            d['reserve0'] = r0d
            d['reserve1'] = r1d
            
            l.append(d)
        except Exception as e:
            print (e)
            continue

    return l

@app.route('/api/listings')
def listings_api():
    info = 'Uniswap listings'
    lastk = 20
    rows = listings(lastk)
    print (len(rows))
    return jsonify(rows)
    
@app.route('/')
def login_view():
    return render_template('login.html')

#@app.route('/')
@app.route('/listings')
def listings_view():
    info = 'Uniswap listings'
    lastk = 20
    rows = listings(lastk)
    num_markets = db.markets.count()
    return render_template('listings.html', title='Speedy', info=info, rows=rows, num_markets=num_markets)


# def get_pool_info():
#     [reserve0,reserve1,blockts] = bot.get_reserves(bot.pair_contract)    
#     target_token = bot.target_token
#     reserves_eth = round(reserve0/ETH_DECIMALS,1)
#     reserves_token = round(reserve1/bot.TOKEN_DECIMALS,1)
#     target_pair = bot.pair_addr
#     price = round(bot.get_price(),6)
#     #TODO
#     eth_balance = bot.get_eth_balance()/ETH_DECIMALS
#     max_buy = round(eth_balance/price,0)
#     percent=100
#     max_buy_pool = round(eth_balance/reserves_eth*percent,2)
#     #TODO get symbol
#     token_symbol = "RMPL"
#     d = {'target_token': target_token, 'reserves_eth': reserves_eth,'reserves_token': reserves_token, 'target_pair': target_pair, \
#         'price': price, 'max_buy': max_buy, 'max_buy_pool': max_buy_pool, 'token_symbol': token_symbol}
#     return d

@app.route('/balances')
def balances():
    address = bot.myaddr    
    max_slippage = bot.max_slippage
    eth_balance = bot.get_eth_balance()/ETH_DECIMALS
    token_balance = bot.get_token_balance(bot.target_token)/bot.TOKEN_DECIMALS
    live_run = bot.LIVE_RUN
    info = bot.get_pool_info()

    return render_template('balances.html', title='Speedy', eth_balance=eth_balance, token_balance=token_balance, \
        address=address, live_run=live_run, max_slippage=max_slippage, pool_info=info)

@app.route('/info')
def info():
    #address = bot.myaddr    
    #max_slippage = bot.max_slippage
    target_token = token_addresses.RMPL
    info = bot.get_pool_info(target_token)
    return render_template('info.html', title='Speedy', pool_info=info)


@app.route('/updateconfig', methods=['POST'])
def handle_data():
    TARGET_TOKEN = request.form['TARGET_TOKEN']
    print (TARGET_TOKEN)
    return jsonify("ok")
    # your code
    # return a response

@app.route('/config')
def config():
    live_run = bot.LIVE_RUN
    target_token = bot.target_token
    max_slippage = bot.max_slippage
    return render_template('config.html', title='Speedy', live_run=live_run, target_token=target_token, max_slippage=max_slippage)

@app.route("/login_post", methods=["GET", "POST"])
def login():
    if request.method == "POST":

        req = request.form.to_dict(flat=False)        
        password = req['password'][0]
        if password == "uniswap":
            return redirect(url_for('listings_view'))
        else:
            return redirect(url_for('login')) 
        
    #elif request.method == "GET":
    #    return redirect(url_for('listings_view')) 

@app.route("/handle_buy", methods=["POST"])
def handle_buy():
    if request.method == "POST":

        req = request.form.to_dict(flat=False)        
        qty = req['qty'][0]
        print (qty)
        
    #elif request.method == "GET":
    #    return redirect(url_for('listings_view')) 


if __name__ == '__main__':    
    app.run(host=app.config["APP_HOST"], port=app.config["APP_PORT"])
    

