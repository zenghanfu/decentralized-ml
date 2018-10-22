import asyncio

import ipfsapi

from core.blockchain.blockchain_utils import *
from core.utils.event_types import *


logging.basicConfig(level=logging.DEBUG,
    format='[BlockchainGateway] %(message)s')


class BlockchainGateway(object):
    """
    Blockchain Gateway 

    The blockchain gateway exposes `setter` and `getter` in order to interact
    with the blockchain.

    In order for this to work, the following must be running:
        IPFS Daemon: `ipfs daemon`
        The lotion app: `node app_trivial.js` from the application root directory

    """

    def __init__(self, config_manager, communication_manager):
        """
        TODO: Refactor dependencies
        TODO: deal with config
        TODO: `communication_manager` is only used in a subset of methods,
        consider separating
        """
        self.communication_manager = communication_manager
        # TODO: We will do this once the Communication Manager is done.
        # self.communication_manager.configure_listener(self)

        config = config_manager.get_config() # TODO: remove this inline comment; if config_manager else {}
        self.state = []
        self.host = config.get("BLOCKCHAIN", "host")
        self.ipfs_port = config.getint("BLOCKCHAIN", "ipfs_port")
        self.port = config.getint("BLOCKCHAIN", "http_port")
        self.timeout = config.getint("BLOCKCHAIN", "timeout")
        self.client = None
        try:
            self.client = ipfsapi.connect(self.host, self.ipfs_port)
        except Exception as e:
            logging.info("IPFS daemon not started, got: {0}".format(e))

    ##########################################################################
    ###                         DEVELOPER SECTION                          ###
    ##########################################################################

    def broadcast_decentralized_learning(self, model_config: object)-> str:
        """
        Upload a model config and weights to the blockchain
        """
        tx_receipt = setter(None, model_config, self.client, self.port)
        return tx_receipt

    def broadcast_terminate(self, key: str) -> str:
        """
        Terminates decentralized training
        TODO: check if training even started
        """
        tx_receipt = setter(key, None, self.client, self.port)
        return tx_receipt

    def handle_decentralized_learning_owner(self, model_config: object) -> None:
        """
        Return weights after training terminates
        TODO: add condition to check if training for specific model terminated
        """
        final_weights = getter(self.client, model_config, self.state, self.port, self.timeout)
        return final_weights

    ##########################################################################
    ###                          PROVIDER SECTION                          ###
    ##########################################################################

    async def start_listening(self, event_filter, handler):
        """
        Starts an indefinite loop that listens for a specific event to occur.
        Called in `filter_set`. Filters are some condition that must be
        fulfilled on a per tx basis
        `poll_interval` specifies the number of seconds to stall before each
        poll
        """
        while True:
            global_state_wrapper = get_global_state(self.port, self.host, self.timeout)
            filtered_diffs = filter_diffs(self.state, global_state_wrapper, event_filter)
            if filtered_diffs:
                return filtered_diffs
            await asyncio.sleep(self.timeout)

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
            check = list(map(event_filter, filtered_diffs))
        finally:
            loop.close()
        return check

    def handle_decentralized_learning_trainer(self, tx: dict) -> None:
        """
        This callback will be triggered by the Listener if it finds the 
        method signature it's looking for.
        The parameters (model weights, model config) will be downloaded 
        and put into the optimizer initially. So the optimizer knows this info.
        """
        logging.info("handling decentralized learning... {}".format(tx))
        assert TxEnum.KEY.name in tx
        key = tx.get(TxEnum.KEY.name)
        value = tx.get('content')
        args = {TxEnum.KEY.name: key, TxEnum.CONTENT.name: ipfs_to_content(self.client, value)}
        self.communication_manager.inform(RawEventTypes.NEW_SESSION.name, args)
        self.listen_new_weights()

    def handle_new_weights(self, tx: dict):
        """
        handle_new_weights() method downloads weights and does something with
        it. This callback is triggered by the Listener when it sees new weights 
        intended for its node ID. Downloads the weights, and gives them to the
        comm. mgr which gives them to the relevant optimizer 
        -which should do the moving average.
        """
        # TODO: Upon CommMgr PR being merged, update this with the appropriate args
        logging.info("handling new weights...{}".format(tx))
        key = tx.get(TxEnum.KEY.name)
        value = tx.get(TxEnum.CONTENT.name)
        args = {TxEnum.KEY.name: key, TxEnum.CONTENT.name: ipfs_to_content(self.client, value)}
        # TODO: Put into in-memory datastore.
        self.communication_manager.inform("NEW_INFO",
                                            args)
        self.listen_new_weights()

    def handle_terminate(self) -> None:
        self.communication_manager.inform("TERMINATE", None)

    def listen_decentralized_learning(self):
        """
        Polls blockchain for node ID in decentralized_learning() method
        signature decentralized_learning(...<node_ids>...) method signature
        will be the key on the blockchain; listener should look for this, and
        if the method signature contains its node id, it will trigger a
        callback
        """
        def filter(tx):
            logging.info("tx: {}".format(tx))
            return tx.get(TxEnum.KEY.name) == tx.get(TxEnum.CONTENT.name)
        return self.filter_set(filter,
                                self.handle_decentralized_learning_trainer)

    def listen_new_weights(self) -> None:
        """
        Polls blockchain for node ID in new_weights() method signature
        new_weights(...<node_ids>...) method signature will be the key on the
        blockchain; listener should look for this, and if the method signature
        contains its node id, it will trigger a callback
        """
        logging.info("I'm listening for new weights!")
        def weights_filter(tx):
            logging.info("filtering for new weights: {}".format(tx))
            return tx.get(TxEnum.KEY.name) != tx.get(TxEnum.CONTENT.name)
        self.filter_set(weights_filter, self.handle_new_weights)

    def listen_terminate(self) -> None:
        """
        Polls blockchain to see whether to terminate
        """
        def filter(tx):
            logging.info("tx: {}".format(tx))
            return tx.get('content') is None
        self.filter_set(filter, self.handle_terminate)
    