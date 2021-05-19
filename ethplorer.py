import requests
import json

BASE_URL = "https://api.ethplorer.io/"
api_key = "EK-3RZq5-EkCfUCw-GJL9j"

def get_info(tokenaddress):
    url = BASE_URL + "getTokenInfo/%s?apiKey=%s"%(tokenaddress, api_key)
    r = json.loads(requests.get(url).content)
    return r

def get_decimals(tokenaddress):
    info = get_info(tokenaddress)
    return int(info['decimals'])

def address_history(address):
    #/getAddressHistory/{address}
    url = BASE_URL + "getAddressHistory/%s/?apiKey=%s"%(address, api_key)
    r = json.loads(requests.get(url).content)
    return r

def address_tx(address):
    url = BASE_URL + "getAddressTransactions/%s/"%(address)
    p = {'apiKey':api_key, 'limit': 50}
    #requests.get('http://youraddress.com', params=evt.fields)
    result = requests.get(url, params=p)
    print (result.url)

    r = json.loads(result.content)
    return r
    #getAddressTransactions
    
a = "0xe17f017475a709de58e976081eb916081ff4c9d5"
r = address_tx(a)
print (len(r))

#tokenaddress = "0x33ea42ecab4681b4a983b9d39c4a7e16dc107df8"
#x = "0x6a3D23fA07c455F88D70c29D230467C407a3964b"
#get_decimals(tokenaddress)
#print (get_info(x))