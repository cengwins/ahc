import logging
import statistics
import sys
import threading
from ahc.Consensus.Raft.log import LogManager

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

logger = logging.getLogger(__name__)

class State:
    

    def __init__(self, old_state=None, server=None):

        if old_state:
            self.server = old_state.server
            self.votedFor = old_state.votedFor
            self.currentTerm = old_state.currentTerm
            self.leaderId = old_state.leaderId
            self.log = old_state.log
        else:
            self.server = server
            self.votedFor = None
            self.currentTerm = 0
            self.leaderId = None
            self.log = LogManager()

    def data_received_peer(self, peer, msg):

        logger.debug('For component %s Received %s from %s', msg['type'], self.server.componentinstancenumber ,peer.componentinstancenumber)

        if self.currentTerm < msg['term']:
            self.currentTerm = msg['term']
            if not type(self) is Follower:
                logger.info('For component %s Remote term is higher, converting to Follower', self.server.componentinstancenumber)
                self.server.change_state(Follower)
                self.server.state.data_received_peer(peer, msg)
                return
        method = getattr(self, 'on_peer_' + msg['type'], None)
        if method:
            method(peer, msg)
        else:
            logger.info('For component %s Unrecognized message from %s: %s', self.server.componentinstancenumber,peer.componentinstancenumber, msg)

    def data_received_client(self, client, msg):

        method = getattr(self, 'on_client_' + msg['type'], None)
        if method:
            method(client, msg)

    def on_client_append(self, client, msg):
        
        msg = {'type': 'redirect',
               'leader': self.leaderId}
        client.send(msg)
        logger.debug('Redirect client %s to leader',
                     self.leaderId)

    def on_client_get(self, client, msg):
        
        client.send(self.log)


class Follower(State):
    

    def __init__(self, old_state=None, server=None):
        
        super().__init__(old_state, server)
        self.votedFor = None
        self.restart_election_timer()

    def teardown(self):
        
        self.election_timer.cancel()

    def restart_election_timer(self):
        
        if hasattr(self, 'election_timer'):
            self.election_timer.cancel()

        timeout = ord(self.server.componentinstancenumber) - ord('A') + 1
        #loop = get_or_create_eventloop()
        #self.election_timer = loop. \
        #    call_later(timeout, self.server.change_state, Candidate)
        self.election_timer = threading.Timer(timeout, self.server.change_state, (Candidate,))
        self.election_timer.start()
        logger.debug(' For component %s Election timer restarted: %s s', self.server.componentinstancenumber,timeout)

    def on_peer_request_vote(self, peer, msg):
        
        term_is_current = msg['term'] >= self.currentTerm
        can_vote = self.votedFor is None
        index_is_current = (msg['lastLogTerm'] > self.log.term() or
                            (msg['lastLogTerm'] == self.log.term() and
                             msg['lastLogIndex'] >= self.log.index))
        granted = term_is_current and can_vote and index_is_current

        if granted:
            self.votedFor = msg['candidateId']
            self.restart_election_timer()

        logger.debug('For component %s Voting for %s. Term:%s Vote:%s Index:%s', self.server.componentinstancenumber,
                     peer.componentinstancenumber, term_is_current, can_vote, index_is_current)

        response = {'type': 'response_vote', 'voteGranted': granted,
                    'term': self.currentTerm}
        self.server.send_to_component(peer, response)

    def on_peer_append_entries(self, peer, msg):

        self.restart_election_timer()

        term_is_current = msg['term'] >= self.currentTerm
        prev_log_term_match = msg['prevLogTerm'] is None or \
                              self.log.term(msg['prevLogIndex']) == msg['prevLogTerm']
        success = term_is_current and prev_log_term_match

        if success:
            self.log.append_entries(msg['entries'], msg['prevLogIndex'])
            self.log.commit(msg['leaderCommit'])
            self.leaderId = msg['leaderId']
            logger.debug('For component %s Log index is now %s', self.server.componentinstancenumber, self.log.index)
        else:
            logger.warning('For component %s Could not append entries. cause: %s', self.server.componentinstancenumber,
                           'wrong\
                term' if not term_is_current else 'prev log term mismatch')

        resp = {'type': 'response_append', 'success': success,
                'term': self.currentTerm,
                'matchIndex': self.log.index}
        self.server.send_to_component(peer, resp)


