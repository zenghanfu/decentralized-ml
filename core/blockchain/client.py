import base58
import json
import logging
import os
import requests

import ipfsapi

from core.configuration import ConfigurationManager
from core.utils.keras import serialize_weights, deserialize_weights
from custom.keras import model_from_serialized, get_optimizer


logging.basicConfig(level=logging.DEBUG,
    format='[Blockchain Client] %(message)s')


class Client(object):
    '''
    The blockchain client exposes `setter` and `getter` in order to interact
    with the blockchain.
    '''
    # TODO: enum-like casting for multiple datatypes, if needed
    # OBJ_TYPES = {str: Client._cast_str, dict: Client._cast_dict}

    with open("./core/blockchain/blockchain_config.json", "r") as read_file:
        CONFIG = json.load(read_file)

    def __init__(self, config_manager):
        '''
        TODO: Decide if `kv` is needed
        TODO: Decide if one client instantiated per model or not
        TODO: Refactor dependencies
        '''
        config = config_manager.get_config()
        self.kv = {}
        self.client_id = config.get("BLOCKCHAIN", "client_id")
        self.checksum = "lgtm"
        self.client = None
        try:
            self.client = ipfsapi.connect(config.get("BLOCKCHAIN", "host"),
                                            config.get("BLOCKCHAIN", "port"))
        except Exception as e:
            logging.info("IPFS daemon not started, got: {0}".format(e))

    ##########################################################################
    ###                            API SECTION                             ###
    ##########################################################################

    def setter(self, key: str, value: object) -> str:
        '''
        Provided a key and a JSON/np.array object, upload the object to
        IPFS and then store the hash as the value on the blockchain. The key
        should be a backward reference to a prior tx
        '''
        on_chain_addr = self._upload(value)
        try:
            tx_receipt = requests.post("http://localhost:{0}/txs".format(self.port),
                                        "{'{0}': '{1}'}".format(key, value))
            tx_receipt.raise_for_status()
        except Exception as e:
            logging.info("HTTP Request error, got: {0}".format(e))
        return tx_receipt

    def getter(self, key: str) -> object:
        '''
        Provided a key, get the IPFS hash from the blockchain and download
        the object from IPFS
        TODO: blockchain getter API required
        '''
        # TODO: add error checking to async call
        on_chain_addr = "some http call with key"
        retval = self._download(on_chain_addr)
        return retval

    def _upload_local(self, key: str, obj: object) -> None:
        '''
        Test method, DO NOT USE
        '''
        addr = self.client.add(obj)
        self.kv[key] = addr

    def _download_local(self, key: str) -> object:
        '''
        Test method, DO NOT USE
        '''
        addr = self.kv[key]
        return self.client.get(addr)

    def _upload(self, obj: object) -> str:
        '''
        Provided any Python object, store it on IPFS and then upload
        the hash to the blockchain
        '''
        ipfs_hash = self._content_to_ipfs(obj)
        byte_addr = self._ipfs_to_blockchain(ipfs_hash)
        return addr

    def _download(self, byte_addr: bytes) -> object:
        '''
        Provided an on-chain content address, retrieve the Python
        object from IPFS
        TODO: blockchain getter API required
        '''
        ipfs_hash = self._blockchain_to_ipfs(byte_addr)
        content = self._ipfs_to_content(ipfs_hash)
        return content

    def _ipfs_to_content(self, ipfs_hash: str) -> object:
        '''
        Helper function to retrieve a Python object from an IPFS hash
        '''
        return self.client.get(addr)

    def _content_to_ipfs(self, obj: object) -> str:
        '''
        Helper function to deploy a Python object onto IPFS, 
        returns an IPFS hash
        '''
        return self.client.add(obj)

    def _ipfs_to_blockchain(self, ipfs_hash: str) -> bytes:
        '''
        Helper function to convert IPFS hashes to on-chain content addresses
        '''
        return base58.b58encode(b'\x12 ' + ipfs_hash)

    def _blockchain_to_ipfs(self, byte_addr: bytes) -> str:
        '''
        Helper function to convert on-chain content addresses to IPFS hashes
        '''
        return base58.b58decode(byte_addr)[2:]

    def _cast_str(self, input: str):
        '''
        Helper function to cast string inputs to desired type
        '''
        pass

    def _cast_dict(self, input: dict):
        '''
        Helper function to cast dict inputs to desired type
        '''
        pass

    ##########################################################################
    ###                         DEVELOPER SECTION                          ###
    ##########################################################################

    def broadcast_decentralized_learning(self, model_config: object)-> str:
        '''
        Upload a model config and weights to the blockchain
        '''
        key = self.construct_header(model_config)
        tx_receipt = self.setter(key, key)
        return tx_receipt

    def construct_value(self, model_config: object) -> str:
        value = {
            "config": model_config
        }
        retval = str(header)
        return retval

    def broadcast_terminate(self) -> None:
        '''
        Terminates decentralized training
        '''
        key = self.construct_header(model_config)
        tx_receipt = self.setter(key, None)
        return tx_receipt

    def handle_decentralized_learning(self, key) -> None:
        '''
        Return weights after training terminates
        '''
        final_weights = self.getter(key)
        return final_weights

    ##########################################################################
    ###                          PROVIDER SECTION                          ###
    ##########################################################################

