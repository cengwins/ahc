import os
import datetime
import sys
import os
from time import sleep

from cryptography.hazmat.primitives import hashes
from ahc.Ahc import ComponentModel, Event, ConnectorTypes, Topology, EventTypes, GenericMessage, GenericMessageHeader
from ahc.Ahc import ComponentRegistry
from ahc.Ahc import EventTypes, ConnectorList, MessageDestinationIdentifiers
from ahc.Ahc import Event
from ahc.Channels.Channels import P2PFIFOPerfectChannel, Channel

sys.path.insert(0, os.getcwd())
registry = ComponentRegistry()

# USAGE:
# Register <username> <password> => Creates a new user
# Login <username> <password> => Authenticates the user, prints hash comparison for testing purposes
# Print => Lists registered users' hashes and salts
# Different from oneWayAuth.py, 5 wrong password locks alice out, restart the program.
# Also adaptive slowdown is implemented.

class UserSimulator(ComponentModel):
    """UserSimulator simulates a user who is trying to log in to a system"""

    def on_init(self, eventobj: Event):
        x = input()
        msg = GenericMessage(GenericMessageHeader("AL", 0, 1), x)
        self.send_down(Event(self, EventTypes.MFRT, msg))

    def on_message_from_bottom(self, eventobj: Event):
        if eventobj.eventcontent.payload == "Access Granted":
            print(eventobj.eventcontent.payload)
            x = input()
            msg = GenericMessage(GenericMessageHeader("AL", 0, 1), x)
            self.send_down(Event(self, EventTypes.MFRT, msg))
        elif eventobj.eventcontent.payload == "Access Denied":
            print(eventobj.eventcontent.payload)
            x = input()
            msg = GenericMessage(GenericMessageHeader("AL", 0, 1), x)
            self.send_down(Event(self, EventTypes.MFRT, msg))
        elif eventobj.eventcontent.payload == "Register Successful":
            print(eventobj.eventcontent.payload)
            x = input()
            msg = GenericMessage(GenericMessageHeader("AL", 0, 1), x)
            self.send_down(Event(self, EventTypes.MFRT, msg))
        else:
            print(eventobj.eventcontent.payload)
            x = input()
            msg = GenericMessage(GenericMessageHeader("AL", 0, 1), x)
            self.send_down(Event(self, EventTypes.MFRT, msg))


class Authenticator(ComponentModel):
    def __init__(self, componentname, componentid):
        super().__init__(componentname, componentid)
        self.userlist = {}
        self.errors = 0

    def enrolluser(self, userid, password):
        digest = hashes.Hash(hashes.SHA3_512())
        salt_value = os.urandom(64)
        password_as_bytes = str.encode(password)
        digest.update(password_as_bytes)
        digest.update(salt_value)
        hash_value = digest.finalize()
        self.userlist[userid] = {"salt": salt_value, "hash": hash_value}
        return "Register Successful"

    def printusers(self):
        def pretty(d, indent=0):
            for key, value in d.items():
                print('\t' * indent + str(key) + ":")
                if isinstance(value, dict):
                    pretty(value, indent + 1)
                else:
                    print('\t' * (indent + 1) + str(value))

        pretty(self.userlist, 0)

    def authuser(self, userid, password):
        if userid in self.userlist:
            salt = self.userlist[userid]['salt']
            hassh = self.userlist[userid]['hash']
        else:
            return "Access Denied, User Does Not Exist!"
        digest = hashes.Hash(hashes.SHA3_512())
        password_as_bytes = str.encode(password)
        digest.update(password_as_bytes)
        digest.update(salt)
        sleep(self.errors * 1)
        hash_value = digest.finalize()
        if hash_value == hassh:
            return "Access Granted"
        else:
            self.errors += 1
            return "Access Denied"

    def on_message_from_bottom(self, eventobj: Event):
        if eventobj.eventcontent.payload.split()[0].lower() == "login":
            pload = self.authuser(eventobj.eventcontent.payload.split()[1], eventobj.eventcontent.payload.split()[2])
            msg = GenericMessage(GenericMessageHeader("AL", 1, 0), pload)
            if self.errors < 5:
                self.send_down(Event(self, EventTypes.MFRT, msg))
            else:
                print("You are locked out, please contact system administrator to password reset.")
        elif eventobj.eventcontent.payload.split()[0].upper() == "PRINT":
            self.printusers()
            msg = GenericMessage(GenericMessageHeader("AL", 1, 0), "")
            self.send_down(Event(self, EventTypes.MFRT, msg))
        elif eventobj.eventcontent.payload.split()[0].lower() == "register":
            pload = self.enrolluser(eventobj.eventcontent.payload.split()[1], eventobj.eventcontent.payload.split()[2])
            msg = GenericMessage(GenericMessageHeader("AL", 1, 0), pload)
            self.send_down(Event(self, EventTypes.MFRT, msg))
        else:
            msg = GenericMessage(GenericMessageHeader("AL", 1, 0), "SOMETHING IS WRONG I CAN FEEL IT")
            self.send_down(Event(self, EventTypes.MFRT, msg))


class Alice(ComponentModel):
    def on_init(self, eventobj: Event):
        pass

    def on_message_from_top(self, eventobj: Event):
        self.send_down(Event(self, EventTypes.MFRT, eventobj.eventcontent))

    def on_message_from_bottom(self, eventobj: Event):
        self.send_up(Event(self, EventTypes.MFRB, eventobj.eventcontent))

    def __init__(self, componentname, componentid):
        # SUBCOMPONENTS
        self.alice_top = UserSimulator("UserSimulator", componentid)

        self.alice_top.connect_me_to_component(ConnectorTypes.DOWN, self)
        self.connect_me_to_component(ConnectorTypes.UP, self.alice_top)

        super().__init__(componentname, componentid)


class Bob(ComponentModel):
    def on_init(self, eventobj: Event):
        pass

    def on_message_from_top(self, eventobj: Event):
        self.send_down(Event(self, EventTypes.MFRT, eventobj.eventcontent))

    def on_message_from_bottom(self, eventobj: Event):
        self.send_up(Event(self, EventTypes.MFRB, eventobj.eventcontent))

    def __init__(self, componentname, componentid):
        # SUBCOMPONENTS
        self.bob_top = Authenticator("Authenticator", componentid)

        self.bob_top.connect_me_to_component(ConnectorTypes.DOWN, self)
        self.connect_me_to_component(ConnectorTypes.UP, self.bob_top)

        super().__init__(componentname, componentid)


def main():
    topo = Topology();
    topo.construct_sender_receiver(Alice, Bob, Channel)
    topo.start()

    while True: pass


if __name__ == "__main__":
    main()
