from enum import Enum

class TxEnum(Enum):
    """
    Enum of tx-related constants, e.g. standard keys present in a transaction
    """
    KEY = "KEY"
    CONTENT = "CONTENT"
    MESSAGES = "MESSAGES"

class Transaction(object):
    """
    Object that represents transactions with the specification outlined:
        `{
            'key': ...
            'value': ...
         }`
    """
    def __init__(self, key: str, value: object) -> None:
        self.key = key
        self.value = value

    def __repr__(self) -> dict:
        return {TxEnum.KEY.name: self.key, TxEnum.CONTENT.name: self.value}
