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

@pytest.fixture
def blockchain_gateway(config_manager, communication_manager):
    blockchain_gateway = BlockchainGateway(config_manager, communication_manager)
    return blockchain_gateway

def test_blockchain_gateway_can_be_initialized(blockchain_gateway):
    assert blockchain_gateway is not None

def test_blockchain_gateway_interface(blockchain_gateway):
    blockchain_gateway.setter('hello', 'world')
    get_val = blockchain_gateway.getter('hello')
    assert get_val == ['world']

def test_listen_decentralized_learning(blockchain_gateway):
    """To be implemented."""
    pass

def test_handle_decentralized_learning(blockchain_gateway):
    """To be implemented."""
    # params = {}
    # blockchain_gateway.broadcast_decentralized_learning(params)
    # blockchain_gateway.listen_decentralized_learning()
    # assert 
    pass

def test_listen_new_weights(blockchain_gateway):
    """To be implemented."""
    pass

def test_handle_new_weights(blockchain_gateway):
    """To be implemented."""
    pass

def test_listen_terminate(blockchain_gateway):
    """To be implemented."""
    pass

def test_handle_terminate(blockchain_gateway):
    """To be implemented."""
    pass