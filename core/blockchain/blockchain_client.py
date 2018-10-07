import base58
import json
import logging
import os
import requests
import asyncio

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

    # TODO: deal with config
    # with open("./core/blockchain/blockchain_config.json", "r") as read_file:
    #     CONFIG = json.load(read_file)

    def __init__(self, config_manager):
        '''
        TODO: Refactor dependencies
        '''
<<<<<<< HEAD
        config = config_manager.get_config()
        self.state = {}
        self.host = config.get("BLOCKCHAIN", "host")
        self.port = config.get("BLOCKCHAIN", "port")
=======
        self.config = config_manager.get_config()
        self.kv = {}
        self.client_id = config.get("BLOCKCHAIN", "client_id")
        self.checksum = "lgtm"
>>>>>>> cd8cc7bb6c0b0d4809f35ac4a61edef07be0e80d
        self.client = None
        self.state = [{}]
        try:
<<<<<<< HEAD
            self.client = ipfsapi.connect(self.host, self.port)
=======
            self.client = ipfsapi.connect(self.config.get("BLOCKCHAIN", "host"),
                                            self.config.get("BLOCKCHAIN", "port"))
>>>>>>> cd8cc7bb6c0b0d4809f35ac4a61edef07be0e80d
        except Exception as e:
            logging.info("IPFS daemon not started, got: {0}".format(e))
    
    async def start_listening(self, event_filter, handler, poll_interval=5):
        while True:
            filtered_diffs = self.get_state_diffs(event_filter, handler)
            if filtered_diffs:
                return filtered_diffs
            await asyncio.sleep(poll_interval)

    def filter_set(self, event_filter, handler):
        asyncio.set_event_loop(asyncio.new_event_loop())
        loop = asyncio.get_event_loop()
        try:
            loop.run_until_complete(self.start_listening(
                event_filter, handler
            ))
            # inter = loop.run_until_complete(
                # self.start_listening(event_filter, handler))
            # check = handler(inter)
        finally:
            loop.close()
        return check

    def get_state_diffs(self, event_filter, handler):
        """
        Gets state, then finds diffs, then sets state of blockchain.
        """
        new_state = self.get_state()
        state_diffs = self.get_diffs(self.state, new_state)
        filtered_diffs = [handler(txn) if event_filter(txn) for txn in state_diffs]
        return filtered_diffs

    def get_state(self):
        """
        Read state of blockchain
        """
        newState = requests.get("http://localhost:{0}/state".format(self.config.port))
        return newState
        # diffs = self.get_diffs(self.state, newState)
        # self.state = newState
        # return diffs

    def get_diffs(self, oldState: str, newState: str) -> str:
        """
        Iterate through oldState and newState to see any differences
        Take action based on the differences
        """
        txnDiffs = [txn for txn in newState if txn not in oldState]
        return txnDiffs
        # for txn in txnDiffs:
        #     for key in txn.keys():
        #         if not txn.get(key):
        #             self.handle_none(txn)
        #         elif key == txn.get(key, None):
        #             self.handle_equals(txn)
        #         elif key != txn.get(key,None) and txn.get(key,None) is not None:
        #             self.handle_diff(txn)

    # def handle_none(self, txn):
    #     """
    #     Does nothing, but anything which inherits must override.
    #     """
    #     pass

    # def handle_equals(self, txn):
    #     """
    #     Does nothing, but anything which inherits must override.
    #     """
    #     pass

    # def handle_diff(self, txn):
    #     """
    #     Does nothing, but anything which inherits must override.
    #     """
    #     pass

    def handler(self):
        '''
        Called on new transactions
        '''
        pass

    def update_state(self, new_state: [dict]) -> None:
        '''
        Given the freshly-downloaded state, call a handler on each transaction
        that was not already present in our own state
        '''
        len_new_state = len(new_state)
        len_state = len(self.state)
        for i in range(len_new_state - len_state, len_new_state):
            self.handler(new_state[i])
            self.state.append(new_state[i])

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
        return tx_receipt.text

    def getter(self, key: str) -> object:
        '''
        Provided a key, get the IPFS hash from the blockchain and download
        the object from IPFS
        '''
        try:
            tx_receipt = requests.get("http://localhost:{0}/state".format(self.port))
            tx_receipt.raise_for_status()
        except Exception as e:
            logging.info("HTTP Request error, got: {0}".format(e))
        self.state = tx_receipt.json()
        retval = self._download(on_chain_addr)
        return retval

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

