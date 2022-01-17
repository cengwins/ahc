import time
from datetime import datetime
from enum import Enum

from ahc.Ahc import GenericMessagePayload, GenericMessageHeader, GenericMessage
import copy

class DBR2PMesageType(Enum):
    RDRequest = "RouteDiscoveryRequest"
    RDReply = "RouteDiscoveryReply"
    BSP = "BackupSetupPacket"
    LFM = "LinkFailMessage"
    LRM = "LinkRecoveryMessage"
    ERROR = 'error'
    DT = "DataTransfer"  # this is just for testing


# define your own message header structure
class DBR2PMessageHeader(GenericMessageHeader):
    def __init__(self, messagetype, messagefrom, messageto, nexthop=float('inf'), interfaceid=float('inf'),
                 sequencenumber=-1):
        super(DBR2PMessageHeader, self).__init__(messagetype, messagefrom, messageto, nexthop, interfaceid,
                                                 sequencenumber)


class DBR2PMessagePayload(GenericMessagePayload):
    def __init__(self, messagepayload, time_now=time.time()):
        super(DBR2PMessagePayload, self).__init__(messagepayload)
        self.time = time_now  # Take time on arrival at destination



