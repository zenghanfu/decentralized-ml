import numpy as np
# from core.blockchain.ipfs_utils import content_hash

# from core.utils.keras import serialize_weights, deserialize_single_weights
from collections import defaultdict
import numpy as np

class Optimizer(object):
    def __init__(self, participants, hyperparams):
        self.metaDict = defaultdict(lambda: defaultdict(lambda: None))
        for participant in participants:
            # participant should be the whoAmI() of the node
            # call a bunch of setter functions. let's see whether this works...
            self.setInstructions(participant, participants, hyperparams)
            self.setInformation(participant, participants, hyperparams)
            self.setNeighbors(participant, participants, hyperparams)

    def setInstructions(self, nodeID, participants, hyperparams):
        # creates generator of instructions for this node
        self.metaDict['instructions'][nodeID] = lambda: None;

    def setInformation(self, nodeID, participants, hyperparams):
        # creates generator of information for this node
        self.metaDict['information'][nodeID] = lambda: None;

    def setNeighbors(self, nodeID, participants, hyperparams):
        # creates generator of neighbors for this node
        self.metaDict['neighbors'][nodeID] = lambda: None;

    def getIP(self):
        # return the IP that nodes should be listening on, default 127.0.0.1
        return hyperparams.get('IP')

    def getPort(self):
        # return the port that nodes should be listening on
        return hyperparams.get('port')

    def getInfo(self, nodeID):
        # tell this node how to get the info it needs to do its job
        return None

    def getInstr(self, nodeID):
        # tell this node what to do with the info it just got
        return None

    def sendInfo(self, nodeID):
        # tell this node where to send the result of its instruction
        return self.metaDict['neighbors'][nodeID]()

    def key(self, nodeID, retval):
        # key the information appropriately and return the key
        return content_hash(retval)

    def value(self, nodeID, retval):
        # get the value appropriately and return the value
        return retval

class FederatedAveraging(Optimizer):
    def __init__(self, participants, hyperparams):
        self.averager = np.random.choice((participants))
        super().__init__(participants, hyperparams)
    
    def setNeighbors(self, nodeID, participants, hyperparams):
        # creates generator of instructions for this node
        def neighbor(averager):
            while True:
                yield averager
        retval = neighbor(self.averager)
        self.metaDict['neighbors'][nodeID] = lambda: next(retval);


def setOptimizer(optimizer):
    # should be able to set parameters in the node by calling appropriate getter methods from the Optimizer. if we find ourselves having to implement Optimizer-specific methods in the P2P node, then we should rethink our architecture.
    # bootstrap to the specific nodes in the rest of the offchain
    self.bootstrap(optimizer.getIP(), optimizer.getPort())
    # ask the optimizer what you should be calculating; functions via callback. whoAmI is a node instance method that tells the optimizer details of this node. Ex: optimizer tells you to train a model. Or avg a model.
    calcval = optimizer.whatToSend(self.whoAmI())
    # ask optimizer what info you need. this would give you a model, or list of models.
    getval = optimizer.whatToGet(self.whoAmI())
    # callback currently is just a bunch of switch cases. we'll abstract this. it finds the appropriate function via string switch-case, then calls the function with getval as the argument.
    retval = self.callback(calcval, getval)
    # ask optimizer how to encode the key-value relationship for your retval. Ex: if you're propagating a new model, what should the key and value be?
    self.send(optimizer.key(self.whoAmI(), retval), optimizer.value(self.whoAmI(), retval)) 

# def optimize(port, optimizer):
    # initialize node with the correct port/socket combination; this is how an offchain channel actually functions -by telling a specific group of peers to communicate on a specific port. now, messages will only propagate through nodes that are listening on this specific port, AKA other members of the offchain instance.
    # tempOffChain = node.Node(self.name, port)
    # tempOffChain.setOptimizer(optimizer)

def federated_averaging(list_of_serialized_weights):
    """
    Deserializes, averages, and returns the weights in the
    `list_of_serialized_weights`.

    NOTE: Currently only does vanilla Federated Averaging.
    NOTE: doesn't use omega (hard coded right now).
    """
    assert len(list_of_serialized_weights) == 2, \
        "Only supports 2 clients right now, {} given.".format(
        len(list_of_serialized_weights))
    omegas = [0.5, 0.5] # HARDCODED right now.

    # Deserialize and average weights.
    averaged_weights = []
    num_layers = len(list_of_serialized_weights[0])
    for j in range(num_layers):
        layer_weights_list = []
        for i, serialized_weights in enumerate(list_of_serialized_weights):
            bytestring = serialized_weights[j]
            deserialized_weight = deserialize_single_weights(serialized_weights[j])
            layer_weights_list.append(omegas[i] * deserialized_weight)
        averaged_weights.append(sum(layer_weights_list) / sum(omegas))
    return averaged_weights

if __name__ == "__main__":
    optimizer = FederatedAveraging([1,2,3],[1,2])
    print(optimizer.sendInfo(1))


