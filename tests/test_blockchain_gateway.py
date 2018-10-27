import tests.context	
import pytest	
from core.configuration import ConfigurationManager	
from core.blockchain.blockchain_gateway import BlockchainGateway
from core.utils.enums import RawEventTypes
from core.blockchain.tx_utils import TxEnum
@pytest.fixture	
def config_manager():	
    config_manager = ConfigurationManager()	
    config_manager.bootstrap(	
        config_filepath='tests/artifacts/blockchain/configuration.ini'	
    )	
    return config_manager	
@pytest.fixture	
def communication_manager():		
    class MockCommunicationManager:
        def __init__(self):
            self.dummy1 = None
            self.dummy2 = None
        def inform(self, dummy1, dummy2):
            self.dummy1 = dummy1
            self.dummy2 = dummy2
    return MockCommunicationManager()
@pytest.fixture	
def blockchain_gateway(config_manager, communication_manager):	
    blockchain_gateway = BlockchainGateway()
    blockchain_gateway.configure(config_manager, communication_manager)
    return blockchain_gateway	

def test_blockchain_gateway_can_be_initialized(config_manager, communication_manager):	
    blockchain_gateway = BlockchainGateway()
    assert blockchain_gateway is not None	


# TODO: This will be implemented once we figure out how.	
def test_blockchain_gateway_can_listen_decentralized_learning(config_manager, communication_manager):
    blockchain_gateway = BlockchainGateway()
    blockchain_gateway.configure(config_manager, communication_manager)
    developer = BlockchainGateway()
    developer.configure(config_manager, communication_manager)
    # developer.broadcast_decentralized_learning({"model": "hello world"})
    blockchain_gateway.listen_decentralized_learning()
    # at this point we should listen for decentralized learning, hear it, then
    # start listening for new weights and hear them as well
    assert communication_manager.dummy1 == RawEventTypes.NEW_INFO.name, "Wrong dummy1"
    assert communication_manager.dummy2.get(TxEnum.CONTENT.name)
# def test_handle_decentralized_learning(blockchain_gateway):	
#     """To be implemented."""	
#     pass	
# def test_listen_new_weights(blockchain_gateway):	
#     """To be implemented."""	
#     pass	
# def test_handle_new_weights(blockchain_gateway):	
#     """To be implemented."""	
#     pass	
# def test_listen_terminate(blockchain_gateway):	
#     """To be implemented."""	
#     pass	
# def test_handle_terminate(blockchain_gateway):	
#     """To be implemented."""	
#     pass