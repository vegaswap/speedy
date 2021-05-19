from enum import Enum

import requests
import time

from graph import *

import logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        # logging.FileHandler("./logs/monitor.log"),
        logging.StreamHandler()
    ]
)


WETH = "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2"
TUSD = "0xdac17f958d2ee523a2206206994597c13d831ec7"
base_pairs = [WETH, TUSD]
base_pairs_dict = {WETH: "WETH", TUSD: "TUSD"}
base_pairs_name = ["WETH", "USDT", "DAI"]



def query_unifactory():
    """ get number of pairs """
    response = requests.post(uniswap_graph_url, json=dict(query=create_query(
        "uniswapFactories",
        Conditions([
            LimitCondition(1)
        ]),
        Fields([
            "id",
            "pairCount",
            "totalVolumeUSD",
        ])
    )))
    res = response.json()
    return res.get("data", {}).get("uniswapFactories", [])


def pair_count():
    """ get pair count from unifactory """
    uni = query_unifactory()
    return uni[0]["pairCount"] if len(uni) > 0 else 0


tokenFields = {
    "id",
    "decimals",
    "symbol",
    "name",
    "totalSupply",
    "totalLiquidity",
}

all_fields = [
    "id",
    "reserve0",
    "reserve1",
    "volumeUSD",
    "reserveUSD",
    "createdAtTimestamp",
    {
        "token0": tokenFields
    },
    {
        "token1": tokenFields
    }
]

ff = [
    "id",
    "amount0In",
    "amount0Out",
    "amount1In",
    "amount1Out",
    "amountUSD",
    "timestamp"
]

def query_pairs_cond(limit, start_time, vx=None, liqmin=None):
    wheres = [ConditionField("createdAtTimestamp", start_time, Operator.GREATER_THAN)]
    if vx is not None:
        wheres.append(ConditionField("volumeUSD", vx, Operator.GREATER_THAN))

    if liqmin is not None:
        wheres.append(ConditionField("reserveUSD", liqmin, Operator.GREATER_THAN))

    
    response = requests.post(uniswap_graph_url, json=dict(query=create_query(
        "pairs",
        Conditions([
            LimitCondition(limit),
            WhereCondition(wheres),
            OrderCondition("volumeUSD", Sort.DESC.value)
        ]),
        Fields(all_fields)
    )))
    #print ("response" ,response.json())
    rj = response.json()
    p = rj.get("data", {}).get("pairs")    
    return p


def query_pairs(limit):
    logging.info("query_pairs")
    days_lookback = 10
    condition = ""
    # if latest_pair_id != "":
    #     start_time =  int(latest_pair_id.timestamp())
    # else:
    thirtydays = 60*60*24*days_lookback
    start_time = int(time.time()-thirtydays)
    vx = 1000
    pairs = query_pairs_cond(limit, start_time, vx)
    return pairs

def new_listings(minutes):    
    start_time = int(time.time()) - minutes * 60
    pairs = query_pairs_cond(100, start_time)
    return pairs

def replace_name(a):
    """ replace name with string """
    for b in base_pairs:
        if a == b:
            return base_pairs_dict[a]
    return a

def reverse_order(a0,a1):
    if a1 in base_pairs_dict.values():
        return a0,a1
    else:
        return a1,a0

def scan_query():
    pairs = query_pairs(100)
    print ("***\npair volumeUSD reserve days active\n***")
    pf = dict()
    pfl = list()
    for p in pairs:
        #print ("reserve0 ",p['reserve0'],p['reserve1'],
        v = int(float(p['volumeUSD']))
        r0 = int(float(p['reserve0']))
        r1 = int(float(p['reserve1']))
        t = p['createdAtTimestamp']
        #print (p['token0']['name'],p['token1']['name'],v,r0, r1)
        #print (p['token0']['name'],p['token1']['name'],v)

        s0  = p['token0']['symbol']
        s1  = p['token1']['symbol']

        id0 = p['token0']['id']
        id1 = p['token0']['id']

        tdif = round((time.time()-int(t))/(60*60*24),1)        
        #s0,s1 = reverse_order(s0,s1)
        if s0 in base_pairs_dict.values():
            s1,s0 = s0,s1
            id1,id0 = id0,id1
        
        l = int(float(p['reserveUSD']))

        pn = s0 + "-" + s1
        d = {'pairname': pn, 'volume': v, 'liquidity': l, 'timedif': tdif, 'symbol0': s0, 'symbol1': s1, 'id0': id0, 'id1': id1}
        pfl.append(d)
        pf[pn] = [v,l,tdif]

    #pf = dict(sorted(pf.items(), key=lambda item: item[1]))
    #pf = {v: k for k, v in pf.items()}
    #for k,v in pf.items():
    #for k in reversed(sorted(pf.keys())):
    #    print (k,pf[k][0],pf[k][1],pf[k][2])
    # for v in pfl:
    #     print(v)
    
    return pfl

def get_pair_data():
    USDETH = '0xb4e16d0168e52d35cacd2c6185b44281ec28c9dc'
    #wheres = [ConditionField("id", USDETH, Operator.STARTS_WITH)]
    wheres = "{ id: '0xb4e16d0168e52d35cacd2c6185b44281ec28c9dc'}"

    # wheres.append('{ pair: "0xa478c2975ab1ea89e8196811f51a7b7ade33eb11" }')
    # tquery = create_query(
    #     "swaps",
    #     Conditions([
    #         "first: 1000, skip: 700000, orderBy: timestamp, orderDirection: desc",
    #         WhereCondition(wheres)
    #     ]),
    #     # Conditions([
    #     #     WhereCondition(wheres)
    #     # ]),
    #     Fields(ff)
    # )


    tquery = '''
    {
    swaps(first: 1000, skip: 700000, orderBy: timestamp, orderDirection: desc, where:
    { pair: "0xa478c2975ab1ea89e8196811f51a7b7ade33eb11" }
    ) {
        id
        amount0In
        amount0Out
        amount1In
        amount1Out
        amountUSD
        to
        timestamp
    }
    }
    '''
    print (tquery)
    response = requests.post(uniswap_graph_url, json=dict(query=tquery))
    #print (response.json())
    
    rj = response.json()
    #print (rj)
    #p = rj.get("data").get("transactions")
    p = rj.get("data").get("swaps")
    #print (p)
    #p = [x['swaps'] for x in p]
    return p

