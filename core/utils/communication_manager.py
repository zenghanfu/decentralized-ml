import numpy as np
from core.blockchain.ipfs_utils import ipfs2keras

# from core.utils.keras import serialize_weights, deserialize_single_weights
from collections import defaultdict
import numpy as np
from transitions import Machine
from core.utils.dmljob import DMLJob, serialize_job, deserialize_job
from core.fed_learning import federated_averaging
from enum import Enum
from core.optimizers import Optimizer, CommunicationManagerEventTypes

class CommunicationManager(object):

	def __init__(self, configManager):
		''' 
		Method that starts the class
		Set up initial values for class properties
		Bind port for outgoing communications
		'''
		self.configManager = configManager
		self.sessions_metadata = None
		# Dictionary from session_id to optimizers
		self.optimizers = None	
		#TODO: Bind port for outgoing communications
	def schedule_job(self, event):
		'''
		Helper function to help the Comm. Mgr. schedule a DMLJob from what it received from the Optimizer
		'''
		job = self.make_job_from_event(event)
		self.scheduler.add_job(job)
		
	def communicate_p2p(self, event):
		# TODO
		pass

	def do_nothing(self, event):
	    print("NOTHING")

	EVENT_TYPE_CALLBACKS = {
		    EventTypes.INTERNAL.value: schedule_job, 
		    EventTypes.EXTERNAL.value: communicate_p2p,
		    EventTypes.UNDEFINED.value: do_nothing,
		}

	def parse(self, event):
	    """
	    Parses an event dictionary into a callback.
	    If the callback is not defined, it does nothing.
	    """
	    event_type = event.get('OptimizerEventType', EventTypes.UNDEFINED.value)
	    callback = EVENT_TYPE_CALLBACKS[EventTypes.UNDEFINED.value]
	    if event_type in EVENT_TYPE_CALLBACKS:
	        callback = EVENT_TYPE_CALLBACKS[event_type]
	    # ASYNCHRONOUS callback
	    callback(event)



	def configure(self, scheduler):
		self.scheduler = scheduler

	def inform(self, session_id, payload):
		'''
		Method called by other modules to inform the Communication Manager about:
		- an event (string) that occurred in the Unix service corresponding the session specified by session_id
		Event will likely trigger or contribute to the trigger of a transition on the Optimizer, unless
		the transition is invalid for the given Optimizer
		Ex: Runner informs the Communication Manager that a node is done training and it needs to comm. the
		new weights to the network
		'''
		optimizer = self.optimizers[session_id]
		# CommunicationManager tells the Optimizer what to do, and does stuff based on the return behavior (if any)
		# SYNCHRONOUS callback
		optimizer_callback = optimizer.tell(payload)
		# ASYNCHRONOUS callback
		self.parse(optimizer_callback)


	def get_state(self, session_id):
		'''
		Returns the state of the particular optimization session corresponding to session_id
		'''
		optimizer = self.optimizers.get(session_id)
		return optimizer.state

	def _send(self, session_id, node_id, message):
		'''
		Send a message to a node within the particular optimization session corresponding to session_id
		'''

	def _send_to_all(self, session_id, message):
		'''
		Send a message to all nodes within the particular optimization session corresponding to session_id
		'''

	def _create_session(self, session_id, optimization_networks, active_optimizer):
		'''
		Helper function to populate the optimization_network, state_machine, and active_optimizers
		which are class properties of a new session
		This also binds the session_id to a particular port
		'''
		new_optimizer = Optimizer({'transitions': , 'states': , 'initial': , 'properties': })
		self.optimizers[session_id] = new_optimizer
		new_optimizer.configure(self)

	def _drop_session(self, session_id):
		'''
		Helper function to remove a particular session from the class properties
		'''
		del self.optimizers[session_id]

	def make_job_from_event(self, event):
		'''
		Helper function to help the Comm. Mgr. make a DMLJob from what it received from the Optimizer
		'''
		return deserialize_job(event)