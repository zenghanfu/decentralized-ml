import numpy as np
from core.blockchain.ipfs_utils import ipfs2keras

# from core.utils.keras import serialize_weights, deserialize_single_weights
from collections import defaultdict
import numpy as np
from transitions import Machine
from core.utils.dmljob import DMLJob, serialize_job, deserialize_job
from core.fed_learning import federated_averaging

class CommunicationManager(object):
	# Here will be the instance stored.
    __instance = None

    @staticmethod
    def get_instance():
        """ Static access method. """
        if CommunicationManager.__instance == None:
            CommunicationManager()
        return CommunicationManager.__instance

	def __init__(self):
		''' 
		Method that starts the class
		Set up initial values for class properties
		Bind port for outgoing communications
		'''
		if CommunicationManager.__instance != None:
            raise Exception("This class is a singleton!")
        else:
            CommunicationManager.__instance = self
		self.sessions_metadata = None
		# Dictionary from session_id to optimizers
		self.optimizers = None		

	def inform(session_id, event, details):
		'''
		Method called by other modules to inform the Communication Manager about:
		- an event (string) that occurred in the Unix service corresponding the session specified by session_id
		- any optional details (dictionary) about this event
		Event will likely trigger or contribute to the trigger of a transition on the Optimizer, unless
		the transition is invalid for the given Optimizer
		Ex: Runner informs the Communication Manager that a node is done training and it needs to comm. the
		new weights to the network
		'''

	def get_state(session_id):
		'''
		Returns the state of the particular optimization session corresponding to session_id
		'''
		optimizer = self.optimizers.get(session_id)
		return optimizer.state

	def _send(session_id, node_id, message):
		'''
		Send a message to a node within the particular optimization session corresponding to session_id
		'''

	def _send_to_all(session_id, message):
		'''
		Send a message to all nodes within the particular optimization session corresponding to session_id
		'''

	def _create_session(session_id, optimization_networks, active_optimizer):
		'''
		Helper function to populate the optimization_network, state_machine, and active_optimizers
		which are class properties of a new session
		This also binds the session_id to a particular port
		'''
		new_optimizer = Optimizer({'transitions': , 'states': , 'initial': , 'properties': })
		self.optimizers[session_id] = new_optimizer

	def _drop_session(session_id):
		'''
		Helper function to remove a particular session from the class properties
		'''
		del self.optimizers[session_id]

class Optimizer(Machine):
	def __init__(self, kwargs):
		'''
		Kwargs is a dictionary containing all the info needed to initialize the Optimizer.
		This includes any number of properties such as thresholds, etc.
		This init method also should set up the DMLRunner for this Optimizer.
		'''
		transitions = kwargs['transitions']
		states = kwargs['states']
		initial = kwargs['initial']
		Machine.__init__(self, transitions=transitions, states=states, initial=initial)
		self.properties = kwargs['properties']
		#TODO: Set up DMLRunner (how does it have a ConfigManager?)
		self.DMLRunner = DMLRunner(ConfigurationManager)


	def make_job_from_event(event):
		return deserialize_job(event)

	def do_training(self, event):
		'''
		Event data should be a callback of what to train, but this defaults to training
		the model this Optimizer currently knows
		'''
		#TODO: Call the train method of the DMLRunner
		job = self.make_job_from_event(event)
		job_results = self.DMLRunner.run_job(job)

	def do_averaging(self, event):
		'''
		When there are many models to be averaged, the Optimizer needs to validate them,
		and then do a weighted average.
		To validate, the DMLRunner needs to be used (by default, we validate on what we have)
		and then averaging is done simply
		'''
		# Get the weights
		old_weights = event['weights']
		# Make a validation job with the weights
		job = self.make_job_from_event(event)
		# Do a validation run with the validation job
		job_results = self.DMLRunner.run_job(job)
		# Take the output of the validation run and average these weights
        federated_averaging(job_results)
        
    def get_model_with_addr(self, model_addr):
    	'''
    	This Optimizer has been sent the address of a model that it should pick up
    	Use the IPFS method to deserialize the model (currently only Keras)
    	'''
    	# TODO: Be able to deserialize more than just Keras models
        return ipfs2keras(self.neural_network, model_addr)
    
    def on_enter_training(self, event):
        model_addr = event.kwargs.get('model_addr')
        self.neural_network = self.get_model_with_addr(model_addr)
        print(self.model)
        
    def on_exit_training(self, event):
        print("result of training {}".format(self.neural_network))
        
    def is_valid(self, event):
        return True
    
    def time_elapsed(self, event):
        return self.time >= self.time_threshold
    
    def is_also_valid(self):
        return True

# class Optimizer(object):
#     def __init__(self, participants, hyperparams):
#         self.metaDict = defaultdict(lambda: defaultdict(lambda: None))
#         for participant in participants:
#             """
#             participant should be the whoAmI() of the node
#             call a bunch of setter functions. let's see whether this works...
#             """
#             self.setInstructions(participant, participants, hyperparams)
#             self.setInformation(participant, participants, hyperparams)
#             self.setNeighbors(participant, participants, hyperparams)

