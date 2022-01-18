from timeit import default_timer as timer
import random
import time

from ahc.Ahc import ComponentModel, Event, GenericMessage, GenericMessageHeader, EventTypes, Lock, Thread
from ahc.Routing.GSR.Constants import GSR_APPLICATION_NAME, \
    GSR_COORDINATOR_NAME, \
    ROUTING_COMPLETED_MESSAGE_TYPE, \
    TERMINATE_MESSAGE_TYPE, \
    INFO_MESSAGE_TYPE, \
    TOMBALA_DRAW_PERIOD_SECS, \
    TOMBALA_PLAYER_PERIOD_SECS, \
    TOMBALA_MAX_NUMBER, \
    TOMBALA_N_NUMBERS_IN_HAND
from ahc.Routing.GSR.GSRExperimentDataCollector import GSRExperimentCollector

class GSRExperimentApplicationComponent(ComponentModel):
    tombala_message_kind = "TOMBALA"
    winner_message_kind = "WINNER"
    new_number_message_kind = "NEW_NUMBER"

    def __init__(self, componentname, componentid):
        super(GSRExperimentApplicationComponent, self).__init__(componentname, componentid)
        self.n_nodes = 0
        self.game_completed = False
        self.winner = 0
        self.numbers = []
        self.message_queue = []
        self.queue_lock = Lock()

    def on_init(self, eventobj: Event):
        if self.componentinstancenumber > 0:
            self.numbers = [i for i in range(1, TOMBALA_MAX_NUMBER)]
            random.shuffle(self.numbers)
            self.numbers = self.numbers[0:TOMBALA_N_NUMBERS_IN_HAND]
            print(f"Hand of Player {self.componentinstancenumber}: {self.numbers}")
        thread = Thread(target=self.job, args=[14, 4, 18])
        thread.start()

    def on_message_from_bottom(self, eventobj: Event):
        event_header = eventobj.eventcontent.header
        message_to = event_header.messageto.split("-")[0]
        message_type = event_header.messagetype
        message = eventobj.eventcontent.payload
        if message_to == GSR_APPLICATION_NAME:
            if message_type == INFO_MESSAGE_TYPE:
                content = message["content"]
                self.queue_lock.acquire()
                self.message_queue.append(content)
                self.queue_lock.release()
            elif message_type == ROUTING_COMPLETED_MESSAGE_TYPE:
                self.end_time = timer()
                if self.n_nodes == 0:
                    print(f"App {self.componentinstancenumber} has received RoutingCompleted message")
                    self.n_nodes = message["n_nodes"]
                    print(f"There are {self.n_nodes} active nodes in the game")

    def send_info_message(self, dest, payload):
        message_header = GenericMessageHeader(
            INFO_MESSAGE_TYPE,
            GSR_APPLICATION_NAME + "-" + str(self.componentinstancenumber),
            GSR_COORDINATOR_NAME + "-" + str(self.componentinstancenumber))
        payload = {
            "src": self.componentinstancenumber,
            "dest": dest,
            "content": payload
        }
        message = GenericMessage(message_header, payload)
        event = Event(self, EventTypes.MFRT, message)
        self.send_down(event)

    def send_terminate_message(self):
        message_header = GenericMessageHeader(
            TERMINATE_MESSAGE_TYPE,
            GSR_APPLICATION_NAME + "-" + str(self.componentinstancenumber),
            GSR_COORDINATOR_NAME + "-" + str(self.componentinstancenumber))
        message = GenericMessage(message_header, "")
        event = Event(self, EventTypes.MFRT, message)
        self.send_down(event)

    def job(self, *arg):
        if self.componentinstancenumber == 0:
            while not self.game_completed:
                time.sleep(TOMBALA_DRAW_PERIOD_SECS)
                if self.n_nodes == 0:
                    continue
                self.check_messages_master()
                if self.winner > 0:
                    self.announce_winner()
                else:
                    self.announce_new_number()
        else:
            while not self.game_completed:
                time.sleep(TOMBALA_PLAYER_PERIOD_SECS)
                self.check_messages_player()
            if self.winner == self.componentinstancenumber:
                print(f"Player {self.componentinstancenumber}: I'm the winner!")
            else:
                print(f"Player {self.componentinstancenumber} congratulates Player {self.winner}! "
                      f"Numbers left in hand: {self.numbers}")
        self.send_terminate_message()
        GSRExperimentCollector().completion_lock.acquire()
        GSRExperimentCollector().completion.append(self.componentinstancenumber)
        GSRExperimentCollector().completion_lock.release()

    def check_messages_master(self):
        self.queue_lock.acquire()
        for message in self.message_queue:
            if message["kind"] == self.tombala_message_kind:
                winner = message["winner"]
                print(f"Master: Game is over! Player {winner} got TOMBALA!")
                self.game_completed = True
                self.winner = winner
        self.queue_lock.release()

    def check_messages_player(self):
        self.queue_lock.acquire()
        for message in self.message_queue:
            message_kind = message["kind"]
            if message_kind == self.new_number_message_kind:
                new_number = message["number"]
                if new_number in self.numbers:
                    print(f"Player {self.componentinstancenumber}: Has number {new_number}!")
                    self.numbers.remove(new_number)
                    if len(self.numbers) == 0:
                        self.announce_tombala()
            if message_kind == self.winner_message_kind:
                winner = message["winner"]
                self.winner = winner
                self.game_completed = True
        self.queue_lock.release()

    def announce_winner(self):
        for i in range(1, self.n_nodes):
            payload = {
                "kind": self.winner_message_kind,
                "winner": self.winner
            }
            self.send_info_message(i, payload)

    def announce_new_number(self):
        new_number = random.randint(1, TOMBALA_MAX_NUMBER)
        all_player_indexes = [i for i in range(1, self.n_nodes)]
        random.shuffle(all_player_indexes)
        payload = {
            "kind": self.new_number_message_kind,
            "number": new_number,
        }
        print(f"Master: Announcing new number {new_number}!")
        for player_index in all_player_indexes:
            self.send_info_message(player_index, payload)

    def announce_tombala(self):
        print(f"Player {self.componentinstancenumber}: Announcing TOMBALA!")
        payload = {
            "kind": self.tombala_message_kind,
            "winner": self.componentinstancenumber
        }
        self.send_info_message(0, payload)
