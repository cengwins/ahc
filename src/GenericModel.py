import queue
from typing import ClassVar, Generic
from helpers import *
from generics import *
from definitions import *
from topology import *
from threading import Thread, Lock
from random import sample
from OSIModel import *
import GenericEvent


class GenericModel:
  
  def __init__(self) -> None:
      pass


  def send_up(self, event: GenericEvent):
      pass 

  def send_down(self, event: GenericEvent):
      pass 
