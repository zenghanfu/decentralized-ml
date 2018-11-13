import tests.context
import pytest
import time
from multiprocessing import Process

from core.communication_manager         import CommunicationManager
from core.runner                        import DMLRunner
from core.scheduler                     import DMLScheduler
from core.configuration                 import ConfigurationManager
from tests.testing_utils                import make_initialize_job, make_model_json
from tests.testing_utils                import make_serialized_job, serialize_job
from core.utils.enums                   import RawEventTypes, JobTypes, MessageEventTypes
from core.utils.keras                   import serialize_weights
from core.blockchain.blockchain_gateway import BlockchainGateway
from core.blockchain.blockchain_utils   import setter, TxEnum


config_manager = ConfigurationManager()
config_manager.bootstrap(
    config_filepath='tests/artifacts/communication_manager/configuration.ini'
)

@pytest.fixture
def new_session_event():
    initialize_job = make_initialize_job(make_model_json())
    initialize_job.hyperparams['epochs'] = 10
    initialize_job.hyperparams['batch_size'] = 128
    initialize_job.hyperparams['split'] = .9
    serialized_job = serialize_job(initialize_job)
    # serialized_job = make_serialized_job()
    new_session_event = {
        TxEnum.KEY.name: None,
        TxEnum.CONTENT.name: {
            "optimizer_params": {"listen_bound": 2, "total_bound": 2},
            "serialized_job": serialized_job
        }
    }
    return new_session_event

def test_federated_learning_two_clients_automated(new_session_event):
    """
    Tests fully automated federated learning.
    """
    # Set up first client
    communication_manager = CommunicationManager()
    blockchain_gateway = BlockchainGateway()
    scheduler = DMLScheduler(config_manager)
    communication_manager.configure(scheduler)
    blockchain_gateway.configure(config_manager, communication_manager)
    scheduler.configure(communication_manager)
    # Set up second client
    communication_manager_2 = CommunicationManager()
    blockchain_gateway_2 = BlockchainGateway()
    scheduler_2 = DMLScheduler(config_manager)
    communication_manager_2.configure(scheduler_2)
    blockchain_gateway_2.configure(config_manager, communication_manager_2)
    scheduler_2.configure(communication_manager_2)
    # (0) Someone sends decentralized learning event to the chain
    tx_receipt = setter(blockchain_gateway.client, None, blockchain_gateway.port, new_session_event, True)
    assert tx_receipt
    # scheduler.start_cron(period_in_mins=0.01)
    # scheduler_2.start_cron(period_in_mins=0.01)
    # blockchain_gateway.start_cron(period_in_mins=0.01)
    # blockchain_gateway_2.start_cron(period_in_mins=0.01)
    # timeout = 25 + time.time()
    # while time.time() < timeout and len(scheduler.processed) < 9:
    #     time.sleep(5)
    # scheduler.stop_cron()
    # scheduler_2.stop_cron()
    # blockchain_gateway.stop_cron()
    # blockchain_gateway_2.stop_cron()
    # assert len(scheduler.processed) == 9, "Jobs failed/not completed in time!"
    # assert len(scheduler_2.processed) == 9, "Jobs failed/not completed in time!"
    # assert communication_manager.optimizer is None
    # assert communication_manager_2.optimizer is None

# def test_federated_learning_two_clients_manual(new_session_event):
#     """
#     Integration test that checks that one round of federated learning can be
#     COMPLETED with total_bound = 2, listen_bound = 1, a.k.a one client
#     training on its own.

#     This is everything that happens in this test:

