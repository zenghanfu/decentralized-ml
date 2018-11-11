import logging

from core.utils.enums 		import ActionableEventTypes, RawEventTypes, MessageEventTypes
from core.utils.enums 		import JobTypes, callback_handler_no_default
from core.utils.dmljob 		import deserialize_job
from core.utils.keras 		import serialize_weights
from core.utils.dmlresult 	import DMLResult
from core.blockchain.tx_utils import TxEnum
logging.basicConfig(level=logging.DEBUG,
	format='[FedAvgOpt] %(asctime)s %(levelname)s %(message)s')


class FederatedAveragingOptimizer(object):
	"""
	Federated Averaging Optimizer

	Implements the Federated Averaging algorithm (with some tweaks) and acts as
	a "brain" or decision making component for the service. This class is
	tightly integrated with the Communication Manager, and serves as an
	abstraction between routing messages internally and making decisions on
	what messages to route and to where.

	The Optimizer stores the DML Job throghout the lifecycle of a DML Session,
	and passes it to the Communication Manager so it can be routed wherever
	needed.

	This particular optimizer works with callbacks:

		- There are "LEVEL 1" callbacks, which represent the types of Raw Events
	  	that the Optimizer needs to process.

		- There also are "LEVEL 2" callbacks, which represent a further breakdown
	  	of the "LEVEL 1" callbacks so that the Optimizer transform the event into
	  	a meaningful DML Job that can be executed by the Execution Pipeline.

	"""

	def __init__(self, initialization_payload):
		"""
		Initializes the optimizer.

		Expects the `initialization_payload` dict to contain two entries:

			- `serialized_job`: the serialized DML Job

			- `optimizer_params`: the optimizer parameters (dict) needed to
			initialize this optimizer (should contain the listen_iterations and
			listen_bound)
		"""
		logging.info("Setting up Optimizer")
		serialized_job = initialization_payload.get('serialized_job')
		self.job = deserialize_job(serialized_job)
		optimizer_params = initialization_payload.get('optimizer_params')
		self.listen_iterations = 0
		self.listen_bound = optimizer_params.get('listen_bound')
		self.total_iterations = 0
		self.total_bound = optimizer_params.get('total_bound')
		self.LEVEL1_CALLBACKS = {
			RawEventTypes.JOB_DONE.name: self._handle_job_done,
			RawEventTypes.NEW_INFO.name: self._handle_new_info,
			RawEventTypes.NEW_SESSION.name: self._do_nothing,
		}
		self.LEVEL2_JOB_DONE_CALLBACKS = {
			JobTypes.JOB_TRAIN.name: self._done_training,
			JobTypes.JOB_INIT.name: self._done_initializing,
			JobTypes.JOB_AVG.name: self._done_averaging,
			JobTypes.JOB_COMM.name: self._done_communicating,
		}
		self.LEVEL_2_INFO_CALLBACKS = {
			MessageEventTypes.NEW_WEIGHTS.name: self._received_new_weights,
			MessageEventTypes.TERMINATE.name: self._received_termination,
		}

		logging.info("Optimizer has been set up!")

	def kickoff(self):
		"""
		Kickoff method used at the beginning of a DML Session.

		Creates a job that transforms and splits the dataset, and also
		randomly initializes the model.
		"""
		self.job.job_type = JobTypes.JOB_INIT.name
		return ActionableEventTypes.SCHEDULE_JOB.name, self.job

	def ask(self, event_type, payload):
		"""
		Processes an event_type by calling the corresponding "LEVEL 1" Callback.
		"""
		callback = callback_handler_no_default(event_type, self.LEVEL1_CALLBACKS)
		return callback(payload)

	# Handlers for job completed in the execution pipeline

	def _handle_job_done(self, dmlresult_obj):
		"""
		"LEVEL 1" Callback that handles the conversion of a DML Result into a
		new DML Job by calling the appropriate "LEVEL 2" Callback.
		"""
		assert isinstance(dmlresult_obj, DMLResult)
		callback = callback_handler_no_default(
			dmlresult_obj.job.job_type,
			self.LEVEL2_JOB_DONE_CALLBACKS
		)
		logging.info("Job completed: {}".format(dmlresult_obj.job.job_type))
		return callback(dmlresult_obj)

	def _done_initializing(self, dmlresult_obj):
		"""
		"LEVEL 2" Callback for a initialization job that just completed. Returns
		a DML Job of type train and modifies the current state of the job.
		"""
		new_weights = dmlresult_obj.results.get('weights')
		self._update_weights(new_weights)
		self.job.job_type = JobTypes.JOB_TRAIN.name
		return ActionableEventTypes.SCHEDULE_JOB.name, self.job

	def _done_training(self, dmlresult_obj):
		"""
		"LEVEL 2" Callback for a training job that just completed. Returns a
		DML Job of type communication and modifies the current state of the job.

		NOTE: Assumes that the training succeeded. In the future, we may care
		about a degree of accuracy needed to be reached before updating the
		weights.
		"""
		new_weights = dmlresult_obj.results.get('weights')
		self._update_weights(new_weights)
		self.job.sigma_omega = 1 if not self.job.sigma_omega else self.job.sigma_omega
		self.job.job_type = JobTypes.JOB_COMM.name
		self.job.set_key("test")
		return ActionableEventTypes.SCHEDULE_JOB.name, self.job

	def _done_communicating(self, dmlresult_obj):
		"""
		"LEVEL 2" Callback for a Communication job.
		"""
		return ActionableEventTypes.NOTHING.name, self.job
	def _done_averaging(self, dmlresult_obj):
		new_weights = dmlresult_obj.results.get('weights')
		self._update_weights(new_weights)
		# Update our memory of the weights we've seen
		self.job.sigma_omega = dmlresult_obj.job.sigma_omega + dmlresult_obj.job.omega
		self.listen_iterations += 1
		if self.listen_iterations >= self.listen_bound:
			logging.info("DONE WITH ONE ROUND OF FEDERATED LEARNING!")
			self.job.job_type = JobTypes.JOB_TRAIN.name
			self.listen_iterations = 0
			# Reset sigma_omega
			self.job.sigma_omega = 1
			self.total_iterations += 1
			if self.total_iterations >= self.total_bound:
				return ActionableEventTypes.TERMINATE.name, self.job
			return ActionableEventTypes.SCHEDULE_JOB.name, self.job
		else:
			return ActionableEventTypes.NOTHING.name, self.job

	# Handlers for new information from the gateway
	# TODO: This will come with the Gateway PR.

	def _handle_new_info(self, payload):
		"""
		"LEVEL 1" Callback to handle new information from the blockchain.
		Payload structure should be:
		{TxEnum.KEY.name: <e.g. NEW_WEIGHTS>, 
		TxEnum.CONTENT.name: <e.g. weights>}	
		"""
		# TODO: Some assert on the payload, like in `_handle_job_done()`.
		callback = callback_handler_no_default(
			payload[TxEnum.KEY.name],
			self.LEVEL_2_INFO_CALLBACKS
		)
		return callback(payload)

	def _received_new_weights(self, payload):
		"""
		"LEVEL 2" Callback for new weights received by the service from the
		blockchain.	
		"""
		logging.info("Received new weights!")
		self.job.job_type = JobTypes.JOB_AVG.name
		self.job.omega = 1
		self.job.new_weights = payload[TxEnum.CONTENT.name]["weights"]
		return ActionableEventTypes.SCHEDULE_JOB.name, self.job

	def _received_termination(self, payload):
		"""
		"LEVEL 2" Callback for a termination message received by the service
		from the blockchain.
		"""
		return ActionableEventTypes.TERMINATE.name, None

	# Helper functions

	def _update_weights(self, weights):
		"""
		Helper function to update the weights in the optimizer's currently
		stored DML Job, therefore ensuring that any future DML Jobs will operate
		with the correct weights. Mutates, does not return anything.
		"""
		self.job.weights = weights

	def _do_nothing(self, payload):
		"""
		Do nothing in case this optimizer heard a new session.
		"""
		return ActionableEventTypes.NOTHING.name, None