import datetime
import logging
from enum import Enum
from threading import Timer, Thread, Event


class GenericMessagePayload:

  def __init__(self, messagepayload):
    self.messagepayload = messagepayload

class GenericMessage:

  def __init__(self, header, payload):
    self.header = header
    self.payload = payload
    self.uniqueid = str(header.messagefrom) + "-" + str(header.sequencenumber)
  def __str__(self) -> str:
    return f"GENERIC MESSAGE: HEADER: {str(self.header)} PAYLOAD: {str(self.payload)}"

class GenericMessageHeader:

  def __init__(self, messagetype, messagefrom, messageto, nexthop=float('inf'), interfaceid=float('inf'), sequencenumber=-1):
    self.messagetype = messagetype
    self.messagefrom = messagefrom
    self.messageto = messageto
    self.nexthop = nexthop
    self.interfaceid = interfaceid
    self.sequencenumber = sequencenumber
  def __str__(self) -> str:
    return f"GenericMessageHeader: TYPE: {self.messagetype} FROM: {self.messagefrom} TO: {self.messagefrom} NEXTHOP: {self.nexthop} INTERFACEID: {self.interfaceid} SEQUENCE#: {self.sequencenumber}"

class EventTypes(Enum):
  INIT = "init"
  MFRB = "msgfrombottom"
  MFRT = "msgfromtop"
  MFRP = "msgfrompeer"
  EXIT = "exit"

class ConnectorTypes(Enum):
  DOWN = "DOWN"
  UP = "UP"
  PEER = "PEER"

class MessageDestinationIdentifiers(Enum):
  LINKLAYERBROADCAST = -1,  # sinngle-hop broadcast, means all directly connected nodes
  NETWORKLAYERBROADCAST = -2  # For flooding over multiple-hops means all connected nodes to me over one or more links


class Event:
  curr_event_id = 0

  def __init__(self, eventsource, event, eventcontent, fromchannel=None, eventid=-1, eventsource_componentname=None, eventsource_componentinstancenumber=None):
    self.eventsource = eventsource
    if eventsource is not None and eventsource_componentname is None:
      self.eventsource_componentname = eventsource.componentname
    else:
      self.eventsource_componentname = eventsource_componentname
    if eventsource is not None and eventsource_componentinstancenumber is None:
      self.eventsource_componentinstancenumber = eventsource.componentinstancenumber
    else:
      self.eventsource_componentinstancenumber = eventsource_componentinstancenumber
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

  # def __getstate__(self):
  #   return {
  #     #'eventsource': None,#self.eventsource,
  #     'eventsource_componentname': self.eventsource_componentname,
  #     'eventsource_componentinstancenumber': self.eventsource_componentinstancenumber,
  #     'event': self.event,
  #     'time': self.time,
  #     'eventcontent': self.eventcontent,
  #     'fromchannel': self.fromchannel,
  #     'eventid': self.eventid,
  #   }
  # def __setstate__(self, d):
  #   self.eventsource = None #d['eventsource']
  #   self.eventsource_componentname = d['eventsource_componentname']
  #   self.eventsource_componentinstancenumber = d['eventsource_componentinstancenumber']
  #   self.event = d['event']
  #   self.time = d['time']
  #   self.eventcontent = d['eventcontent']
  #   self.fromchannel = d['fromchannel']
  #   self.eventid = d['eventid']

  def __str__(self) -> str:
      return "EVENT: " + str(self.event) + " FROM " + str(self.eventsource_componentname) + "-" + str(self.eventsource_componentinstancenumber) + " RECEIVED FROM CHANNEL " + str(self.fromchannel) + " WITH CONTENT: " + str(self.eventcontent)

class FramerObjects():
  framerobjects = {}
  sdrobjects = {}
  def add_framer(self, id, obj):
    self.framerobjects[id] = obj

  def get_framer_by_id(self, id):
    return self.framerobjects[id]

  def add_sdrdev(self, id, obj):
    self.sdrobjects[id] = obj

  def get_sdrdev_by_id(self, id):
    return self.sdrobjects[id]



# A Dictionary that holds a list for the same key
class ConnectorList(dict):

  def __setitem__(self, key, value):
    try:
      self[key]
    except KeyError:
      super(ConnectorList, self).__setitem__(key, [])
    self[key].append(value)


class SDRConfiguration():
  def __init__(self, freq =2162000000.0, bandwidth = 250000, chan = 0, hw_tx_gain = 50.0, hw_rx_gain = 20.0, sw_tx_gain=-12.0):
      self.freq= freq
      self.bandwidth = bandwidth
      self.chan=chan
      self.hw_tx_gain=hw_tx_gain
      self.hw_rx_gain=hw_rx_gain
      self.sw_tx_gain=sw_tx_gain


DEBUG_LEVEL_APPLOG = 21
logging.addLevelName(DEBUG_LEVEL_APPLOG, "APPLOG")
def applog(self, message, *args, **kws):
    if self.isEnabledFor(DEBUG_LEVEL_APPLOG):
        # Yes, logger takes its '*args' as 'args'.
        self._log(DEBUG_LEVEL_APPLOG, message, args, **kws) 
logging.Logger.applog = applog


class CustomFormatter(logging.Formatter):

    debugcolor = '\033[0m' #"\x1b[38;20m"
    warningcolor = '\033[33m'#"\x1b[33;20m"''
    errorcolor = '\033[91m'
    infocolor = '\33[34m'
    criticialcolor = '\033[31m' #"\x1b[31;1m"
    applogcolor = '\33[7m'
    reset = '\033[0m' #"\x1b[0m"
    format = "===> %(asctime)s - %(name)s - %(levelname)s - %(message)s (%(filename)s:%(lineno)d)"

    FORMATS = {
        logging.DEBUG: debugcolor + format + reset,
        logging.INFO: infocolor + format + reset,
        DEBUG_LEVEL_APPLOG: applogcolor + format + reset,
        logging.WARNING: warningcolor + format + reset,
        logging.ERROR: errorcolor + format + reset,
        logging.CRITICAL: criticialcolor + format + reset
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


logger = logging.getLogger("AHC")
ch = logging.StreamHandler()

def setAHCLogLevel(level):
  logger.setLevel(level)
  ch.setLevel(level)
  ch.setFormatter(CustomFormatter())
  logger.addHandler(ch)


class AHCTimer():

  def __init__(self, t, hFunction):
    self.t = t
    self.hFunction = hFunction
    self.thread = Timer(self.t, self.handle_function)

  def handle_function(self):
    self.hFunction()
    self.thread = Timer(self.t, self.handle_function)
    self.thread.start()

  def start(self):
    self.thread.start()
  
  def cancel(self):
    self.thread.cancel()