#     """
#     # Set up first client
#     communication_manager = CommunicationManager()
#     blockchain_gateway = BlockchainGateway()
#     scheduler = DMLScheduler(config_manager)
#     communication_manager.configure(scheduler)
#     blockchain_gateway.configure(config_manager, communication_manager)
#     scheduler.configure(communication_manager)
#     # Set up second client
#     communication_manager_2 = CommunicationManager()
#     blockchain_gateway_2 = BlockchainGateway()
#     scheduler_2 = DMLScheduler(config_manager)
#     communication_manager_2.configure(scheduler_2)
#     blockchain_gateway_2.configure(config_manager, communication_manager_2)
#     scheduler_2.configure(communication_manager_2)
#     # set up new session
#     # (0) Someone sends decentralized learning event to the chain
#     tx_receipt = setter(blockchain_gateway.client, None, blockchain_gateway.port, new_session_event, True)
#     assert tx_receipt
#     # (1) Gateway_1 listens for the event
#     blockchain_gateway.listen(blockchain_gateway._handle_new_session_creation, 
#         blockchain_gateway._filter_new_session)
#     # (2) Gateway_2 listens for the event
#     blockchain_gateway_2.listen(blockchain_gateway_2._handle_new_session_creation, 
#         blockchain_gateway_2._filter_new_session)
#     # (3) Scheduler_1 and Scheduler_2 runs the following jobs:
#         # (3a) JOB_INIT
#         # (3b) JOB_TRAIN
#         # (3c) JOB_COMM
#     scheduler.start_cron(period_in_mins = 0.01)
#     scheduler_2.start_cron(period_in_mins=0.01)
#     time.sleep(9)
#     assert len(scheduler.processed) == 3, "Jobs failed/not completed in time!"
#     assert len(scheduler_2.processed) == 3, "Jobs failed/not completed in time!"
#     # (4) Gateway_1 listens for the new weights 
#     blockchain_gateway.listen(blockchain_gateway._handle_new_session_info,
#         blockchain_gateway._filter_new_session_info)
#     # (6) Gateway_2 listens for the new weights
#     blockchain_gateway_2.listen(blockchain_gateway_2._handle_new_session_info,
#         blockchain_gateway_2._filter_new_session_info)
#     # (8) Scheduler_1 and Scheduler_2 runs the following jobs:
#         # (6a) JOB_AVG
#         # (6b) JOB_AVG
#         # (6a) JOB_TRAIN
#         # (6a) JOB_COMM
#     time.sleep(9)
#     assert len(scheduler.processed) == 7, \
#         "Jobs {} failed/not completed in time!".format([
#             result.job.job_type for result in scheduler.processed])
#     assert len(scheduler_2.processed) == 7, "Jobs failed/not completed in time!"
#     # (4) Gateway_1 listens for the new weights 
#     blockchain_gateway.listen(blockchain_gateway._handle_new_session_info,
#         blockchain_gateway._filter_new_session_info)
#     # (6) Gateway_2 listens for the new weights
#     blockchain_gateway_2.listen(blockchain_gateway_2._handle_new_session_info,
#         blockchain_gateway_2._filter_new_session_info)
#     # (13) Optimizer tells Communication Manager to schedule JOB_AVG
#     # (14) Scheduler_1 and Scheduler_2 runs the following jobs:
#         # (9a) JOB_AVG
#         # (9a) JOB_AVG
#     time.sleep(2)
#     scheduler.stop_cron()
#     scheduler_2.stop_cron()
#     assert len(scheduler.processed) == 9, "Jobs failed/not completed in time!"
#     assert len(scheduler_2.processed) == 9, "Jobs failed/not completed in time!"
#     # (10) Optimizer terminates
#     assert communication_manager.optimizer is None, "Should have terminated!"
#     assert communication_manager_2.optimizer is None, "Should have terminated!"
#     # and that completes one local round of federated learning!

# def test_federated_learning_one_client():
#     """
#     Integration test that checks that one round of federated learning can be
#     COMPLETED with total_bound = 2, listen_bound = 1, a.k.a one client
#     training on its own.

#     This is everything that happens in this test:

 
#     """
#     communication_manager = CommunicationManager()
#     blockchain_gateway = BlockchainGateway()
#     scheduler = DMLScheduler(config_manager)
#     communication_manager.configure(scheduler)
#     blockchain_gateway.configure(config_manager, communication_manager)
#     scheduler.configure(communication_manager)
#     # set up new session
#     json = make_model_json()
#     true_job = make_initialize_job(json)
#     serialized_job = serialize_job(true_job)
#     new_session_event = {
#         TxEnum.KEY.name: None,
#         TxEnum.CONTENT.name: {
#             "optimizer_params": {"listen_bound": 1, "total_bound": 2},
#             "serialized_job": serialized_job
#         }
#     }
#     # (0) Someone sends decentralized learning event to the chain
#     tx_receipt = setter(blockchain_gateway.client, None, blockchain_gateway.port, new_session_event, True)
#     assert tx_receipt
#     # (1) Gateway listens for the event
#     await blockchain_gateway.listen_decentralized_learning(manual=True)
#     # (2) Optimizer tells Communication Manager to schedule JOB_INIT
#     assert communication_manager.optimizer.job.job_type == JobTypes.JOB_INIT.name, \
#         "Should be ready to init!"
#     # (3) Scheduler runs the following jobs:
#         # (3a) JOB_INIT
#         # (3b) JOB_TRAIN
#         # (3c) JOB_COMM
#     scheduler.start_cron(period_in_mins = 0.01)
#     time.sleep(7)
#     assert len(scheduler.processed) == 3, "Jobs failed/not completed in time!"
#     # (4) Gateway listens for the new weights that we just communicated to ourself
#     blockchain_gateway._listen_new_weights(manual=True)
#     # (5) Optimizer tells Communication Manager to schedule JOB_AVG
#     assert communication_manager.optimizer.job.job_type == JobTypes.JOB_AVG.name, \
#         "Should be ready to average!"
#     # (6) Scheduler runs the following jobs:
#         # (6a) JOB_AVG
#         # (6a) JOB_TRAIN
#         # (6a) JOB_COMM
#     time.sleep(7)
#     assert len(scheduler.processed) == 6, "Jobs failed/not completed in time!"
#     # (7) Gateway listens for the new weights that we just communicated to ourself
#     blockchain_gateway._listen_new_weights(manual=True)
#     # (8) Optimizer tells Communication Manager to schedule JOB_AVG
#     assert communication_manager.optimizer.job.job_type == JobTypes.JOB_AVG.name, \
#         "Should be ready to average!"
#     # (9) Scheduler runs the following jobs:
#         # (9a) JOB_AVG
#     time.sleep(2)
#     scheduler.stop_cron()
#     assert len(scheduler.processed) == 7, "Jobs failed/not completed in time!"
#     # (10) Optimizer terminates
#     assert communication_manager.optimizer is None, "Should have terminated!"
#     # and that completes one local round of federated learning!

