import tests.context
import pytest
import time

from core.communication_manager import CommunicationManager
from core.runner                import DMLRunner
from core.scheduler             import DMLScheduler
from core.configuration         import ConfigurationManager
from tests.testing_utils        import make_initialize_job, make_model_json
from tests.testing_utils        import make_serialized_job, serialize_job
from core.utils.enums           import RawEventTypes, JobTypes, MessageEventTypes
from core.utils.keras           import serialize_weights
from core.blockchain.blockchain_gateway import BlockchainGateway
from core.blockchain.blockchain_utils import setter
from core.blockchain.tx_utils   import TxEnum

config_manager = ConfigurationManager()
config_manager.bootstrap(
    config_filepath='tests/artifacts/communication_manager/configuration.ini'
)

def test_federated_learning():
    """
    Integration test that checks that one round of federated learning can be
    COMPLETED.

    This is everything that happens in this test:

 
    """
    communication_manager = CommunicationManager()
    blockchain_gateway = BlockchainGateway()
    scheduler = DMLScheduler(config_manager)
    communication_manager.configure(scheduler)
    blockchain_gateway.configure(config_manager, communication_manager)
    scheduler.configure(communication_manager)
    # set up new session
    json = make_model_json()
    true_job = make_initialize_job(json)
    serialized_job = serialize_job(true_job)
    new_session_event = {
        TxEnum.KEY.name: None,
        TxEnum.CONTENT.name: {
            "optimizer_params": {"listen_bound": 1, "total_bound": 2},
            "serialized_job": serialized_job
        }
    }
    # (0) Someone sends decentralized learning event to the chain
    tx_receipt = setter(blockchain_gateway.client, None, blockchain_gateway.port, new_session_event, True)
    assert tx_receipt
    # (1) Gateway listens for the event
    blockchain_gateway.listen_decentralized_learning(manual=True)
    # (2) Optimizer tells Communication Manager to schedule JOB_INIT
    assert communication_manager.optimizer.job.job_type == JobTypes.JOB_INIT.name, \
        "Should be ready to init!"
    # (3) Scheduler runs the following jobs:
        # (3a) JOB_INIT
        # (3b) JOB_TRAIN
        # (3c) JOB_COMM
    scheduler.start_cron(period_in_mins = 0.01)
    time.sleep(7)
    scheduler.stop_cron()
    assert len(scheduler.processed) == 3, "Jobs failed/not completed in time!"
    # (4) Gateway listens for the new weights that we just communicated to ourself
    blockchain_gateway._listen_new_weights(manual=True)
    # (5) Optimizer tells Communication Manager to schedule JOB_AVG
    assert communication_manager.optimizer.job.job_type == JobTypes.JOB_AVG.name, \
        "Should be ready to average!"
    # (6) Scheduler runs the following jobs:
        # (6a) JOB_AVG
        # (6a) JOB_TRAIN
        # (6a) JOB_COMM
    scheduler.start_cron(period_in_mins = 0.05)
    time.sleep(10)
    scheduler.stop_cron()
    assert len(scheduler.processed) == 6, "Jobs failed/not completed in time!"
    # # (7) Gateway listens for the new weights that we just communicated to ourself
    # # (8) Optimizer tells Communication Manager to schedule JOB_AVG
    # assert communication_manager.optimizer.job.job_type == JobTypes.JOB_AVG.name, \
    #     "Should be ready to average!"
    # # (9) Scheduler runs the following jobs:
    #     # (9a) JOB_AVG
    #     # (9a) JOB_TRAIN
    #     # (9a) JOB_COMM
    # scheduler.start_cron(period_in_mins = 0.01)
    # time.sleep(13)
    # scheduler.stop_cron()
    # assert len(scheduler.processed) == 9, "Jobs failed/not completed in time!"
    # # (10) Optimizer terminates
    # assert communication_manager.optimizer is None, "Should have terminated!"
    # # and that completes one local round of federated learning!