import logging
import requests
import time
from typing import Callable

from core.utils.tx_enum import TxEnum


logging.basicConfig(level=logging.DEBUG,
    format='[BlockchainGateway] %(message)s')


##############################################################################
###                              REQUIRE IPFS                              ###
##############################################################################

def upload(client: object, value: dict) -> str:
    """
    Provided any Python object, store it on IPFS and then upload the hash that
    will be uploaded to the blockchain as a value
    """
    assert TxEnum.KEY.name in value
    assert TxEnum.CONTENT.name in value
    ipfs_hash = content_to_ipfs(client, value)
    return str(ipfs_hash)

def download(client: object, state: list, key: str) -> list:
    """
    Provided an on-chain key, retrieve the value from local state and retrieve
    the Python object from IPFS
    TODO: implement a better way to parse through state list
    """
    relevant_txs = list(
        map(lambda tx: ipfs_to_content(client, tx.get(TxEnum.CONTENT.name)),
        filter(lambda tx: tx.get(TxEnum.KEY.name) == key, state)))
    return relevant_txs

def ipfs_to_content(client: object, ipfs_hash: str) -> object:
    """
    Helper function to retrieve a Python object from an IPFS hash
    """
    return client.get_json(ipfs_hash)

def content_to_ipfs(client: object, content: dict) -> str:
    """
    Helper function to deploy a Python object onto IPFS, returns an IPFS hash
    """
    return client.add_json(content)

##############################################################################
###                                REQUESTS                                ###
##############################################################################

def construct_getter_call(port: int, host: str = '127.0.0.1') -> str:
    return "http://{0}:{1}/state".format(host, port)

def make_getter_call(port: int, host: str = '127.0.0.1') -> object:
    tx_receipt = requests.get(construct_getter_call(port, host))
    tx_receipt.raise_for_status()
    return tx_receipt

def construct_setter_call(port: int, host: str = '127.0.0.1') -> str:
    return "http://{0}:{1}/txs".format(host, port)

def make_setter_call(tx: dict, port: int, host: str = '127.0.0.1') -> object:
    tx_receipt = requests.post(construct_setter_call(port, host), json=tx)
    tx_receipt.raise_for_status()
    return tx_receipt

##############################################################################
###                                 STATE                                  ###
##############################################################################

def get_global_state(port: int, timeout: int) -> object:
    """
    Gets the global state which should be a list of dictionaries
    TODO: perhaps it might be better to offload the retrying to the request method
    """
    timeout = time.time() + timeout
    tx_receipt = None
    while time.time() < timeout:
        try:
            retval = make_getter_call(port).json()
            break
        except (UnboundLocalError, requests.exceptions.ConnectionError) as e:
            logging.info("HTTP GET error, got: {0}".format(e))
            continue
    logging.info("global state: {}".format(retval))
    return retval

def get_diffs(local_state: list, global_state: list) -> list:
    """
    Return list of transactions that are present in `global_state` but not in
    `local_state`
    """
    len_local_state = len(local_state)
    return global_state[len_local_state:]

# TODO: consider merging the two methods below into one

def filter_diffs(local_state: list, global_state_wrapper: object,
                    filter_method: Callable = lambda tx: True) -> list:
    """
    Provided the freshly-downloaded state, call a handler on each transaction
    that was not already present in our own state and return the new state
    """
    new_state = get_diffs(local_state,
                            global_state_wrapper.get(TxEnum.MESSAGES.name, {}))
    return list(filter(filter_method, new_state))

def update_diffs(local_state: list, global_state_wrapper: object, 
                    handler: Callable = lambda tx: tx) -> list:
    """
    Provided the freshly-downloaded state, call a handler on each transaction
    that was not already present in our own state and return the new state
    """
    new_state = get_diffs(local_state,
                            global_state_wrapper.get(TxEnum.MESSAGES.name, {}))
    return list(map(handler, new_state))

def do_nothing(payload: dict) -> None:
    """
    Do nothing.
    """
    pass
