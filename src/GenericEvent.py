import queue
from typing import ClassVar, Generic
from helpers import *
from generics import *
from definitions import *
from topology import *
from threading import Thread, Lock
from random import sample
from OSIModel import *
from generics import *

@auto_str
class GenericEvent:
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