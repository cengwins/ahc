from multiprocessing import Event
import time
from enum import Enum

from ...GenericModel import GenericModel, GenericMessageHeader, GenericMessagePayload, GenericMessage
from ...Generics import  *

#################FAILURE ASSUMPTIONS
# TODO: Correctness properties: Safety and liveness
# TODO: Model fail stop, fail silent, omission, fail-recover and byzantine failure models to the components
# TODO: Add storage (temporary, persistent) to crash-recover model

# define your own message types
class FailureDetectorMessageTypes(Enum):
  IAMALIVE = "IAMALIVE"

# define your own message header structure
class FailureDetectorMessageHeader(GenericMessageHeader):
  pass

# define your own message payload structure
class FailureDetectorMessagePayload(GenericMessagePayload):
  pass

# define your own component model extending the generic component model
# do not forget to define onInit event handler...MUST!

class FailureDetector(GenericModel):
  def on_tx_alive_message(self, eventobj: Event):
    time.sleep(self.alivemessageperiod)  # Period of alive messages
    # Send down the I'm Alive mesage
    # logger.debug("I am alive....")
    hdr = FailureDetectorMessageHeader(FailureDetectorMessageTypes.IAMALIVE, self.componentinstancenumber,
                                       MessageDestinationIdentifiers.LINKLAYERBROADCAST)
    payload = FailureDetectorMessagePayload(f"I am Node.{self.componentinstancenumber} and I am live ")
    failuredetectormessage = GenericMessage(hdr, payload)
    self.send_down(Event(self, EventTypes.MFRT, failuredetectormessage))
    # Schedule the next I'm Alive message
    self.send_self(Event(self, "txalivemessage", "timer for alive message"))

  def on_message_from_bottom(self, eventobj: Event):
    try:
      failuredetectormessage = eventobj.eventcontent
      hdr = failuredetectormessage.header
      if hdr.messagetype == FailureDetectorMessageTypes.IAMALIVE:
        logger.debug(f"Node-{self.componentinstancenumber} says Node-{hdr.messagefrom} has sent {hdr.messagetype} message")
      else:
        logger.debug(f"Node-{self.componentinstancenumber} says received {hdr.messagetype}")

    except AttributeError:
      logger.error("Attribute Error")

  def on_init(self, eventobj: Event):
    self.alivemessageperiod = 1
    self.send_self(Event(self, "txalivemessage", "timer for alive message"))

  def __init__(self, componentname, componentinstancenumber, context=None, configurationparameters=None, num_worker_threads=1, topology=None):
    super().__init__(componentname, componentinstancenumber, context, configurationparameters, num_worker_threads, topology)
    self.eventhandlers["txalivemessage"] = self.on_tx_alive_message
