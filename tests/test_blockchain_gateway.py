import tests.context

import pytest

from core.configuration import ConfigurationManager
from core.communication_manager import CommunicationManager
from core.blockchain.blockchain_client import BlockchainGateway


@pytest.fixture
def config_manager():
    config_manager = ConfigurationManager()
    config_manager.bootstrap(
        config_filepath='tests/artifacts/configuration.ini'
    )
    return config_manager

@pytest.fixture
def communication_manager(config_manager):
    communication_manager = CommunicationManager(config_manager=config_manager)
    return communication_manager


def test_blockchain_gateway_can_be_initialized(config_manager, communication_manager):
    blockchain_gateway = BlockchainGateway(config_manager, communication_manager)
    assert blockchain_gateway is not None

def test_blockchain_gateway_interface(config_manager, communication_manager):
    blockchain_gateway = BlockchainGateway(config_manager, communication_manager)
    blockchain_gateway.setter('hello', 'world')
    get_val = blockchain_gateway.getter('hello')
    assert get_val == ['world']

def test_blockchain_gateway_can_schedule_training(config_manager, communication_manager):
    """To be implemented."""
    pass

def test_blockchain_gateway_can_pick_up_training(config_manager, communication_manager):
    """To be implemented."""
    pass

def test_blockchain_gateway_can_inform_the_optimizer(config_manager, communication_manager):
    """To be implemented."""
    pass

def test_blockchain_gateway_can_parse_events_correctly(config_manager, communication_manager):
    """To be implemented."""
    pass

def test_blockchain_gateway_terminates_training(config_manager, communication_manager):
    """To be implemented."""
    pass

def test_blockchain_gateway_picks_up_termination(config_manager, communication_manager):
    """To be implemented."""
    pass
