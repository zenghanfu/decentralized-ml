import asyncio
import logging
import ipfsapi
import time
from typing import Callable

from core.blockchain.blockchain_utils   import filter_diffs
from core.blockchain.blockchain_utils   import get_global_state, ipfs_to_content
from core.utils.enums                   import RawEventTypes, MessageEventTypes
from core.blockchain.tx_utils           import TxEnum


logging.basicConfig(level=logging.DEBUG,
    format='[BlockchainGateway] %(message)s')


class BlockchainGateway(object):
    """
    Blockchain Gateway 

    The blockchain gateway listens to the blockchain and notifies the appropriate classes
    inside the Unix Service when there is relevant information ready for them. Follows
    an event-driven programming paradigm using a series of asyncio loops for listening.

    In order for this to work, the following must be running:
        IPFS Daemon: `ipfs daemon`
        The lotion app: `node app_trivial.js` from dagora-chain
    For more specific instructions check travis.yaml to see how travis does it.
    """

    def __init__(self):
        """
        Initialize state to an empty list. Everything else is left to configure().
        """
        self.state = []

    def configure(self, config_manager: object, communication_manager: object):
        """
        Add communication_manager.
        Set up IPFS client via config_manager.
        """
        self.communication_manager = communication_manager
        config = config_manager.get_config()
        self.host = config.get("BLOCKCHAIN", "host")
        self.ipfs_port = config.getint("BLOCKCHAIN", "ipfs_port")
        self.port = config.getint("BLOCKCHAIN", "http_port")
        self.timeout = config.getint("BLOCKCHAIN", "timeout")
        self.client = None
        # try:
        self.client = ipfsapi.connect(self.host, self.ipfs_port)
        # except Exception as e:
        #     logging.info("IPFS daemon not started, got: {0}".format(e))

    ##########################################################################
    ###                          PROVIDER SECTION                          ###
    ##########################################################################

    def _update_local_state(self, global_state_wrapper):
        """
        Helper function to update the local state with freshly downloaded global state.
        """
        self.state = global_state_wrapper.get(TxEnum.MESSAGES.name, {})

    async def _start_listening(self, event_filter: Callable,
                                timeout=25) -> list:
        """
        Starts an indefinite loop that listens for a specific event to occur.
        Called in `_filter_set`. Filters are some condition that must be
        fulfilled on a per tx basis
        `poll_interval` specifies the number of seconds to stall before each
        poll
        """
        timeout = time.time() + timeout
        while time.time() < timeout:
            global_state_wrapper = get_global_state(self.host, self.port, self.timeout)
            filtered_diffs = filter_diffs(global_state_wrapper, self.state, event_filter)
            self._update_local_state(global_state_wrapper)
            if filtered_diffs:
                return filtered_diffs
            await asyncio.sleep(self.timeout)

    def _filter_set(self, event_filter: Callable, handler: Callable) -> list:
        """
        Calls async method `_start_listening` and called by various listening
        methods
        """
        asyncio.set_event_loop(asyncio.new_event_loop())
        loop = asyncio.get_event_loop()
        try:
            filtered_diffs = loop.run_until_complete(
                self._start_listening(event_filter))
            check = list(map(handler, filtered_diffs))
        except TypeError as e:
            logging.info("Listening terminated: {}".format(e))
        finally:
            loop.close()

    def _handle_decentralized_learning_trainer(self, manual) -> Callable:
        """
        This callback will be triggered by the Listener if it finds the 
        method signature it's looking for.
        The parameters (model weights, model config) will be downloaded 
        and put into the optimizer initially. So the optimizer knows this info.
        """
        def handler(tx: dict) -> None:
            # Calls _listen_new_weights
            logging.info("handling decentralized learning... {}".format(tx))
            assert TxEnum.KEY.name in tx
            key = tx.get(TxEnum.KEY.name)
            value = tx.get(TxEnum.CONTENT.name)
            # args = {TxEnum.KEY.name: key, TxEnum.CONTENT.name: ipfs_to_content(self.client, value)}
            self.communication_manager.inform(RawEventTypes.NEW_SESSION.name, ipfs_to_content(self.client, value))
            self._listen_new_weights()
        def handler_manual(tx: dict) -> None:
            # Doesn't call _listen_new_weights
            logging.info("handling decentralized learning... {}".format(tx))
            assert TxEnum.KEY.name in tx
            key = tx.get(TxEnum.KEY.name)
            value = tx.get(TxEnum.CONTENT.name)
            self.communication_manager.inform(RawEventTypes.NEW_SESSION.name, ipfs_to_content(self.client, value))
        return handler_manual if manual else handler

    def _handle_new_weights(self, manual) -> Callable:
        """
        _handle_new_weights() method downloads weights and does something with
        it. This callback is triggered by the Listener when it sees new weights 
        intended for its node ID. Downloads the weights, and gives them to the
        comm. mgr which gives them to the relevant optimizer 
        -which should do the moving average.
        """
        def handler(tx: dict) -> None:
            # Calls itself again
            key = tx.get(TxEnum.KEY.name)
            value = tx.get(TxEnum.CONTENT.name)
            args = {TxEnum.KEY.name: MessageEventTypes.NEW_WEIGHTS.name, 
                    TxEnum.CONTENT.name: ipfs_to_content(self.client, value)}
            # TODO: Put into in-memory datastore.
            self.communication_manager.inform(
                RawEventTypes.NEW_INFO.name,args)
            self._listen_new_weights()
        def handler_manual(tx: dict) -> None:
            # Doesn't call itself again
            key = tx.get(TxEnum.KEY.name)
            value = tx.get(TxEnum.CONTENT.name)
            args = {TxEnum.KEY.name: MessageEventTypes.NEW_WEIGHTS.name, 
                    TxEnum.CONTENT.name: ipfs_to_content(self.client, value)}
            # TODO: Put into in-memory datastore.
            self.communication_manager.inform(
                RawEventTypes.NEW_INFO.name,args)
        return handler_manual if manual else handler

    def _handle_terminate(self) -> None:
        self.communication_manager.inform(
            MessageEventTypes.TERMINATE.name, None)

    def listen_decentralized_learning(self, manual=False) -> list:
        """
        Polls blockchain for node ID in decentralized_learning() method
        signature decentralized_learning(...<node_ids>...) method signature
        will be the key on the blockchain; listener should look for this, and
        if the method signature contains its node id, it will trigger a
        callback
        """
        def filter(tx: dict) -> bool:
            return tx.get(TxEnum.KEY.name) == tx.get(TxEnum.CONTENT.name)
        return self._filter_set(filter,
                                self._handle_decentralized_learning_trainer(manual))

    def _listen_new_weights(self, manual=False) -> None:
        """
        Polls blockchain for node ID in new_weights() method signature
        new_weights(...<node_ids>...) method signature will be the key on the
        blockchain; listener should look for this, and if the method signature
        contains its node id, it will trigger a callback
        """
        logging.info("Listening for new weights...")
        def filter(tx: dict) -> bool:
            return tx.get(TxEnum.KEY.name) != tx.get(TxEnum.CONTENT.name)
        self._filter_set(filter, self._handle_new_weights(manual))

    def _listen_terminate(self) -> None:
        """
        Polls blockchain to see whether to terminate
        """
        def filter(tx: dict) -> bool:
            return tx.get(TxEnum.CONTENT.name) is None
        self._filter_set(filter, self._handle_terminate)
    