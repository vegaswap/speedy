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

from appconf import *
from consts import *
import ethplorer

from ethwrap.contract_utils import *
import ethwrap.token_addresses as token_addresses
import ethwrap.manager as manager
import ethwrap.erc20 as erc20
import ethwrap.ethplorer as ethplorer

w3 = manager.get_w3()


from coingecko import CoinGeckoAPI
cg = CoinGeckoAPI()    

import importlib

AddressLike = Union[Address, ChecksumAddress, ENS]

_netid_to_name = {1: "mainnet", 4: "rinkeby"}

uniswap_factory_address_v2 = str_to_addr("0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f")
uniswap_router_address = str_to_addr("0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D")

log_dir = wdir + "/logs"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(log_dir + "/uniwrap.log"),
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
        
class Uniwrap(manager.Manager):
    """ uniswap wrapper bot """

    def __init__(self):
        super().__init__()
        logging.info("init Uniwrap")

        self.last_nonce: Nonce = self.w3.eth.getTransactionCount(self.myaddr)

        #self.gasprice = 484029841099 #484 gwei
        wdir = "."
        config = toml.load(wdir + "/config.toml")
        gas_strategy = config["GAS_STRATEGY"]
        self.gas = Wei(config["GAS"])
        self.gasPrice = config["GASPRICE"]
        #
        if gas_strategy == "medium":
            self.w3.eth.setGasPriceStrategy(medium_gas_price_strategy) 
        elif gas_strategy == "fast":
            self.w3.eth.setGasPriceStrategy(fast_gas_price_strategy) 
        #self.w3.eth.setGasPriceStrategy(value_gas_price_strategy)

        self.init_setup_contracts()

        self.target_token_symbol = config["TARGET_TOKEN"]
        token_dict = self.get_token_dict()
        self.target_token = Web3.toChecksumAddress(token_dict[self.target_token_symbol])
        print (self.target_token)

        self.max_slippage = config["MAX_SLIPPAGE"]
        self.TOKEN_DECIMALS = config["TOKEN_DECIMALS"]
        logging.info(f"TOKEN DECIMALS  {self.TOKEN_DECIMALS}")

        r = config["LIVE_RUN"]
        if r == 0:
            self.LIVE_RUN = False
        elif r== 1:
            self.LIVE_RUN = True

    def get_token_dict(self):
        module = importlib.import_module('token_addresses')
        token_dict = {}
        token_dict.update({k: v for k, v in module.__dict__.items() if not k.startswith('_')})
        return token_dict

    def init_setup_contracts(self):
        logging.info("init_setup_contracts")
        
        self.factory_contract = self.load_contract(abi_name="UniswapV2Factory", address=uniswap_factory_address_v2,)

        # https://uniswap.org/docs/v2/smart-contracts/router02/
        #self.router_address = uniswap_router_address
        self.router = self.load_contract(abi_name="UniswapV2Router02", address=uniswap_router_address)


    def get_pairsn(self):
        return self.factory_contract.functions.allPairsLength().call()

    def get_pair(self, i):
        return self.factory_contract.functions.allPairs(i).call()

    def init_pair_contract(self, token_address):
        pair_addr = self.factory_contract.functions.getPair(token_addresses.WETH, token_address).call()
        self.pair_addr = Web3.toChecksumAddress(pair_addr)
        self.pair_contract = self.get_pair_contract_weth(self.pair_addr)

    def _deadline(self) -> int:
        """Get a predefined deadline. 10min by default (same as the Uniswap SDK)."""
        return int(time.time()) + 10 * 60

    def get_reserves(self, pair_contract):
        reserve0,reserve1,blockts = pair_contract.functions.getReserves().call()
        return [reserve0,reserve1,blockts]

    def pair_info(self, pair_contract):
        token_addr0 = pair_contract.functions.token0().call()
        token_addr1 = pair_contract.functions.token1().call()
        pair_type = ""
        if token_addr0==token_addresses.WETH:
            pair_type="ETH-TOKEN"
        elif token_addr1==token_addresses.WETH:
            pair_type="TOKEN-ETH"
        else:
            pair_type="TOKEN-TOKEN"
        return [token_addr0, token_addr1, pair_type]

    def get_reserves_info(self, pair_contract):
        [reserve0,reserve1,blockts] = self.get_reserves(pair_contract)
        [token_addr0, token_addr1, pair_type] = self.pair_info(pair_contract)
        #print (pair_type)
        #TODO this assumes ETH-TOKEN
        reserves_eth = round(reserve0/WETH_FACTOR,1)
        token_info = self.get_token_info(token_addr1)
        token_decimals = int(token_info["decimals"])
        reserves_token = round(reserve1/(10**token_decimals),1)
        return [reserves_eth, reserves_token]

    def get_pair_address_ETH(self, token_address):
        pair_addr = self.factory_contract.functions.getPair(token_addresses.WETH, token_address).call()
        pair_addr = Web3.toChecksumAddress(pair_addr)
        return pair_addr

    def get_pair_address_TK(self, token_address):
        pair_addr = self.factory_contract.functions.getPair(token_address, token_addresses.WETH).call()
        pair_addr = Web3.toChecksumAddress(pair_addr)
        return pair_addr

    def get_pair_contract_weth(self, pair_addr):
        pair_contract = self.load_contract(
            abi_name="UniswapV2Pair", address=pair_addr,
        )
        return pair_contract

    def get_pair_contract_token(self, token_address):
        contract_addr = self.get_pair_address_ETH(token_address)
        pair_contract = self.get_pair_contract_weth(contract_addr)
        return pair_contract

    def get_balance_info(self, token):
        eth_balance = self.get_eth_balance()
        eth_balance_float = eth_balance/WETH_FACTOR
        self.eth_usd = self.get_eth_usd()
        eth_balance_usd = round(eth_balance * self.eth_usd/WETH_FACTOR, 0)        
        token_info = self.get_token_info(token)
        decimals = int(token_info['decimals'])        
        token_balance = self.get_token_balance(token, self.myaddr)
        token_balance_nom = token_balance/(10**decimals)
        #token_balance_usd = round(token_balance_nom*price_usd,0)

        d = {'eth_balance': eth_balance, 'eth_balance_float': eth_balance_float, 'eth_usd': self.eth_usd, 'eth_balance_usd': eth_balance_usd, \
            'decimals': decimals , 'token_balance': token_balance, 'token_balance_nom': token_balance_nom, \
            #'token_balance_usd': token_balance_usd
            }
        return d

    def get_amounts_out(self, qty, route) -> Wei:
        """ETH to Token trades with an exact input"""        
        price = self.router.functions.getAmountsOut(
                qty, route
            ).call()[-1]
        return price    

    def get_amounts_in(self, qty, route):
        try:
            #trying  1 ['0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2', '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2']
            price = self.router.functions.getAmountsIn(
            qty, route
            ).call()[0]
            logging.debug(f"get_amounts_in {price} qty: {qty}")
            return price
        except Exception as e:
            print (e)

    def getAmountsOut(self, qty: Wei, token) -> Wei:
        """ETH to Token trades with an exact input"""
        route = [token, token_addresses.WETH]
        price = self.get_amounts_out(qty, route)
        return price

    def getAmountsIn(self, qty: int, token) -> Wei:
        """ETH to Token trades with an exact output"""
        route = [token_addresses.WETH, token]
        price = self.get_amounts_in(qty, route)
        return price

    def get_price_buy(self, token, decimals):
        """ ETH-token quotation"""
        buy_qty = 1
        buy_qty_nominal = buy_qty*(10**decimals)
        logging.debug(f"get price {buy_qty_nominal} {token} {decimals}")
        price_total = self.getAmountsIn(buy_qty_nominal, token)
        price = price_total/buy_qty_nominal
        logging.debug(f"price {price_total} {price}")        
        return price

    def get_price_sell(self, token, decimals):
        """ ETH-token quotation"""
        sell_qty = 1
        sell_qty_nominal = sell_qty*(10**decimals)
        logging.info(f"get price {sell_qty_nominal} {token} {decimals}")
        price_total = self.getAmountsOut(sell_qty_nominal, token)
        price = price_total/sell_qty_nominal
        logging.info(f"sell price {price_total} {price}")        
        return price        

    def sell_tokens_tx(self, token, amountIn, amountOutMin, token_decimals):
        """
        amountIn	uint	The amount of input tokens to send.
        amountOutMin	uint	The minimum amount of output tokens that must be received for the transaction not to revert.

        #amountOut	uint	The amount of ETH to receive.
        #amountInMax	uint	The maximum amount of input tokens that can be required before the transaction reverts.
        """
        logging.info("sell_tokens_tx")
        recipient = self.myaddr
        route = [token, token_addresses.WETH]
        #uld not identify the intended function with name `swapTokensForExactETH`,
        #  positional argument(s) of type 
        # `(<class 'float'>, <class 'int'>, <class 'list'>, <class 'str'>, <class 'int'>)` and keyword argument(s) of type `{}`.
                
        deadline = self._deadline()
        # import pdb
        # pdb.set_trace()
        logging.info(f" amountIn amountOutMin route recipient deadline => {amountIn} {amountOutMin} {route} {recipient} {deadline}")
        logging.info(f" amountIn amountOutMin  => {amountIn/(10**token_decimals)} {amountOutMin/WETH_FACTOR}")

        #logging.info(f" amountIn amountOutMin => {amountIn/WETH_FACTOR} {amountOutMin/(10**token_decimals)}")
        logging.info(f"create swap tx")
        swaptx = self.router.functions.swapExactTokensForETH(
                amountIn, 
                amountOutMin,
                route,
                recipient,
                deadline,
        )
        logging.info(f"swaptx {swaptx}")
        return swaptx

    def build_and_send_tx(
        self, function: ContractFunction, tx_params: TxParams
    ) -> HexBytes:
        """Build and send a transaction"""

        # logging.info("_build_and_send_tx")        
        # transaction = function.buildTransaction(tx_params)
        # logging.info(f"transaction {transaction}")
        # signed_txn = self.w3.eth.account.sign_transaction(
        #     transaction, private_key=self.privateKey
        # )
        # logging.info(f"signed_txn {signed_txn}")
        #TODO check sufficient funds for gas
        signed_tx = self.build_tx(function, tx_params)
        logging.info(f"signed_tx {signed_tx}")
        
        # TODO: This needs to get more complicated if we want to support replacing a transaction
        # FIXME: This does not play nice if transactions are sent from other places using the same wallet.

        #TODO add timeout
        #Optionally, specify a timeout in seconds. 
        #https://web3py.readthedocs.io/en/stable/web3.eth.html#web3.eth.Eth.waitForTransactionReceipt
        try:
            txidb = self.w3.eth.sendRawTransaction(signed_tx.rawTransaction)
            txid = binascii.hexlify(txidb)
            logging.info(f"txid {txid}")
            receipt = self.w3.eth.getTransaction(txid)
            return receipt
        finally:
            #ValueError: {'code': -32000, 'message': 'insufficient funds for gas * price + value'}
            logging.debug(f"nonce: {tx_params['nonce']}")
            self.last_nonce = Nonce(tx_params["nonce"] + 1)

    def getGas(self):
        logging.info("getGas")
        setGasDynamic = True
        if setGasDynamic:
            logging.info("generateGasPrice")
            gasPrice = self.w3.eth.generateGasPrice()
        else:
            if self.gasPrice:
                logging.info("default gas price")
                gasPrice = self.gasPrice
                logging.info(f"gasPrice {gasPrice}")
            else:
                logging.info(f"gasPrice not set!")
        return gasPrice

    def sell_tokens(self, token, sell_qty, decimals):
        #sell_qty =  sell_qty_nominal*(10**self.TOKEN_DECIMALS)
        logging.info (f"tokens to SELL {sell_qty/(10**decimals)} ({sell_qty})")

        price = self.get_price_sell(token, decimals)
        price_float = price/(10**decimals)
        logging.info(f"> price {price_float} ({price})")
        
        price_usd = self.eth_usd*price_float

        eth_balance = self.get_eth_balance()

        token_balance = self.get_token_balance(token, self.myaddr)        
        token_balance_float = token_balance/(10**decimals)
        value_usd = price_usd*token_balance/(10**decimals)
        logging.info(f"token_balance: {token_balance}  value_usd {value_usd}")

        eth_expected = int(sell_qty*price)
        # eth_required_float = eth_required/WETH_FACTOR
        logging.info(f"token balance: {token_balance_float}")
        logging.info(f"eth_expected: {eth_expected/WETH_FACTOR}")

        slip = int(self.max_slippage * eth_expected)        
        amountOutMin = eth_expected - slip
        logging.info(f"amountOutMin {amountOutMin} {amountOutMin/WETH_FACTOR}")

        #gas=250000
        #gasPrice=185828026070
        #fee=gas*gasPrice
        # >>> fee
        # 46457006517500000

        #Check fee and got enough left for gas
        #Web3.eth.generateGasPrice()
        #https://web3py.readthedocs.io/en/stable/gas_price.html?highlight=gas%20price
        #gasPrice=185828026070
        
        fee=self.gas*gasPrice
        #eth_qty = self.get_eth_token_output_price(output_token, qty)
        logging.info(f"fee {fee}")
        swaptx = self.sell_tokens_tx(token, sell_qty, amountOutMin, decimals)
        #amountIn	uint	The amount of input tokens to send.
        #amountOutMin	uint	The minimum amount of output tokens that must be received for the transaction not to revert.

        #eth_pay = fee #int(57834719710116393/2)
        #txparams = self._get_tx_params(eth_required, self.gas)
        txparams = self.get_tx_params(0, self.gas)
        logging.info(f"txparams: {txparams}")
        
        total_required = fee
        if total_required > eth_balance:
            logging.info(f"not enough balance, required {total_required/WETH_FACTOR}, got {eth_balance/WETH_FACTOR} ")
        else:
            logging.info(f"enough balance ")


        if self.LIVE_RUN:
            logging.info("!!! live mode !!!")
            txidb = self.build_and_send_tx(swaptx, txparams)
            
            txida = binascii.hexlify(txidb)
            txid = '0x' + str(txida.decode("utf-8"))
            logging.info(f"txid {txid}")
            tx = self.w3.eth.getTransaction(txid)
            logging.info(f"tx {tx}")
            gas_price = tx.gasPrice
            gas_used = tx.gasUsed
            gas_price = tx.gasPrice
            gas_used = tx.gasUsed
            #gas_used = self.w3.getTransactionReceipt(receipt).gasUsed
            transaction_cost = gas_price * gas_used
            logging.info(f"gas_price {gas_price} gas_used {gas_used} transaction_cost {transaction_cost}")
        else:
            logging.info("demo mode")
            logging.info(f"swaptx {swaptx}")

    def get_price_buy_float(self, token, decimals):
        p = self.get_price_buy(token, decimals)
        return p/(10**decimals)

    def get_price_sell_float(self, token, decimals):
        p = self.get_price_sell(token, decimals)
        return p/(10**decimals)

    def get_pool_info_pair(self, pair_contract):
        """ETH-TOKEN"""
        token_addr0 = pair_contract.functions.token0().call()
        token_addr1 = pair_contract.functions.token1().call()
        #ETH-TOKEN quotation
        #if token_addr0 == WETH:
        [reserve0,reserve1,blockts] = self.get_reserves(pair_contract)
        reserves_eth = round(reserve0/WETH_FACTOR,1)

        token_info = self.get_token_info(token_addr1)
        token_decimals = int(token_info["decimals"])
        reserves_token = round(reserve1/(10**token_decimals),1)
            
        price = self.get_price_buy(token_addr1, token_decimals)
        price_float = self.get_price_buy_float(token_addr1, token_decimals)
        
        d = {'token_addr0': token_addr0, 'token_addr1': token_addr1, 'reserves_eth': reserves_eth,'reserves_token': reserves_token, \
        'price': price, 'price_float': price_float, 'token_decimals': token_decimals}
        #'target_pair': pair_addr, 
        return d

    def approved_amount(self, token):
        ctr = self.erc20_contract(token)
        approved_amount = ctr.functions.allowance(self.myaddr, uniswap_router_address).call()
        return approved_amount

    def approve(self, token, max_approval):
        """Give an exchange/router max approval of a token."""
        
        #max_approval = self.max_approval_int if not max_approval else max_approval
        logging.info(f"approve")
        contract_addr = self.router_address
        function = self.erc20_contract(token).functions.approve(
            contract_addr, max_approval
        )
        #gas_price = function.estimateGas()
        #logging.info(f"gas_estimate {gas_price}")

        #transaction_hashes = web3.eth.getFilterChanges(web3_filter.filter_id)
        #transactions = [web3.eth.getTransaction(h) for h in transaction_hashes]

        logging.info(f"Approving token: {token}...")
        #txparams = self._get_tx_params(0, self.gas)
        tx_params = self.get_tx_params(0, self.gas)
        gasPrice = self.w3.eth.generateGasPrice()
        fee=self.gas*gasPrice
        logging.info(f"gasPrice {gasPrice}, fee {fee}")

        
        #medium_gas_price_strategy
        logging.info(f"tx_params: {tx_params}")
        signed_txn = self._build_tx(function, tx_params)

        #send tx
        #https://ethereum.stackexchange.com/questions/6002/transaction-status
        try:
            logging.info(f"sendRawTransaction ")
            tx_hash = self.w3.eth.sendRawTransaction(signed_txn.rawTransaction)
            logging.info(f"tx hash {tx_hash.hex()}")
            tx_receipt = self.w3.eth.waitForTransactionReceipt(tx_hash, timeout=120) # , poll_latency=0.1)
            logging.info(f"tx_receipt: {tx_receipt}")
            return receipt
            #{'code': -32000, 'message': 'replacement transaction underpriced'}
        except Exception as e:
            logging.error(f"error submitting tx: {e}")
        finally:
            #ValueError: {'code': -32000, 'message': 'insufficient funds for gas * price + value'}
            logging.debug(f"nonce: {tx_params['nonce']}")
            self.last_nonce = Nonce(tx_params["nonce"] + 1)
        
        #tx = self._build_and_send_tx(function, txparams)
        #print (tx)
        #print (tx.gas)
        #TODO! check gas and sufficient balance
        #self.w3.eth.waitForTransactionReceipt(tx, timeout=6000)

        # Add extra sleep to let tx propogate correctly
        #time.sleep(1)

####################
    def get_gas(self):
        return Wei(250000)

    def _build_tx(self, function, tx_params):
        tx = function.buildTransaction(tx_params)
        # gasPrice = self.w3.eth.generateGasPrice()
        # logging.info(f"gasPrice {gasPrice}")
        # fee=self.gas*gasPrice
        gp = tx['gasPrice']
        total_fee = tx_params['gas']*gp
        total_fee_float = total_fee/WETH_FACTOR
        total_fee_usd = total_fee_float*self.eth_usd
        logging.info(f"transaction {tx}")
        logging.info(f"total_fee {total_fee} {total_fee_float} {total_fee_usd}")
        signed_txn = self.w3.eth.account.sign_transaction(
            tx, private_key=self.privateKey
        )
        return signed_txn