from enum import Enum
'''
This file contains all <>EventTypes used in IPC.
Enum["string of entry"] returns the entry itself.
e.g. 
OptimizerEventTypes["TRAIN"] returns <OptimizerEventTypes.TRAIN>
'''
class CommMgrEventTypes(Enum):
    '''
    Dictionary of events that the Optimizer might receive from the Communication Manager.
    The event indicates what has occurred previously in the Communication Manager.
    This is essentially a 'memory' for the Optimizer so these are all past 
    i.e. a "TRAIN" event would contain auxiliary information about what occurred,
    in the form of a DMLResults object.
    Contains all the functionality of
    what the Communication Manager might have previously done and therefore is not specific
    to any one Optimizer.
    '''
    SCHEDULE = "SCHEDULE"
    TERMINATE = "TERMINATE"
    NOTHING = "NOTHING"

class OptimizerEventTypes(Enum):
    '''
    Dictionary of events that the Communication Manager might receive from the Optimizer.
    The event indicates what state the Optimizer has transitioned to.
    This is essentially a 'command' for the Comm. Mgr. so these are all imperatives.
    This dictionary has to contain all possible states that an Optimizer can be in.
    '''
    TRAIN = "training"
    COMM = "communicating"
    AVERAGE = "averaging"
    SPLIT = "splitting"
    TERMINATE = "terminate"
    # WEIGHT = "WEIGHT"
    UNDEFINED = "UNDEFINED"