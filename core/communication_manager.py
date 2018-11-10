import logging

from core.utils.enums       import RawEventTypes, ActionableEventTypes
from core.utils.enums       import callback_handler_no_default
from core.fed_avg_optimizer import FederatedAveragingOptimizer
from core.utils.dmljob      import DMLJob


logging.basicConfig(level=logging.DEBUG,
    format='[CommunicationManager] %(asctime)s %(levelname)s %(message)s')


class CommunicationManager(object):
    """
    Communication Manager

    Manages the communication within the modules of the service throughout all
    active DML Sessions.

    Right now, the service can only have one session at a time. This will be
    reflected in the code by just having one optimizer property and no
    information about sessions throughout the code.

    """

    def __init__(self):
        """
        Initializes the class.
        """
        logging.info("Setting up Communication Manager...")
        self.optimizer = None # NOTE: Since right now we're only dealing with
                              # one session at a time, the class is only
                              # concerned with one optimizer.
        self.scheduler = None
        # NOTE: This should be updated when Gateway PR is merged and we make
        # the Communication Manager error-handle out of order/missed messages.
        self.EVENT_TYPE_2_CALLBACK = {
            RawEventTypes.NEW_SESSION.name: self._create_session,
            ActionableEventTypes.SCHEDULE_JOB.name: self._schedule_job,
            ActionableEventTypes.TERMINATE.name: self._terminate_session,
            ActionableEventTypes.NOTHING.name: self._do_nothing,
        }
        logging.info("Communication Manager is set up!")

    # Setup Methods

    def configure(self, scheduler):
        """
        Configures the Communication Manager so that it can submit jobs to the
        Scheduler.
        """
        logging.info("Configuring the Communication Manager...")
        self.scheduler = scheduler
        logging.info("Communication Manager is configured!")

    # Public methods

    def inform(self, event_type, payload):
        """
        Method called by other modules to inform the Communication Manager about
        events that are going on in the service.

        If there isn't an active optimizer, the Communication Manager will handle it

        Else, payloads are relayed to the active optimizer which decides how
        and to whom the Communication Manager should communicate the event/message.

        For example: A runner could inform the Communication Manager that the
        node is done training a particular model, to which the Optimizer could
        decide it's time to communicate the new weights to the network.
        """
        # logging.info("Information has been received: {}".format(event_type))
        if self.optimizer:
            # We have an active session so we ask the optimizer what to do.
            event_type, payload = self.optimizer.ask(event_type, payload)
        callback = callback_handler_no_default(
            event_type,
            self.EVENT_TYPE_2_CALLBACK
        )
        callback(payload)

    # Callbacks

    def _create_session(self, payload):
        """
        Creates a new session and optimizer based on the parameters sent by a
        model developer. It then asks the optimizer what's the first thing to do
        and the service starts working on that session from that point on.
        """
        # NOTE: We removed the 'optimizer_type' argument since for the MVP we're
        # only considering the 'FederatedAveragingOptimizer' for now.
        # TODO: We need to incorporate session id's when we're ready.
        logging.info("New optimizer session is being set up...")
        initialization_payload = payload.get('content')
        self.optimizer = FederatedAveragingOptimizer(initialization_payload)
        logging.info("Optimizer session is set! Now doing kickoff...")
        event_type, payload = self.optimizer.kickoff()
        callback = callback_handler_no_default(
            event_type,
            self.EVENT_TYPE_2_CALLBACK,
        )
        callback(payload)
        logging.info("Kickoff complete.")

    def _schedule_job(self, dmljob_obj):
        """
        Helper function that schedules a DML Job through the Scheduler.
        """
        if not self.scheduler:
            raise Exception("Communication Manager needs to be configured first!")
        if not isinstance(dmljob_obj, DMLJob):
            raise Exception("Job is not valid!")
        self.scheduler.add_job(dmljob_obj)

    def _terminate_session(self, payload):
        """
        Helper function that removes the current session (and optimizer) from
        the Communication Manager.

        Note that it ignores the payload for now (since we're only dealing with
        one session).
        """
        self.optimizer = None
        logging.info("Session terminated.")

    def _do_nothing(self, payload):
        """
        Do nothing
        """
        logging.info("Doing nothing")
