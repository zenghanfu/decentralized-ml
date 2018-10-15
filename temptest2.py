from core.communication_manager import CommunicationManager
from core.blockchain.blockchain_gateway import BlockchainGateway

configmgr = None
commmgr = CommunicationManager(configmgr)
blck = BlockchainGateway(configmgr, commmgr)
commmgr.configure_listener(blck)
# blck.broadcast_decentralized_learning({"kwargs": "booga booga"})
# blck.listen_decentralized_learning()
# blck.broadcast_new_weights({"weights": "smeargle can learn every move in Pokemon"})
# blck.broadcast_new_weights({"weights": "imma let you finish but the otsutsukis are a bunch of jobbers"})