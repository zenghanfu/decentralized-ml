import tests.context

import pytest
import time

from core.communication_manager         import CommunicationManager
from core.runner                        import DMLRunner
from core.scheduler                     import DMLScheduler
from core.configuration                 import ConfigurationManager
from tests.testing_utils                import make_initialize_job, make_model_json
from tests.testing_utils                import make_serialized_job, serialize_job
from core.utils.enums                   import RawEventTypes, JobTypes, MessageEventTypes
from core.utils.keras                   import serialize_weights
from core.blockchain.blockchain_utils   import TxEnum


config_manager = ConfigurationManager()
config_manager.bootstrap(
    config_filepath='tests/artifacts/communication_manager/configuration.ini'
)

@pytest.fixture
def new_session_event():
    serialized_job = make_serialized_job()
    new_session_event = {
        TxEnum.KEY.name: None,
        TxEnum.CONTENT.name: {
            "optimizer_params": {"listen_bound": 2, "total_bound": 2},
            "serialized_job": serialized_job
        }
    }
    return new_session_event

def test_communication_manager_can_be_initialized():
    """
    Very simple check. Checks if the Communication Manager can initialize.
    """
    communication_manager = CommunicationManager()
    assert communication_manager


def test_communication_manager_fails_if_not_configured(new_session_event):
    """
    Ensures that Communication Manager won't be able to function if it's not
    configured.
    """
    communication_manager = CommunicationManager()
    try:
        communication_manager.inform(
            RawEventTypes.NEW_SESSION.name,
            new_session_event
        )
        raise Exception("This should have raised an exception")
    except Exception as e:
        assert str(e) == "Communication Manager needs to be configured first!"


def test_communication_manager_creates_new_sessions(new_session_event):
    """
    Ensures that upon receiving an initialization job, the Communication Manager
    will make an optimizer.
    """
    communication_manager = CommunicationManager()
    scheduler = DMLScheduler(config_manager)
    communication_manager.configure(scheduler)
    scheduler.configure(communication_manager)
    communication_manager.inform(
        RawEventTypes.NEW_SESSION.name,
        new_session_event
    )
    assert communication_manager.optimizer


def test_communication_manager_can_inform_new_job_to_the_optimizer():
    """
    Ensures that Communication Manager can tell the optimizer of something,
    and that the job will transfer correctly.
    """
    communication_manager = CommunicationManager()
    scheduler = DMLScheduler(config_manager)
    communication_manager.configure(scheduler)
    scheduler.configure(communication_manager)
    true_job = make_initialize_job(make_model_json())
    serialized_job = serialize_job(true_job)
    new_session_event = {
        TxEnum.KEY.name: None,
        TxEnum.CONTENT.name: {
            "optimizer_params": {},
            "serialized_job": serialized_job
        }
    }
    communication_manager.inform(
        RawEventTypes.NEW_SESSION.name,
        new_session_event
    )
    optimizer_job = communication_manager.optimizer.job
    assert optimizer_job.weights == true_job.weights
    assert optimizer_job.job_type == true_job.job_type
    assert optimizer_job.serialized_model == true_job.serialized_model
    assert optimizer_job.framework_type == true_job.framework_type
    assert optimizer_job.hyperparams == true_job.hyperparams
    assert optimizer_job.label_column_name == true_job.label_column_name

# NOTE: The following are tests that we will implement soon.

# def test_communication_manager_can_parse_events_correctly(communication_manager):
#     """To be implemented."""
#     assert False, "Implement me!"


# def test_communication_manager_terminates_sessions():
#     """
#     Tests that the Communication Manager can terminate a session after setting it up.
#     """
#     communication_manager = CommunicationManager()
#     scheduler = DMLScheduler(config_manager, communication_manager)
#     communication_manager.configure(scheduler)
#     true_job = make_initialize_job(make_model_json())
#     serialized_job = serialize_job(true_job)
#     new_session_event = {
#         "key": None,
#         "content": {
#             "optimizer_params": {},
#             "serialized_job": serialized_job
#         }
#     }
#     communication_manager.inform(RawEventTypes.NEW_SESSION.name, new_session_event)
#     terminate_session_event = {
#         "key": None,
#         "content": {}
#     }
#     communication_manager.inform(RawEventTypes.NEW_INFO.name, terminate_session_event)
#     assert not communication_manager.optimizer
