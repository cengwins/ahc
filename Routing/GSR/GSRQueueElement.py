import time


class GSQQueueElement:
    link_states = {}
    sequence_numbers = {}
    source_id = -1
    transfer_duration = -1

    def __init__(self, source_id, payload):
        self.link_states = payload["link_states"].copy()
        self.sequence_numbers = payload["sequence_numbers"].copy()
        self.source_id = int(source_id)
        self.transfer_duration = time.time() * 1000 - payload["timestamp"]
