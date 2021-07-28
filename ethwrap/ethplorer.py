import requests
import json
import ethwrap.manager as manager

BASE_URL = "https://api.ethplorer.io/"

api_key = ""

def init():
    api_key = manager.get_ethplorer_key()

def get_info(tokenaddress):
    url = BASE_URL + "getTokenInfo/%s?apiKey=%s"%(tokenaddress, api_key)
    r = json.loads(requests.get(url).content)
    return r

def get_decimals(tokenaddress):
    info = get_info(tokenaddress)    
    return int(info['decimals'])
