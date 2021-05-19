import requests
import json
import pymongo
import os
import logging
import toml
import time

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

AddressLike = Union[Address, ChecksumAddress, ENS]


def str_to_addr(s: str) -> AddressLike:
    if s.startswith("0x"):
        return Address(bytes.fromhex(s[2:]))
    elif s.endswith(".ens"):
        return ENS(s)
    else:
        raise Exception("Could't convert string {s} to AddressLike")


def addr_to_str(a: AddressLike) -> str:
    if isinstance(a, bytes):
        # Address or ChecksumAddress
        addr: str = Web3.toChecksumAddress("0x" + bytes(a).hex())
        return addr
    elif isinstance(a, str):
        if a.endswith(".ens"):
            # Address is ENS
            raise Exception("ENS not supported for this operation")
        elif a.startswith("0x"):
            addr = Web3.toChecksumAddress(a)
            return addr
        else:
            raise InvalidToken(a)

def load_abi(name: str) -> str:
    path = f"{os.path.dirname(os.path.abspath(__file__))}/abi/"
    with open(os.path.abspath(path + f"{name}.abi")) as f:
        abi: str = json.load(f)
    return abi

def load_abi_json(name: str) -> str:
    path = f"{os.path.dirname(os.path.abspath(__file__))}/abi/"
    with open(os.path.abspath(path + f"{name}.json")) as f:
        abi: str = json.load(f)["abi"]
    return abi