import tests.context

import pytest

from core.configuration import ConfigurationManager
# from core.communication_manager import CommunicationManager
from core.blockchain.blockchain_gateway import BlockchainGateway


@pytest.fixture
def config_manager():
    config_manager = ConfigurationManager()
    config_manager.bootstrap(
        config_filepath='tests/artifacts/configuration.ini'
    )
    return config_manager

@pytest.fixture
def communication_manager(config_manager):
    # NOTE: We will fill this out when the PR for the Comm. Mgr. is done.
    # communication_manager = CommunicationManager(config_manager)
    # return communication_manager
    return None

@pytest.fixture
def blockchain_gateway(config_manager, communication_manager):
    blockchain_gateway = BlockchainGateway(config_manager, communication_manager)
    return blockchain_gateway


def test_blockchain_gateway_can_be_initialized(blockchain_gateway):
    assert blockchain_gateway is not None

def test_blockchain_gateway_public_interface_works(blockchain_gateway):
    blockchain_gateway.setter('hello', 'world')
    get_val = blockchain_gateway.getter('hello')
    assert get_val == ['world']

def test_listen_decentralized_learning(blockchain_gateway):
    """To be implemented."""
    pass

def test_handle_decentralized_learning(blockchain_gateway):
    """To be implemented."""
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