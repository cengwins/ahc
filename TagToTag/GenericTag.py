import random
from enum import Enum
import time
from threading import Thread, Lock

from Ahc import ComponentModel, MessageDestinationIdentifiers, Event, GenericMessageHeader, GenericMessagePayload, GenericMessage, EventTypes

class TagMessageTypes(Enum):
  TTT = "TAGTOTAG"
  RTI = "READERTOTAGINIT"
  RTC = "READERTOTAGCOLLECT"
  TRI = "TAGTOREADERINITRESPONSE"
  TRC = "TAGTOREADERCOLLECTRESPONSE"

class TagMessageHeader(GenericMessageHeader):
  pass

class TagPayload(GenericMessagePayload):
  pass

class TagMessage(GenericMessage):
  pass

class TagMessageDestinationIdentifiers(Enum):
  TAGTOTAGBROADCAST = -3

class TagComponent(ComponentModel):
  known_tags_list_max_length = 10
  min_seconds_to_repeat_same_tag = 30
  sleep_time_between_broadcast_second = 10

  def on_init(self, eventobj: Event):
    # print(f"Initializing {self.componentname}.{self.componentinstancenumber}")
    pass

  def start_tag_to_tag_broadcast_thread(self):
    t = Thread(target=self.send_tag_to_tag_broadcast_message_to_down, args=[self.tag_id])
    t.daemon = True
    t.start()

  def send_tag_to_tag_broadcast_message_to_down(self, tag_id):
    while True:
      message_header = TagMessageHeader(TagMessageTypes.TTT, tag_id, TagMessageDestinationIdentifiers.TAGTOTAGBROADCAST)
      message_payload = TagPayload(None)
      message = TagMessage(message_header, message_payload)

      self.send_down(Event(self, EventTypes.MFRT, message))

      time.sleep(random.randint(1, self.sleep_time_between_broadcast_second))

  def send_message_to_reader(self, reader_id, message, message_type):
    message_header = TagMessageHeader(message_type, self.tag_id, reader_id)
    message_payload = TagPayload(message)
    message = TagMessage(message_header, message_payload)

    self.send_down(Event(self, EventTypes.MFRT, message))

  def compare_tags_belong_to_same_person(self, other_tag_id):
    return int(other_tag_id/10) == int(self.tag_id/10)

  def on_message_from_bottom(self, eventobj: Event):
    incoming_message_time = time.perf_counter()
    message_header = eventobj.eventcontent.header
    message_type = message_header.messagetype
    message_from = message_header.messagefrom
    message_to = message_header.messageto

    if message_to == TagMessageDestinationIdentifiers.TAGTOTAGBROADCAST and message_type == TagMessageTypes.TTT and not(self.compare_tags_belong_to_same_person(message_from)):
      for check_index in range(self.known_tags_list_index - self.min_seconds_index_diff, self.known_tags_list_index):
        if incoming_message_time - self.known_tags_list[check_index][1] > self.min_seconds_to_repeat_same_tag:
          self.min_seconds_index_diff -= 1
        else:
          break

      founded = False
      for check_index in range(self.known_tags_list_index - self.min_seconds_index_diff, self.known_tags_list_index):
        if self.known_tags_list[check_index][0] == message_from:
          founded = True
          break

      if founded == False:
        self.known_tags_list[self.known_tags_list_index] = (message_from, incoming_message_time)
        self.known_tags_list_index = (self.known_tags_list_index + 1) % self.known_tags_list_max_length
        if self.min_seconds_index_diff + 1 < self.known_tags_list_max_length:
          self.min_seconds_index_diff += 1

    elif message_to == self.tag_id and self.compare_tags_belong_to_same_person(message_from):
      if message_type == TagMessageTypes.RTI:
        self.send_message_to_reader(message_from, self.known_tags_list_max_length, TagMessageTypes.TRI)
      elif message_type == TagMessageTypes.RTC:
        known_tags_list_index = eventobj.eventcontent.payload.messagepayload
        self.send_message_to_reader(message_from, (known_tags_list_index, self.known_tags_list[known_tags_list_index]), TagMessageTypes.TRC)

  def __init__(self, componentname, componentinstancenumber, tag_id):
    # tag_id = TC No. + [1-9]
    self.tag_id = tag_id
    self.known_tags_list = [None for i in range(0, self.known_tags_list_max_length)]
    self.known_tags_list_index = 0
    self.min_seconds_index_diff = 0
    self.start_tag_to_tag_broadcast_thread()

    super().__init__(componentname, componentinstancenumber)


