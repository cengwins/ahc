import datetime
from enum import Enum

class GenericMessagePayload:

  def __init__(self, messagepayload):
    self.messagepayload = messagepayload

class GenericMessage:

  def __init__(self, header, payload):
    self.header = header
    self.payload = payload
    self.uniqueid = str(header.messagefrom) + "-" + str(header.sequencenumber)

class GenericMessageHeader:

  def __init__(self, messagetype, messagefrom, messageto, nexthop=float('inf'), interfaceid=float('inf'), sequencenumber=-1):
    self.messagetype = messagetype
    self.messagefrom = messagefrom
    self.messageto = messageto
    self.nexthop = nexthop
    self.interfaceid = interfaceid
    self.sequencenumber = sequencenumber

class EventTypes(Enum):
  INIT = "init"
  MFRB = "msgfrombottom"
  MFRT = "msgfromtop"
  MFRP = "msgfrompeer"

class ConnectorTypes(Enum):
  DOWN = "DOWN"
  UP = "UP"
  PEER = "PEER"

class MessageDestinationIdentifiers(Enum):
  LINKLAYERBROADCAST = -1,  # sinngle-hop broadcast, means all directly connected nodes
  NETWORKLAYERBROADCAST = -2  # For flooding over multiple-hops means all connected nodes to me over one or more links


class Event:
  curr_event_id = 0

  def __init__(self, eventsource, event, eventcontent, fromchannel=None,
               eventid=-1):
    self.eventsource = eventsource
    self.event = event
    self.time = datetime.datetime.now()
    self.eventcontent = eventcontent
    self.fromchannel = fromchannel
    self.eventid = eventid
    if self.eventid == -1:
      self.eventid = self.curr_event_id
      self.curr_event_id += 1

  def __eq__(self, other) -> bool:
    if type(other) is not Event:
      return False

    return self.eventid == other.eventid

  def __hash__(self) -> int:
    return self.eventid


class FramerObjects():
  framerobjects = {}
  ahcuhdubjects = {}
  def add_framer(self, id, obj):
    self.framerobjects[id] = obj

  def get_framer_by_id(self, id):
    return self.framerobjects[id]

  def add_ahcuhd(self, id, obj):
    self.ahcuhdubjects[id] = obj

  def get_ahcuhd_by_id(self, id):
    return self.ahcuhdubjects[id]