def test_communication_manager_can_initialize_and_train_model(mnist_filepath):
    """
    Integration test that checks that the Communication Manager can initialize,
    train, (and soon communicate) a model, and average a model.

    NOTE: This should be renamed after the COMM PR.

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

    NOTE: These next steps are not implemented yet! (They need the COMM PR.)
    (13) Optimizer tells Communication Manager to schedule a communication job
    (14) Communication Manager schedules communication job
    (15) Communication Manager receives DMLResult for communication job from
         Scheduler
    (16) Communication Manager gives DMLResult to Optimizer
    (17) Optimizer tells the Communication Manager to do nothing

    NOTE: Next steps are specific to Averaging PR
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

    NOTE: Timeout errors can be as a result of Runners repeatedly erroring. Check logs for this.
    """
    communication_manager = CommunicationManager()
    scheduler = DMLScheduler(config_manager)
    communication_manager.configure(scheduler)
    scheduler.configure(communication_manager)
    true_job = make_initialize_job(make_model_json())
    serialized_job = serialize_job(true_job)
    new_session_event = {
        "key": None,
        "content": {
            "optimizer_params": {},
            "serialized_job": make_serialized_job(mnist_filepath)
        }
    }
    communication_manager.inform(
        RawEventTypes.NEW_SESSION.name,
        new_session_event
    )

    assert communication_manager.optimizer.job.job_type == JobTypes.JOB_INIT.name, \
        "Should be ready to init!"
    timeout = time.time() + 3
    while time.time() < timeout and len(scheduler.processed) == 0:
        # initialization job
        scheduler.runners_run_next_jobs()
        time.sleep(0.1)
    assert len(scheduler.processed) == 1, "Initialization failed/not completed in time!"
    assert communication_manager.optimizer.job.job_type == JobTypes.JOB_TRAIN.name, \
        "Should be ready to train!"
    timeout = time.time() + 3
    while time.time() < timeout and len(scheduler.processed) == 1:
        # training job
        scheduler.runners_run_next_jobs()
        time.sleep(0.1)
    assert len(scheduler.processed) == 2, "Training failed/not completed in time!"
    assert communication_manager.optimizer.job.job_type == JobTypes.JOB_COMM.name, \
        "Should be ready to communicate!"
    timeout = time.time() + 3
    while time.time() < timeout and len(scheduler.processed) == 2:
        # communication job
        scheduler.runners_run_next_jobs()
        time.sleep(0.1)
    assert len(scheduler.processed) == 3, "Communication failed/not completed in time!"
    # now the communication manager should be idle
    scheduler.runners_run_next_jobs()
    time.sleep(0.1)
    assert len(scheduler.processed) == 3, "No job should have been run!"
    # now it should hear some new weights
    new_weights_event = {
        "key": MessageEventTypes.NEW_WEIGHTS.name,
        "content": {
            "weights": serialize_weights(communication_manager.optimizer.job.weights)
        }
    }
    communication_manager.inform(
        RawEventTypes.NEW_INFO.name,
        new_weights_event
    )
    assert communication_manager.optimizer.job.job_type == JobTypes.JOB_AVG.name, \
        "Should be ready to average!"
    timeout = time.time() + 3
    while time.time() < timeout and len(scheduler.processed) == 3:
        # averaging job
        scheduler.runners_run_next_jobs()
        time.sleep(0.1)
    assert len(scheduler.processed) == 4, "Averaging failed/not completed in time!"
    # we've only heard one set of new weights so our listen_iters are 1
    assert communication_manager.optimizer.listen_iterations == 1, \
        "Should have only listened once!"
    # now the communication manager should be idle
    scheduler.runners_run_next_jobs()
    time.sleep(0.1)
    assert len(scheduler.processed) == 4, "No job should have been run!"
    # now it should hear more new weights
    communication_manager.inform(
        RawEventTypes.NEW_INFO.name,
        new_weights_event
    )
    assert communication_manager.optimizer.job.job_type == JobTypes.JOB_AVG.name, \
        "Should be ready to average!"
    timeout = time.time() + 3
    while time.time() < timeout and len(scheduler.processed) == 4:
        # second averaging job
        scheduler.runners_run_next_jobs()
        time.sleep(0.1)
    assert len(scheduler.processed) == 5, "Averaging failed/not completed in time!"
    # we've heard both sets of new weights so our listen_iters are 2
    assert communication_manager.optimizer.listen_iterations == 0, \
        "Either did not hear anything, or heard too much!"
    # now we should be ready to train
    assert communication_manager.optimizer.job.job_type == JobTypes.JOB_TRAIN.name, \
        "Should be ready to train!"
    # and that completes one local round of federated learning!
