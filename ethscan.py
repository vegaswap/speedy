"""
etherscan events
"""
import requests
import json
import time

etherscan_ApiKeyToken="DYBBRKBGT76MEBPTE57HYIGR7MVJGY1B5A"

base_url = "https://api.etherscan.io/api"

def est_confirm_time(gas):
    url = base_url + "?module=gastracker&action=gasestimate&gasprice=%i&apikey=%s"%(gas,etherscan_ApiKeyToken)
    x = requests.get(url)
    return int(json.loads(x.content)["result"])

def get_block():
    ts = int(time.time())
    url = base_url + "?module=block&action=getblocknobytime&timestamp=%i&closest=before&apikey=%s"%(ts, etherscan_ApiKeyToken)
    x = requests.get(url)
    return int(json.loads(x.content)["result"])

def scan_events():
    """ scan createPair events. tx hash of last blocks"""
    uniswap_contract_addr = "0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f"
    
    #from_block = get_block()-1
    lastN = 20
    from_block = get_block()-lastN
    print ("block " + str(from_block))
    url = base_url + "?module=logs&action=getLogs&fromBlock=%i&toBlock=latest&address=%s&apikey=%s"%(from_block, uniswap_contract_addr, etherscan_ApiKeyToken)
    #print (url)
    x = requests.get(url)
    logs = json.loads(x.content)["result"]
    for l in logs:
        print (l['transactionHash'])

def poll_events():
    while True:
        scan_events()
        time.sleep(1.0)

f = get_block()
print (f)
#poll_events()
#&topic0=0xf63780e752c6a54a94fc52715dbc5518a3b4c3c2833d301a204226548a2a8545

# url = "https://etherscan.io/tx/0x3e020196be6b46331a08b49610e9391e21eb6b80cd0fa79728063374acced516"
# x = requests.get(url)
# print (x.content)