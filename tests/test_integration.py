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

config_manager = ConfigurationManager()
config_manager.bootstrap(
    config_filepath='tests/artifacts/communication_manager/configuration.ini'
)

def test_federated_learning():
    """
    Integration test that checks that one round of federated learning can be
    COMPLETED.

    This is everything that happens in this test:

    (1) Communication Manager receives the packet it's going to receive from
        BlockchainGateway
    (2) Communication Manager gives packet to Optimizer
    (3) Optimizer tells Communication Manager to schedule an initialization job
    (4) Communication Manager schedules initialization job
    (5) Communication Manager receives DMLResult for initialization job from
        Scheduler
    (6) Communication Manager gives DMLResult to Optimizer
    (7) Optimizer updates its weights to initialized model
    (8) Optimizer tells Communication Manager to schedule a training job
    (9) Communication Manager schedules training job
    (10) Communication Manager receives DMLResult for training job from
         Scheduler
    (11) Communication Manager gives DMLResult to Optimizer
    (12) Optimizer updates its weights to trained weights
    (13) Optimizer tells Communication Manager to schedule a communication job
    (14) Communication Manager schedules communication job
    (15) Communication Manager receives DMLResult for communication job from
         Scheduler
    (16) Communication Manager gives DMLResult to Optimizer
    (17) Optimizer tells the Communication Manager to do nothing
    (18) Communication Manager receives new weights from Blockchain Gateway
    (19) Communication Manager gives new weights to Optimizer
    (20) Optimizer tells Communication Manager to schedule an averaging job
    (21) Communication Manager schedules averaging job
    (22) Communication Manager receives DMLResult for averaging job from
        Scheduler
    (23) Communication Manager gives DMLResult to Optimizer
    (24) Optimizer updates its weights to initialized model and increments listen_iterations
    (25) Optimizer tells Communication Manager to do nothing
    (26) Communication Manager receives new weights from Blockchain Gateway
    (27) Communication Manager gives new weights to Optimizer
    (28) Optimizer tells Communication Manager to schedule an averaging job
    (29) Communication Manager schedules averaging job
    (30) Communication Manager receives DMLResult for averaging job from
        Scheduler
    (31) Communication Manager gives DMLResult to Optimizer
    (32) Optimizer updates its weights to initialized model and increments listen_iterations
    (33) Optimizer tells Communication Manager to schedule a training job since it's heard enough

    """
    communication_manager = CommunicationManager()
    blockchain_gateway = BlockchainGateway()
    scheduler = DMLScheduler(config_manager)
    communication_manager.configure(scheduler)
    blockchain_gateway.configure(config_manager, communication_manager)
    scheduler.configure(communication_manager)
    json = make_model_json()
    true_job = make_initialize_job(json)
    serialized_job = serialize_job(true_job)
    new_session_event = {
        "key": None,
        "content": {
            "optimizer_params": {},
            "serialized_job": serialized_job
        }
    }
    # (0) Someone sends decentralized learning event to the chain
    tx_receipt = setter(blockchain_gateway.client, None, blockchain_gateway.port, new_session_event, True)
    assert tx_receipt
    # (1) Blockchain Gateway listens for decentralized learning
    scheduler.start_cron(period_in_mins=0.01)
    blockchain_gateway.listen_decentralized_learning()
    scheduler.stop_cron()
    assert False
    # # (1) Communication Manager receives the packet it's going to receive from BlockchainGateway
    
    # timeout = time.time() + 3
    # while time.time() < timeout and len(scheduler.processed) == 0:
    #     # initialization job
    #     scheduler.runners_run_next_jobs()
    #     time.sleep(0.1)
    # timeout = time.time() + 3
    # while time.time() < timeout and len(scheduler.processed) == 1:
    #     # training job
    #     scheduler.runners_run_next_jobs()
    #     time.sleep(0.1)
    # assert len(scheduler.processed) == 2
    # timeout = time.time() + 3
    # while time.time() < timeout and len(scheduler.processed) == 2:
    #     # communication job
    #     scheduler.runners_run_next_jobs()
    #     time.sleep(0.1)
    # assert len(scheduler.processed) == 3
    # # now the communication manager should be idle
    # scheduler.runners_run_next_jobs()
    # time.sleep(0.1)
    # assert len(scheduler.processed) == 3
    # # now it should hear some new weights
    # new_weights_event = {
    #     "key": MessageEventTypes.NEW_WEIGHTS.name,
    #     "content": {
    #         "weights": serialize_weights(communication_manager.optimizer.job.weights)
    #     }
    # }
    # communication_manager.inform(
    #     RawEventTypes.NEW_INFO.name,
    #     new_weights_event
    # )
    # timeout = time.time() + 3
    # while time.time() < timeout and len(scheduler.processed) == 3:
    #     # averaging job
    #     scheduler.runners_run_next_jobs()
    #     time.sleep(0.1)
    # # we've only heard one set of new weights so our listen_iters are 1
    # assert communication_manager.optimizer.listen_iterations == 1
    # # now the communication manager should be idle
    # scheduler.runners_run_next_jobs()
    # time.sleep(0.1)
    # # now it should hear more new weights
    # communication_manager.inform(
    #     RawEventTypes.NEW_INFO.name,
    #     new_weights_event
    # )
    # timeout = time.time() + 3
    # while time.time() < timeout and len(scheduler.processed) == 4:
    #     # second averaging job
    #     scheduler.runners_run_next_jobs()
    #     time.sleep(0.1)
    # # we've heard both sets of new weights so our listen_iters are 2
    # assert communication_manager.optimizer.listen_iterations == 0
    # # now we should be ready to train
    # assert communication_manager.optimizer.job.job_type == JobTypes.JOB_TRAIN.name
    # and that completes one local round of federated learning!