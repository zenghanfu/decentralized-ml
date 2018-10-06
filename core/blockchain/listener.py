class Listener(object):
    def __init__(self, client):
        self.client = client
    def handle_decentralized_learning(self):
        """
        Downloads parameters of decentralized_learning() query and 
        saves them appropriately to in-memory datastore
        This callback will be triggered by the Listener if it finds the 
        method signature it's looking for.
        The parameters (model weights, model config) will be downloaded 
        and put into the optimizer initially. So the optimizer knows this info.
        """
        pass
    def listen_decentralized_learning(self):
        """
        Polls blockchain for node ID in decentralized_learning() method signature
        decentralized_learning(...<node_ids>...) method signature will be the key 
        on the blockchain; listener should look for this, and if the method signature 
        contains its node id, it will trigger a callback
        """
        pass
    def broadcast_new_weights(self):
        """
        broadcast_new_weights() method with all relevant parameters
        should populate the key of new_weights with all of the nodes for which 
        these new weights are relevant. value should be IPFS hash.
        """
        pass
    def listen_new_weights(self):
        """
        Polls blockchain for node ID in new_weights() method signature
        new_weights(...<node_ids>...) method signature will be the key on the blockchain; 
        listener should look for this, and if the method signature contains its node id, 
        it will trigger a callback
        """
        pass
    def listen_terminate(self):
        pass
    def handle_terminate(self):
        pass