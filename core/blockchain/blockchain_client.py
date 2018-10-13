import asyncio
import base58
import json
import logging
import os
import requests
import time

import ipfsapi

from core.utils.event_types import ListenerEventTypes

# from core.configuration import ConfigurationManager

# TODO: Fix logging for this file
logging.basicConfig(level=logging.DEBUG,
    format='[Blockchain Client] %(message)s')


class BlockchainGateway(object):
    """
    The blockchain client exposes `setter` and `getter` in order to interact
    with the blockchain.

    In order for this to work, the following must be running:
        IPFS Daemon: `ipfs deamon`
        The lotion app: `node app.js` from the application root directory
    """
    # TODO: enum-like casting for multiple datatypes, if needed
    # OBJ_TYPES = {str: Client._cast_str, dict: Client._cast_dict}

    def __init__(self, config_manager, comm_mgr):
        """
        TODO: Refactor dependencies
        TODO: Figure out core dependency issue
        TODO: deal with config
        """
        # TODO: `comm_mgr` is only used in a subset of methods, consider separating
        self.comm_mgr = comm_mgr
        self.comm_mgr.configure_listener(self)

        config = config_manager.get_config() if config_manager else {}
        self.state = []
        self.host = config.get("BLOCKCHAIN", "host")
        self.ipfs_port = config.get("BLOCKCHAIN", "ipfs_port")
        self.port = config.get("BLOCKCHAIN", "http_port")
        self.host = '127.0.0.1'
        self.ipfs_port = 5001
        self.port = 3000
        self.client = None
        try:
            self.client = ipfsapi.connect(self.host, self.ipfs_port)
        except Exception as e:
            logging.info("IPFS daemon not started, got: {0}".format(e))

        self.CALLBACKS = {
            ListenerEventTypes.NEW_WEIGHTS.name: self.broadcast_new_weights, 
            ListenerEventTypes.NOTHING.name: self._do_nothing,
        }
    ##########################################################################
    ###                            API SECTION                             ###
    ##########################################################################

    def _do_nothing(self, payload):
        """
        Do nothing.
        """
        pass

    def get_global_state(self):
        """
        Gets the global state with should be a list of dictionaries
        """
        timeout = time.time() + 5
        while time.time() < timeout:
            try:
                tx_receipt = requests.get("http://localhost:{0}/state".format(self.port))
                tx_receipt.raise_for_status()
            except (UnboundLocalError, requests.exceptions.ConnectionError) as e:
                logging.info("HTTP Request error, got: {0}".format(e))
                continue
            if tx_receipt:
                break
        logging.info("global state:{}".format(tx_receipt.json()))
        return tx_receipt.json()

    def handler(self):
        pass

    def update_state(self, new_state_wrapper: [dict]) -> None:
        """
        Given the freshly-downloaded state, call a handler on each transaction
        that was not already present in our own state
        """
        # TODO: Set self.handler, else this method errors
        new_state = dict(new_state_wrapper)['messages']
        len_state = len(self.state)
        for i in new_state[len_state:]:
            new_item = self.handler(i)
            self.state.append(new_item)

    def setter(self, key: str, value: object, flag: bool = False) -> str:
        """
        Provided a key and a JSON/np.array object, upload the object to
        IPFS and then store the hash as the value on the blockchain. The key
        should be a backward reference to a prior tx
        """
        logging.info("Posting to blockchain...")
        on_chain_value = self._upload(value) if value else None
        tx = {'key': key, 'content': on_chain_value} if not flag else {'key': on_chain_value, 'content': on_chain_value}
        try:
            tx_receipt = requests.post("http://localhost:{0}/txs".format(self.port),
                                        json=tx)
            tx_receipt.raise_for_status()
        except Exception as e:
            logging.info("HTTP Request error, got: {0}".format(e))
        return tx_receipt.text

    def getter(self, key: str) -> object:
        """
        First, get the latest state. Next, provided a key, get the IPFS hash
        from the blockchain and download the object from IPFS
        """
        logging.info("Getting latest state from blockchain...")
        retval = self._download(key)
        return retval

    def _upload(self, obj: object) -> str:
        """
        Provided any Python object, store it on IPFS and then upload
        the hash that will be uploaded to the blockchain as a value
        """
        ipfs_hash = self._content_to_ipfs(obj)
        return str(ipfs_hash)

    def _download(self, key: str) -> object:
        """
        Provided an on-chain key, retrieve the value from local state and
        retrieve the Python object from IPFS
        TODO: implement a better way to parse through state list
        TODO: user needs to get from IPFS addresses for now
        """
        relevant_txs = [self._ipfs_to_content(tx['content'])
                            for tx in self.state if (tx['key'] == key)]
        return relevant_txs

    def _ipfs_to_content(self, ipfs_hash: str) -> object:
        """
        Helper function to retrieve a Python object from an IPFS hash
        """
        logging.info("ipfs hash: {}".format(ipfs_hash))
        return self.client.get_json(ipfs_hash)

    def _content_to_ipfs(self, obj: object) -> str:
        """
        Helper function to deploy a Python object onto IPFS, 
        returns an IPFS hash
        """
        return self.client.add_json(obj)

    ##########################################################################
    ###                         DEVELOPER SECTION                          ###
    ##########################################################################

    def broadcast_decentralized_learning(self, model_config: object)-> str:
        """
        Upload a model config and weights to the blockchain
        """
        tx_receipt = self.setter(None, model_config, True)
        return tx_receipt

    def broadcast_terminate(self, key: str) -> None:
        """
        Terminates decentralized training
        TODO: check if training even started
        """
        tx_receipt = self.setter(key, None)
        return tx_receipt

    def handle_decentralized_learning_owner(self, model_config: object) -> None:
        """
        Return weights after training terminates
        TODO: add condition to check if training for specific model has terminated
        """
        final_weights = self.getter(header)
        return final_weights

    ##########################################################################
    ###                          PROVIDER SECTION                          ###
    ##########################################################################

    async def start_listening(self, event_filter, handler, poll_interval=5):
        """
        Starts an indefinite loop that listens for a specific event to occur.
        Called in `filter_set`. Filters are some condition that must be fulfilled
        on a per tx basis
        `poll_interval` specifies the number of seconds to stall before each poll
        """
        while True:
            logging.info("start_listening_loop")
            filtered_diffs = self.get_state_diffs(event_filter)
            if filtered_diffs:
                return filtered_diffs
            await asyncio.sleep(poll_interval)

    def filter_set(self, event_filter, handler):
        """
        Calls async method `start_listening` and called by various listening
        methods
        """
        asyncio.set_event_loop(asyncio.new_event_loop())
        loop = asyncio.get_event_loop()
        try:
            filtered_diffs = loop.run_until_complete(
                self.start_listening(event_filter, handler))
            check = [handler(diff) for diff in filtered_diffs]
        finally:
            loop.close()
        return check

    def get_diffs(self, oldState: str, newState: str) -> str:
        """
        Iterate through oldState and newState to see any differences
        Take action based on the differences
        """
        txnDiffs = [txn for txn in newState.get('messages') if txn not in oldState]
        return txnDiffs

    def get_state_diffs(self, event_filter):
        """
        Gets state, then finds diffs, then sets state of blockchain.
        """
        new_state = self.get_global_state()
        state_diffs = self.get_diffs(self.state, new_state)
        filtered_diffs = [txn for txn in state_diffs if event_filter(txn)]
        logging.info("filtered diffs:{}".format(filtered_diffs))
        # Comment out below line for testing else you'll have to actually push txns
        # to test which is pretty annoying. Without below line, this class
        # does not update its own state!!!
        # self.update_state(new_state)
        return filtered_diffs

    def handle_decentralized_learning_trainer(self, tx: dict) -> None:
        """
        Downloads parameters of decentralized_learning() query and 
        saves them appropriately to in-memory datastore
        This callback will be triggered by the Listener if it finds the 
        method signature it's looking for.
        The parameters (model weights, model config) will be downloaded 
        and put into the optimizer initially. So the optimizer knows this info.
        """
        logging.info("handling decentralized learning...{}".format(txn))
        key = txn.get('key')
        value = txn.get('content')
        args = {'key': key, 'content': self._ipfs_to_content(value)}
        self.comm_mgr.inform("new_session", args)

    def handle_new_weights(self, key: str, value: str):
        """
        handle_new_weights() method downloads weights and does something with it
        This callback is triggered by the Listener when it sees new weights 
        intended for its node ID. Downloads the weights, and gives them to the
        comm. mgr which gives them to the relevant optimizer 
        -which should do the moving average.
        """
        weights = self.getter(key, value)
        # TODO: Put into in-memory datastore.
        self.comm_mgr.inform("new_weights", weights)

    def handle_terminate(self):
        self.comm_mgr.inform("TERMINATE", None)

    def listen_decentralized_learning(self):
        """
        Polls blockchain for node ID in decentralized_learning() method signature
        decentralized_learning(...<node_ids>...) method signature will be the key 
        on the blockchain; listener should look for this, and if the method signature 
        contains its node id, it will trigger a callback
        """
        def filter(txn):
            logging.info("txn: {}".format(txn))
            return txn.get('key') == txn.get('content')
            # return list(txn.keys())[0] == txn.get(list(txn.keys())[0])
        self.filter_set(filter, self.handle_decentralized_learning_trainer)

    def broadcast_new_weights(self, payload: dict):
        """
        broadcast_new_weights() method with all relevant parameters
        should populate the key of new_weights with all of the nodes for which 
        these new weights are relevant. value should be IPFS hash.
        """
        key = payload.get("key", None)
        weights = payload.get("weights", None)
        tx_receipt = self.setter(key, weights)
        return tx_receipt

    def listen_new_weights(self):
        """
        Polls blockchain for node ID in new_weights() method signature
        new_weights(...<node_ids>...) method signature will be the key on the blockchain; 
        listener should look for this, and if the method signature contains its node id, 
        it will trigger a callback
        """
        def filter(txn):
            logging.info("txn: {}".format(txn))
            return txn.get('key') != txn.get('content')
        self.filter_set(lambda x: x[0] != x.get(x[0]), self.handle_new_weights)

    def listen_terminate(self):
        """
        Polls blockchain to see whether to terminate
        """
        def filter(txn):
            logging.info("txn: {}".format(txn))
            return txn.get('content') is None
        self.filter_set(filter, self.handle_terminate)

    def inform(self, event_type, payload):
        """
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
        """
        self._parse_and_run_callback(event_type, payload)

    def _parse_and_run_callback(self, event_type, payload):
        """
        Parses an actionable_event and runs the
        corresponding "callback" based on the event type, which could be to do
        nothing.
        The way this method parses an event is by stripping out the event type
        and sending the raw payload to the callback function, which will handle
        everything from there on.
        """
        logging.info("payload:{}".format(payload))
        callback = self.CALLBACKS.get(event_type, ListenerEventTypes.NOTHING.value)
        callback(payload)
