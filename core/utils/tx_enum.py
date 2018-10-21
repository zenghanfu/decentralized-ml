from enum import Enum

class TxEnum(Enum):
    """
    Enum of tx-related constants, e.g. standard keys present in a transaction
    """
    KEY = "KEY"
    CONTENT = "CONTENT"
    MESSAGES = "MESSAGES"
