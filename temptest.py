from core.utils.event_types import CommMgrEventTypes, ActionableEventTypes, CommMgrEventTypes
from core.fedavgoptimizer import FederatedAveragingOptimizer
from core.communication_manager import CommunicationManager
from core.blockchain.blockchain_client import BlockchainGateway

configmgr = None
commmgr = CommunicationManager(configmgr)
blck = BlockchainGateway(configmgr, commmgr)
commmgr.configure_listener(blck)
blck.broadcast_decentralized_learning("decentralized learning")
blck.listen_decentralized_learning()