#     def setInstructions(self, nodeID, participants, hyperparams):
#         # creates generator of instructions for this node
#         self.metaDict['instructions'][nodeID] = lambda: None;

#     def setInformation(self, nodeID, participants, hyperparams):
#         # creates generator of information for this node
#         self.metaDict['information'][nodeID] = lambda: None;

#     def setNeighbors(self, nodeID, participants, hyperparams):
#         # creates generator of neighbors for this node
#         self.metaDict['neighbors'][nodeID] = lambda: None;

#     def getIP(self):
#         # return the IP that nodes should be listening on, default 127.0.0.1
#         return hyperparams.get('IP')

#     def getPort(self):
#         # return the port that nodes should be listening on
#         return hyperparams.get('port')

#     def getInfo(self, nodeID):
#         # tell this node how to get the info it needs to do its job
#         return None

#     def getInstr(self, nodeID):
#         # tell this node what to do with the info it just got
#         return None

#     def sendInfo(self, nodeID):
#         # tell this node where to send the result of its instruction
#         return self.metaDict['neighbors'][nodeID]()

#     def key(self, nodeID, retval):
#         # key the information appropriately and return the key
#         return content_hash(retval)

#     def value(self, nodeID, retval):
#         # get the value appropriately and return the value
#         return retval

# class FederatedAveraging(Optimizer):
#     def __init__(self, participants, hyperparams):
#         """
#         make sure to initialize any instance variables which will be used by 
#         the super's init method (i.e. anything called in the setter instance
#         methods)
#         """
#         self.averager = np.random.choice((participants))
#         super().__init__(participants, hyperparams)
    
#     def setNeighbors(self, nodeID, participants, hyperparams):
#         """
#         creates generator of neighbors for this node
#         for federated averaging, we want each node to know that it needs to
#         send its information to one specific node.
#         except for that one specific node, which needs to broadcast its info
#         to all the other nodes.
#         """
#         def neighbor(averager):
#             while True:
#                 yield averager
#         retval = neighbor(self.averager)
#         self.metaDict['neighbors'][nodeID] = lambda: next(retval)

#     def setInstructions(self, nodeID, participants, hyperparams):
#         def instruct():
#             while True:

#         retval = instruct()
#         self.metaDict['instructions'][nodeID] = lambda: next(retval)


# def setOptimizer(optimizer):
#     # should be able to set parameters in the node by calling appropriate getter methods from the Optimizer. if we find ourselves having to implement Optimizer-specific methods in the P2P node, then we should rethink our architecture.
#     # bootstrap to the specific nodes in the rest of the offchain
#     self.bootstrap(optimizer.getIP(), optimizer.getPort())
#     # ask the optimizer what you should be calculating; functions via callback. whoAmI is a node instance method that tells the optimizer details of this node. Ex: optimizer tells you to train a model. Or avg a model.
#     calcval = optimizer.whatToSend(self.whoAmI())
#     # ask optimizer what info you need. this would give you a model, or list of models.
#     getval = optimizer.whatToGet(self.whoAmI())
#     # callback currently is just a bunch of switch cases. we'll abstract this. it finds the appropriate function via string switch-case, then calls the function with getval as the argument.
#     retval = self.callback(calcval, getval)
#     # ask optimizer how to encode the key-value relationship for your retval. Ex: if you're propagating a new model, what should the key and value be?
#     self.send(optimizer.key(self.whoAmI(), retval), optimizer.value(self.whoAmI(), retval)) 

# # def optimize(port, optimizer):
#     # initialize node with the correct port/socket combination; this is how an offchain channel actually functions -by telling a specific group of peers to communicate on a specific port. now, messages will only propagate through nodes that are listening on this specific port, AKA other members of the offchain instance.
#     # tempOffChain = node.Node(self.name, port)
#     # tempOffChain.setOptimizer(optimizer)

# def federated_averaging(list_of_serialized_weights):
#     """
#     Deserializes, averages, and returns the weights in the
#     `list_of_serialized_weights`.

#     NOTE: Currently only does vanilla Federated Averaging.
#     NOTE: doesn't use omega (hard coded right now).
#     """
#     assert len(list_of_serialized_weights) == 2, \
#         "Only supports 2 clients right now, {} given.".format(
#         len(list_of_serialized_weights))
#     omegas = [0.5, 0.5] # HARDCODED right now.

#     # Deserialize and average weights.
#     averaged_weights = []
#     num_layers = len(list_of_serialized_weights[0])
#     for j in range(num_layers):
#         layer_weights_list = []
#         for i, serialized_weights in enumerate(list_of_serialized_weights):
#             bytestring = serialized_weights[j]
#             deserialized_weight = deserialize_single_weights(serialized_weights[j])
#             layer_weights_list.append(omegas[i] * deserialized_weight)
#         averaged_weights.append(sum(layer_weights_list) / sum(omegas))
#     return averaged_weights

# if __name__ == "__main__":
#     optimizer = FederatedAveraging([1,2,3],[1,2])
#     print(optimizer.sendInfo(1))