class Developer(BlockchainClient):
    '''
    The developer is able to initiate and terminate training on the blockchain.
    '''

    def __init__(self, config_manager):
        super().__init__(config_manager)

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

class Listener(BlockchainClient):
    from core.EventTypes import ListenerEventTypes

    CALLBACKS = {
        ListenerEventTypes.WEIGHTS.name: broadcast_new_weights, 
        ListenerEventTypes.UNDEFINED.name: do_nothing,
    }

    def __init__(self, config_manager, comm_mgr):
        super().__init__(config_manager)
        self.comm_mgr = comm_mgr
        self.comm_mgr.configure_listener(self)

    def handle_decentralized_learning(self, key: str, value: str):
        '''
        Downloads parameters of decentralized_learning() query and 
        saves them appropriately to in-memory datastore
        This callback will be triggered by the Listener if it finds the 
        method signature it's looking for.
        The parameters (model weights, model config) will be downloaded 
        and put into the optimizer initially. So the optimizer knows this info.
        '''
        args = self.getter(key, value)
        self.comm_mgr.inform("new_session", args)

    def handle_new_weights(self, key: str, value: str):
        '''
        handle_new_weights() method downloads weights and does smth with it
        This callback is triggered by the Listener when it sees new weights 
        intended for its node ID. Downloads the weights, and gives them to the
        comm. mgr which gives them to the relevant optimizer 
        -which should do the moving average.
        '''
        weights = self.getter(key, value)
        #TODO: Put into in-memory datastore.
        self.comm_mgr.inform("new_weights", weights)

    def handle_terminate(self):
        self.comm_mgr.inform("TERMINATE", None)

    def listen_decentralized_learning(self):
        '''
        Polls blockchain for node ID in decentralized_learning() method signature
        decentralized_learning(...<node_ids>...) method signature will be the key 
        on the blockchain; listener should look for this, and if the method signature 
        contains its node id, it will trigger a callback
        '''
        self.filter_set(lambda x: x[0] == x.get(x[0]), self.handle_decentralized_learning)

    def broadcast_new_weights(self, payload: dict):
        '''
        broadcast_new_weights() method with all relevant parameters
        should populate the key of new_weights with all of the nodes for which 
        these new weights are relevant. value should be IPFS hash.
        '''
        key = payload.get("key", None)
        weights = payload.get("weights", None)
        self.setter(key, weights)

    def listen_new_weights(self):
        '''
        Polls blockchain for node ID in new_weights() method signature
        new_weights(...<node_ids>...) method signature will be the key on the blockchain; 
        listener should look for this, and if the method signature contains its node id, 
        it will trigger a callback
        '''
        self.filter_set(lambda x: x[0] != x.get(x[0]), self.handle_new_weights)

    def listen_terminate(self):
        """
        Polls blockchain to see whether to terminate
        """
        self.filter_set(lambda x: x.get(x[0]) is None, self.handle_terminate)

    def inform(self, event_type, payload):
        '''
        Method called by other modules to inform the Listener about
        events that are going on in the service.
        These payloads are relayed to the blockchain (right now the only
        one, in the future, the one corresponding to the session_id passed),
        based on some internal logic of the Listener.
        For example: A runner could inform the Communication Manager that the
        node is done training a particular model, to which the Optimizer could
        decide it's time to communicate the new weights to the network.
        If the Optimizer says yes, then the Communication Manager should
        relay this info to the Listener, and the Listener uploads weights.
        '''
        self._parse_and_run_callback(event_type, payload)

    def _parse_and_run_callback(self, event_type, payload):
        '''
        Parses an actionable_event and runs the
        corresponding "callback" based on the event type, which could be to do
        nothing.
        The way this method parses an event is by stripping out the event type
        and sending the raw payload to the callback function, which will handle
        everything from there on.
        '''
        callback = EVENT_TYPE_CALLBACKS.get(event_type, ListenerEventTypes.UNDEFINED.value)
        callback(payload)
