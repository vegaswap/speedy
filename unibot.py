"""
uniswap bot base

swapExactETHForTokens
swapETHForExactTokens
swapTokensForExactETH
swapExactTokensForETH
"""
import toml
import logging
import binascii

from web3 import Web3, HTTPProvider, WebsocketProvider
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

from typing import List, Any, Optional, Callable, Union, Tuple, Dict
from contract_utils import *

from token_addresses import *
from appconf import *
from consts import *
import ethplorer

from coingecko import CoinGeckoAPI
cg = CoinGeckoAPI()    

import importlib

AddressLike = Union[Address, ChecksumAddress, ENS]

_netid_to_name = {1: "mainnet", 4: "rinkeby"}

log_dir = wdir + "/logs"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(log_dir + "/unibot.log"),
        logging.StreamHandler()
    ]
)

def value_gas_price_strategy(web3, transaction_params):
    #210900881855
    # if transaction_params['value'] > Web3.toWei(1, 'ether'):
    #     return Web3.toWei(20, 'gwei')
    # else:
    #     return Web3.toWei(5, 'gwei')
    return Web3.toWei(250, 'gwei')
        
class UniswapBot:
    """ uniswap wrapper bot """


    def buy_tokens_tx(self, token, amount_out_min):
        recipient = self.myaddr
        route = [WETH, token]
        swaptx = self.router.functions.swapETHForExactTokens(
                amount_out_min,
                route,
                recipient,
                self._deadline(),
        )
        return swaptx


    def getAmountsInR(self, qty: int, token) -> Wei:
        """ETH to Token trades with an exact output"""
        route = [token, WETH]
        price = self.get_amounts_in(qty, route)
        return price        

    def get_price_buyR(self, token, decimals):
        """ token-ETH quotation"""
        #buy_qty_nominal = 1*10**18
        buy_qty_nominal = 1
        #buy_qty = buy_qty_nominal*self.TOKEN_DECIMALS
        #buy_qty = buy_qty_nominal*(10**decimals)
        price = self.getAmountsInR(buy_qty_nominal, token)
        #price = price_total/buy_qty_nominal
        
        return price        


    


    
    def _get_tx_params(self, value: Wei, gas: Wei) -> TxParams:
        """Get generic transaction parameters."""
        extra_unconfirmed = 6
        #TODO
        gas = self.get_gas()
        
        txcount = self.w3.eth.getTransactionCount(self.myaddr)
        #TMP bug fix if unconfirmed pending
        #https://ethereum.stackexchange.com/questions/27256/error-replacement-transaction-underpriced
        txcount += extra_unconfirmed
        return {
            "from": addr_to_str(self.myaddr),
            "value": value,
            "gas": gas,
            "nonce": max(
                self.last_nonce, txcount
            ),
        }



                

    def buy_eth_qty(self, buy_qty, route):
        eth_qty = self.router.functions.getAmountsIn(
                buy_qty, route
        ).call()[0]
        return eth_qty

    def buy_tokens(self, token, buy_qty_nominal):
        #TODO clean up
        
        recipient = self.myaddr
        
        #buy_qty = buy_qty_nominal*self.TOKEN_DECIMALS
        buy_qty =  buy_qty_nominal*(10**self.TOKEN_DECIMALS)
        logging.info (f"tokens to BUY {buy_qty_nominal} ({buy_qty})")

        price = self.get_price_buy(token, self.TOKEN_DECIMALS)
        logging.info(f"price {price}")        

        eth_needed = price*buy_qty

        #logging.info(f"est_price per token {est_price_float}")
        logging.info(f"need ETH {eth_needed} {eth_needed/WETH_FACTOR}")


        eth_balance = self.get_eth_balance()
        logging.info(f"got ETH {eth_balance/WETH_FACTOR}")

        if eth_needed > eth_balance:
            logging.info("not enough balance")

        else:
            logging.info("do trade")
            
            #ADD SLIPPAGE
            slip = int(self.max_slippage * buy_qty)            

            amount_out_min = buy_qty - slip
            
            logging.info(f"amount_out_min {amount_out_min}")

            #TODO! check with reverse order
            route = [WETH, token]
        
            #TODO! replace with price function
            eth_qty = self.buy_eth_qty(buy_qty, route)
            
            # msg.value (amountInMax)
            # The maximum amount of ETH that can be required before the transaction reverts.
            max_eth = eth_qty
            max_value_float = max_eth/WETH_FACTOR

            swaptx = self.buy_tokens_tx(token, amount_out_min)

            print (f"swaptx {swaptx}")

            logging.info(f"eth_qty {eth_qty} msg_value_float {max_value_float}")

            txparams = self._get_tx_params(max_eth, self.gas)

            if self.LIVE_RUN:
                logging.info("live mode")
                txid = self._build_and_send_tx(swaptx, txparams)
                logging.info(f"receipt {txid}")
                tx = self.w3.eth.getTransaction(txid)
                logging.info(f"tx {tx}")
                gas_price = tx.gasPrice
                gas_used = tx.gasUsed
                #gas_used = self.w3.getTransactionReceipt(receipt).gasUsed
                transaction_cost = gas_price * gas_used
                logging.info(f"gas_price {gas_price} gas_used {gas_used} transaction_cost {transaction_cost}")
                # print (receipt)
            else:
                logging.info("demo mode")


    def show_balance_info(self):
        b = self.get_balance_info(self.target_token)
        pool_info = self.get_pool_info(self.target_token)
        pf = pool_info["price_float"]
        price_usd = pf*b['eth_usd']
        
        token_balance_usd = round(b['token_balance_nom']*price_usd,0)
        logging.info("*** show_balance_info ***")
        logging.info(f"eth_balance_float {round(b['eth_balance_float'],2)}")
        logging.info(f"Token balance {str(b['token_balance'])}")
        logging.info(f"Token balance {str(b['token_balance_nom'])}")
        logging.info(f"token_balance $: {token_balance_usd}")
        logging.info(f"eth_balance $:  {b['eth_balance_usd']}")
        logging.info(f"price {round(pf,6)}   {round(price_usd,3)} $")

    # def get_token(self, address: AddressLike) -> dict:
    #     # FIXME: This function should always return the same output for the same input
    #     #        and would therefore benefit from caching
    #     token_contract = self._load_contract(abi_name="erc20", address=address)
    #     try:
    #         symbol = token_contract.functions.symbol().call()
    #         name = token_contract.functions.name().call()
    #     except Exception as e:
    #         logger.warning(
    #             f"Exception occurred while trying to get token {addr_to_str(address)}: {e}"
    #         )
    #         raise InvalidToken(address)
    #     return {"name": name, "symbol": symbol}  