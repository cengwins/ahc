from enum import Enum

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