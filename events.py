


"""
event listener
"""

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

class EventListener(Uniwrap):

    def __init__(self):
        super().__init__()
        logging.info("init bot")

        #self.init_pair_contract(token_addresses.RMPL)
        self.init_pair_contract(token_addresses.UNI)
        ctr = self.pair_contract
        print (ctr.events)

        lb = self.w3.eth.blockNumber
        #event_filter = ctr.events.Mint.createFilter(fromBlock='latest') #, argument_filters={'arg1':10})
        lookback = 1000
        event_filter = ctr.events.Mint.createFilter(fromBlock=(lb-lookback))
        print (event_filter)

        evs = event_filter.get_all_entries()
        print (f"*** mints last {lookback} blocks ***")
        for ev in evs:
            print (ev['transactionHash'].hex())
        #.Issued("to", "value")



e = EventListener()
