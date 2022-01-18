import binascii
import hashlib
import sys
import threading
import time
from copy import deepcopy
from enum import Enum

import networkx as nx
from random import choice

import matplotlib.pyplot as plt

from ahc.Channels.Channels import Channel
from ahc.Ahc import ComponentRegistry, Topology, GenericMessageHeader, GenericMessage, EventTypes, Event, ComponentModel

PATH_OF_DATA = "data"
sys.setrecursionlimit(1500)
def transaction_generator(numberofNodes,txn_count):
    for n in range(0,numberofNodes):
        filename =  f"{PATH_OF_DATA}/transaction{n}.txt"
        file = open(filename,"w")
        for i in range(0, txn_count):
            rnd_hex=''.join([str(y) for x in range(64) for y in choice('0123456789abcdef')])
            file.write(rnd_hex + "\n")
        file.close()
def hash_double(firstTxHash, secondTxHash):
    unhexReverseFirst = binascii.unhexlify(firstTxHash)[::-1]
    unhexReverseSecond = binascii.unhexlify(secondTxHash)[::-1]
    concatInputs = unhexReverseFirst + unhexReverseSecond
    firstHashInputs = hashlib.sha256(concatInputs).digest()
    finalHashInputs = hashlib.sha256(firstHashInputs).digest()
    return binascii.hexlify(finalHashInputs[::-1])

def merkle_root_calculator(hashList):
    if len(hashList) == 1:
        return hashList[0].decode('utf-8')
    hashes = []
    for i in range(0, len(hashList) - 1, 2):
        hashes.append(hash_double(hashList[i], hashList[i + 1]))
    if len(hashList) % 2 == 1:
        hashes.append( hashList[-1])
    return merkle_root_calculator(hashes)

class Block:
    def __init__(self, hashPrevHeader, merkleroot, timestamp, transactions, blockhash, nonce , height = 0):
        self.hashPrevHeader = hashPrevHeader
        self.merkleRoot = merkleroot
        self.timestamp = timestamp
        self.transactions = transactions
        self.nonce = nonce
        self.hashBlockHeader = blockhash
        self.height = height

class Blockchain:
    def __init__(self, difficulty=4):
        self.blocks = []
        self.difficulty = difficulty
        self.generate_genesis_block()


    def generate_genesis_block(self):
        genesis_block = Block("0", "0",time.time(), [], "0", 0, 0)
        self.blocks.append(genesis_block)

    def get_last_block(self):
        return self.blocks[-1]

class NkMessageTypes(Enum):
    TXN = "transaction"
    VLD = "validation"
    QUERY_LC = "querylongestchain"
    RW_LC = "responsewithlongestchain"