class Candidate(Follower):
    

    def __init__(self, old_state=None, server=None):
        
        super().__init__(old_state, server)
        self.currentTerm += 1
        self.votes_count = 0
        logger.info('New Election. Term: %s', self.currentTerm)
        #TODO: put it in seperate thread
        def vote_self():
            self.votedFor = self.server.componentinstancenumber
            self.on_peer_response_vote(
                self.votedFor, {'voteGranted': True})

        vote_self()
        self.send_vote_requests()



    def send_vote_requests(self):
        
        logger.info(' For component %s Broadcasting request_vote', self.server.componentinstancenumber)
        msg = {'type': 'request_vote', 'term': self.currentTerm,
               'candidateId': self.votedFor,
               'lastLogIndex': self.log.index,
               'lastLogTerm': self.log.term()}
        self.server.broadcast_peers(msg)

    def on_peer_append_entries(self, peer, msg):
        
        logger.debug('For component %s Converting to Follower', self.server.componentinstancenumber)
        self.server.change_state(Follower)
        self.server.state.on_peer_append_entries(peer, msg)

    def on_peer_response_vote(self, peer, msg):
        
        self.votes_count += msg['voteGranted']
        logger.info(' For component %s Vote count: %s', self.server.componentinstancenumber, self.votes_count)
        if self.votes_count > len(self.server.registry.get_non_channel_components()) / 2:
            self.server.change_state(Leader)


class Leader(State):
    

    def __init__(self, old_state=None, server=None):

        super().__init__(old_state, server)
        logger.info('For component %s Leader of term: %s', self.server.componentinstancenumber,self.currentTerm)
        self.leaderId = self.server.componentinstancenumber
        cluster = self.server.registry.get_non_channel_components()
        cluster_names = [c.componentinstancenumber for c in cluster]
        self.matchIndex = {p: 0 for p in cluster_names}
        self.nextIndex = {p: self.log.commitIndex + 1 for p in self.matchIndex}
        self.waiting_clients = {}
        self.send_append_entries()

        self.log.append_entries([{'term': self.currentTerm,
                                  'data': {
                                      'key': 'leaderId',
                                      'value': self.server.componentinstancenumber,
                                      }}],
                                self.log.index)
        self.log.commit(self.log.index)

    def teardown(self):
        
        self.append_timer.cancel()

        for clients in self.waiting_clients.values():
            for client in clients:
                client.send({'type': 'result', 'success': False})
                logger.error('Sent unsuccessful response to client')

    def send_append_entries(self):

        cluster = self.server.registry.get_non_channel_components()
        for peer in cluster:
            if peer.componentinstancenumber == self.server.componentinstancenumber:
                continue
            msg = {'type': 'append_entries',
                   'term': self.currentTerm,
                   'leaderCommit': self.log.commitIndex,
                   'leaderId': self.server.componentinstancenumber,
                   'prevLogIndex': self.nextIndex[peer.componentinstancenumber] - 1,
                   'entries': self.log.log
                   }
            msg.update({'prevLogTerm': self.log.term(msg['prevLogIndex'])})

            logger.debug(' For component %s Sending %s entries to %s. Start index %s',self.server.componentinstancenumber,
                         len(msg['entries']), peer.componentinstancenumber, self.nextIndex[peer.componentinstancenumber])
            self.server.send_to_component(peer, msg)

        timeout = 1
        #loop = get_or_create_eventloop()
        #self.append_timer = loop.call_later(timeout, self.send_append_entries)
        self.append_timer = threading.Timer(timeout, self.send_append_entries)
        self.append_timer.start()

    def on_peer_response_append(self, peer, msg):

        if msg['success']:
            self.matchIndex[peer] = msg['matchIndex']
            self.nextIndex[peer] = msg['matchIndex'] + 1

            self.matchIndex[self.server.componentinstancenumber] = self.log.index
            self.nextIndex[self.server.componentinstancenumber] = self.log.index + 1
            index = statistics.median_low(self.matchIndex.values())
            self.log.commit(index)
            self.send_client_append_response()
        else:
            self.nextIndex[peer.componentinstancenumber] = max(0, self.nextIndex[peer.componentinstancenumber] - 1)

    def on_client_append(self, client, msg):
        
        entry = {'term': self.currentTerm, 'data': msg['data']}

        self.log.append_entries([entry], self.log.index)
        if self.log.index in self.waiting_clients:
            self.waiting_clients[self.log.index].append(client)
        else:
            self.waiting_clients[self.log.index] = [client]
        self.on_peer_response_append(
            self.server.componentinstancenumber, {'success': True,
                                       'matchIndex': self.log.commitIndex})

    def send_client_append_response(self):
        
        to_delete = []
        for client_index, clients in self.waiting_clients.items():
            if client_index <= self.log.commitIndex:
                for client in clients:
                    client.send({'type': 'result', 'success': True})  # TODO
                    logger.debug('Sent successful response to client')
                to_delete.append(client_index)
        for index in to_delete:
            del self.waiting_clients[index]
