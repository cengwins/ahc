import logging

logger = logging.getLogger(__name__)


class LogManager:
    """Instantiate and manage the components of the "Log" subsystem.
    That is: the log, the compactor and the state machine."""

    def __init__(self):
        self.log = []
        self.commitIndex = len(self.log)

    def __getitem__(self, index):
        """Get item or slice from the log, based on absolute log indexes.
        Item(s) already compacted cannot be requested."""
        if type(index) is slice:
            start = index.start
            stop = index.stop
            return self.log[start:stop:index.step]
        elif type(index) is int:
            return self.log[index]

    @property
    def index(self):
        """Log tip index."""
        return len(self.log)

    def term(self, index=None):
        """Return a term given a log index. If no index is passed, return
        log tip term."""
        if index is None:
            return self.term(self.index)
        elif index == -1:
            return 0
        elif not len(self.log):
            return 0
        else:
            return self.log[index]['term']

    def append_entries(self, entries, prevLogIndex):
        start = prevLogIndex
        if len(self.log) >= start:
            del self.log[:start]
            self.log.extend(entries)
        else:
            self.log.extend(entries)
        if entries:
            logger.debug('Appending. New log: %s', self.log)

    def commit(self, leaderCommit):
        if leaderCommit <= self.commitIndex:
            return

        self.commitIndex = min(leaderCommit, self.index)  # no overshoots
        logger.debug('Advancing commit to %s', self.commitIndex)
        # above is the actual commit operation, just incrementing the counter!