class ReaderComponent(ComponentModel):
  reader_retry_count = 10
  reader_retry_timeout = 0.1
  def on_init(self, eventobj: Event):
    # print(f"Initializing {self.componentname}.{self.componentinstancenumber}")
    pass

  def start_collecting(self):
    self.incoming_messages = {}
    self.initially_reading_tag = None
    self.collector_thread.start()
    self.collector_thread = Thread(target=self.collect_tag_information_thread, args=[])
    self.collector_thread.daemon = True

  def collect_tag_information_thread(self):
    for tag_index in range(1, 10):
      tag_id = self.reader_id + tag_index
      self.incoming_messages[tag_id] = None
      retry = 0
      while retry < self.reader_retry_count:
        self.send_message_to_tag(tag_id, TagMessageTypes.RTI)
        starting_time = time.perf_counter()
        while time.perf_counter() - starting_time < self.reader_retry_timeout and self.incoming_messages[tag_id] == None:
          pass
        if self.incoming_messages[tag_id] != None:
          break
        retry += 1

    ids_to_delete = []
    for tag_id in self.incoming_messages:
      if self.incoming_messages[tag_id] == None:
        ids_to_delete.append(tag_id)
      else:
        for known_tags_list_index in range(0, len(self.incoming_messages[tag_id])):
          self.initially_reading_tag = (known_tags_list_index, tag_id)
          retry_count = 0
          while retry_count < self.reader_retry_count and self.initially_reading_tag == (known_tags_list_index, tag_id) and self.incoming_messages[tag_id][known_tags_list_index] == None:
            self.send_message_to_tag(tag_id, TagMessageTypes.RTC, known_tags_list_index)
            starting_time = time.perf_counter()
            while time.perf_counter() - starting_time < self.reader_retry_timeout and self.initially_reading_tag == (known_tags_list_index, tag_id) and self.incoming_messages[tag_id][known_tags_list_index] == None:
              pass
            retry_count += 1
          if self.initially_reading_tag == None:
            break
    for tag_id in ids_to_delete:
      del self.incoming_messages[tag_id]
    self.print_collected_information()

  def send_message_to_tag(self, send_to, message_type, payload=None):
    message_header = TagMessageHeader(message_type, self.reader_id, send_to)
    message_payload = TagPayload(payload)
    message = TagMessage(message_header, message_payload)

    self.send_down(Event(self, EventTypes.MFRT, message))

  def print_collected_information(self):
    for tag_id in self.incoming_messages:
      print("\n", tag_id, ": ", self.incoming_messages[tag_id], "\n")

  def compare_tags_belong_to_same_person(self, other_tag_id):
    return int(other_tag_id/10) == int(self.reader_id/10)

  def on_message_from_bottom(self, eventobj: Event):
    message_header = eventobj.eventcontent.header
    message_type = message_header.messagetype
    message_from = message_header.messagefrom
    message_to = message_header.messageto

    if message_to == self.reader_id and self.compare_tags_belong_to_same_person(message_from):
      if message_type == TagMessageTypes.TRI:
        if message_from in self.incoming_messages and self.incoming_messages[message_from] == None:
          known_tags_list_max_length = eventobj.eventcontent.payload.messagepayload
          self.incoming_messages[message_from] = [None for i in range(0, known_tags_list_max_length)]
      elif message_type == TagMessageTypes.TRC:
        tag_information = eventobj.eventcontent.payload.messagepayload
        if self.incoming_messages[message_from][tag_information[0]] == None and self.initially_reading_tag != None and message_from == self.initially_reading_tag[1] and tag_information[0] == self.initially_reading_tag[0]:
          if tag_information[1] == None:
            self.initially_reading_tag = None
          else:
            self.incoming_messages[message_from][tag_information[0]] = tag_information[1]

  def __init__(self, componentname, componentinstancenumber, reader_id):
    # reader_id = TC No. + 0
    self.reader_id = reader_id
    self.initially_reading_tag = None
    self.incoming_messages = {}

    self.collector_thread = Thread(target=self.collect_tag_information_thread, args=[])
    self.collector_thread.daemon = True
    super().__init__(componentname, componentinstancenumber)