class NkComponent(ComponentModel):
    def __init__(self, componentname, componentinstancenumber, difficulty=5):
        super().__init__(componentname, componentinstancenumber)
        self.blockchain = Blockchain()
        self.txnPool = []
        self.txnLog = []
        self.difficulty = difficulty
        self.isMiner = True

        # To test components with different registeries
        self.speedDown = 1

        self.lock = threading.Lock()
        minerThread = threading.Thread(target=self.mine_next_block)
        minerThread.daemon = True
        minerThread.start()

    def on_init(self, eventobj: Event):

        with open(f"data/transaction{self.componentinstancenumber}.txt", "r") as txns:
            txn_list = txns.read()
        self.txnPool = txn_list.splitlines()
        self.passNextBlock = True

    def print_chain(self):
        print(f"{self.componentname}-{self.componentinstancenumber} blockchain is : ")
        for b in self.blockchain.blocks:
            print(f"{b.hashPrevHeader}-{b.hashBlockHeader}\n")

    def on_message_from_bottom(self, eventobj: Event):
        msg = eventobj.eventcontent
        msgType = msg.header.messagetype
        msgPayload = msg.payload
        msgfrom = msg.header.messagefrom
        msgto = msg.header.messageto
        '''
        Three types of message could be transmitted:
        1) Transaction Messages : A new transaction from client is added to transaction pool and 
           the node broadcast that to nearby nodes (probably miners)
        2) Validation Message : Recently mined  block is recieved for validation from other nodes and local blockchain is 
        updated if it obeys to rules
        3) Blockchain update message : Periodically a chain queries the blockchains from neighbour nodes, if their blockchain
        is more up to date and valid, replace current chain with more recent one  and add transactions stored in current 
        blockchain to pool which doesnt included in new chain

        '''
        self.lock.acquire()
        if msgType == NkMessageTypes.TXN:
            if msgPayload in self.txnPool:
                pass
            else:
                self.txnPool.append(msgPayload)
                nk_header = GenericMessageHeader(NkMessageTypes.TXN, self, None)
                nk_payload = msgPayload
                nk_eventContent = GenericMessage(nk_header, nk_payload)
                nk_event = Event(self, EventTypes.MFRT, nk_eventContent)
                self.send_down(nk_event)

        elif msgType == NkMessageTypes.VLD:
            if self.is_valid(msgPayload) and self.is_prev_correct(msgPayload):
                self.txnPool = [txn for txn in self.txnPool if not txn in msgPayload.transactions]
                self.blockchain.blocks.append(msgPayload)
                nk_header = GenericMessageHeader(NkMessageTypes.VLD, self, None)
                nk_payload = msgPayload
                nk_eventContent = GenericMessage(nk_header, nk_payload)
                nk_event = Event(self, EventTypes.MFRT, nk_eventContent)
                self.send_down(nk_event)
                print(f"Component {self.componentinstancenumber}  validated a new block: "
                      f"txn count= {len(self.txnPool)} - block count= {len(self.blockchain.blocks)}\n"
                      f"{self.blockchain.get_last_block().hashPrevHeader}")
                self.passNextBlock = True

            elif msgPayload.height > self.blockchain.get_last_block().height:
                print(f"Component {self.componentinstancenumber}  the message block height is higher ")
                self.search_longest_chain()

        elif msgType == NkMessageTypes.QUERY_LC:
            # response to sender
            nk_header = GenericMessageHeader(NkMessageTypes.RW_LC, self, msgfrom)
            nk_payload = deepcopy(self.blockchain)
            nk_eventContent = GenericMessage(nk_header, nk_payload)
            nk_event = Event(self, EventTypes.MFRT, nk_eventContent)
            self.send_down(nk_event)

        elif msgType == NkMessageTypes.RW_LC and msgto is self:
            if msgPayload.get_last_block().height > self.blockchain.get_last_block().height:
                nTxn = []
                self.txnPool.extend(self.txnLog)  # Restore back all txn mined before to txn pool
                self.txnLog.clear() # Not necessary but memory overload causes crashes
                for block in msgPayload.blocks:
                    nTxn.extend(block.transactions)
                self.txnPool = [txn for txn in self.txnPool if txn not in nTxn]  # Eliminate the ones in new ledger
                self.blockchain = msgPayload
                self.passNextBlock = False
                print(f"Component {self.componentinstancenumber} received a longer chain: "
                      f"txn count= {len(self.txnPool)} - block count= {len(self.blockchain.blocks)}\n"
                      f"{self.blockchain.get_last_block().hashPrevHeader}")

            else:
                pass
        self.lock.release()

    def is_valid(self, inBlock: Block):
        prvHeader = inBlock.hashPrevHeader
        mrklRoot = inBlock.merkleRoot
        nonce = inBlock.nonce
        hdr = (mrklRoot + str(nonce) + prvHeader).encode('utf-8')
        blockHash = hashlib.sha256(hdr).hexdigest()
        return blockHash.startswith("0" * self.difficulty)

    def is_prev_correct(self, inBlock: Block):
        currBlockHash = self.blockchain.blocks[-1].hashBlockHeader
        inBlockPrvHash = inBlock.hashPrevHeader
        return currBlockHash == inBlockPrvHash

    def mine_next_block(self, minTxnPackage=10):
        while self.isMiner:
            if minTxnPackage <= len(self.txnPool):
                txnPending = self.txnPool[:minTxnPackage]
                lastBlock = self.blockchain.get_last_block()
                hashPrevHeader = lastBlock.hashBlockHeader
                height = lastBlock.height + 1
                merkleRoot = merkle_root_calculator(txnPending)
                nonce = 0
                isMined = False
                self.passNextBlock = False
                time.sleep(self.speedDown)
                while not self.passNextBlock and not isMined:
                    hdr = (merkleRoot + str(nonce) + hashPrevHeader).encode('utf-8')
                    blockHash = hashlib.sha256(hdr).hexdigest()
                    if blockHash.startswith("0" * self.difficulty):
                        self.lock.acquire()
                        self.txnPool = [txn for txn in self.txnPool if txn not in txnPending]
                        self.txnLog.extend(txnPending)
                        currTime = time.localtime()
                        newBlock = Block(hashPrevHeader, merkleRoot, currTime, txnPending, blockHash, nonce, height)
                        self.blockchain.blocks.append(newBlock)

                        nkHeader = GenericMessageHeader(NkMessageTypes.VLD, self, None)
                        nkPayload = newBlock
                        nkEventContent = GenericMessage(nkHeader, nkPayload)
                        nkEvent = Event(self, EventTypes.MFRT, nkEventContent)
                        self.send_down(nkEvent)

                        isMined = True
                        print(f"Component {self.componentinstancenumber}  mined a new block: "
                              f"txn count= {len(self.txnPool)} - block count= {len(self.blockchain.blocks)}\n"
                              f"{self.blockchain.get_last_block().hashPrevHeader}")
                        self.lock.release()
                    else:
                        nonce = nonce + 1

    def search_longest_chain(self):
        self.passNextBlock = True
        print(f"Component {self.componentinstancenumber} is asking for longer chain")
        nk_payload = "asking for longer chain"
        nk_header = GenericMessageHeader(NkMessageTypes.QUERY_LC, self, None)
        nk_eventContent = GenericMessage(nk_header, nk_payload)
        nk_event = Event(self, EventTypes.MFRT, nk_eventContent)
        self.send_down(nk_event)

def main():
    number_of_nodes = 5
    number_of_txn = 50
    G = nx.erdos_renyi_graph(number_of_nodes, 0.4)
    transaction_generator(number_of_nodes,number_of_txn)
    topo = Topology()
    topo.construct_from_graph(G, NkComponent, Channel)

    ComponentRegistry().print_components()
    topo.start()
    nx.draw(G, with_labels=True, font_weight='bold')
    plt.show()

if __name__ == '__main__':
    main()
    while True: pass