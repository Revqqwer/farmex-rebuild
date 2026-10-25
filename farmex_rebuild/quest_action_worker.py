"""Owned Quest append-prefix publication. No game IO or native equivalence.

The queue writer must synchronously retain an immutable QueueState. Retry may
recognize an already retained candidate and later appends; removals or unrelated
rewrites during an uncertain write require reconciliation rather than guessing.
"""
from dataclasses import dataclass
from action_queue import QueueState, publish_appended_records
from quest_action import QuestActionFrame

TAKE_PATH = 'frmMain/MainTab/sheetQuest/GroupBox53/btnTakeQuest'
GIVE_PATH = 'frmMain/MainTab/sheetQuest/GroupBox53/Button22'
METHODS = {TAKE_PATH: 'take', GIVE_PATH: 'give'}


@dataclass(frozen=True)
class QuestActionContext:
    ticket: int
    generation: int
    method: str
    phase: str
    selected_index: int
    record_index: object
    needed: object


@dataclass(frozen=True)
class QuestActionWorkerResult:
    status: str
    complete: bool = False
    action: object = None
    error: object = None
    published_ids: tuple = ()
    native_execution_verified: bool = False
    delivery_verified: bool = False
    live_compatibility_verified: bool = False

    @property
    def needed(self):
        return self.action.needed if self.action is not None else None


class QuestActionWorker:
    def __init__(self, frame, queue_reader, queue_writer):
        if not isinstance(frame, QuestActionFrame):
            raise ValueError('Typed Quest action frame required')
        if not callable(queue_reader) or not callable(queue_writer):
            raise ValueError('Own shared queue reader and writer required')
        self.frame = frame
        self.reader = queue_reader
        self.writer = queue_writer
        self.published = ()
        self.published_ids = ()
        self.publication = None
        self.action = None
        self.cancelled = False
        self.stepping = False
        self.result = QuestActionWorkerResult('idle')

    def _queue(self):
        queue = self.reader()
        if not isinstance(queue, QueueState):
            raise ValueError('Typed own shared queue required')
        return queue

    def _out(self, status, complete=False, error=None):
        self.result = QuestActionWorkerResult(status, complete, self.action,
                                             error, self.published_ids)
        return self.result

    def cancel(self):
        # Already published prefixes remain. Uncertain publication is never
        # retried after cancellation/profile invalidation.
        self.cancelled = True
        return self._out('cancelled')

    def _flush(self):
        if self.publication is None:
            records = self.frame.queue.records
            if records[:len(self.published)] != self.published:
                raise ValueError('Owned child append prefix changed')
            if len(records) == len(self.published):
                return True
            expected = self._queue()
            candidate, ids, _ = publish_appended_records(expected, records, len(self.published))
            self.publication = (expected, candidate, ids, records)
        expected, candidate, ids, records = self.publication
        current = self._queue()
        retained = (current.next_id >= candidate.next_id and
                    current.records[:len(candidate.records)] == candidate.records)
        if not retained:
            if current != expected:
                self._out('queue_conflict')
                return False
            try:
                self.writer(candidate)
            except (OSError, ValueError) as error:
                self._out('needs_queue_publish', error=str(error))
                return False
            if self.cancelled:
                return False
            current = self._queue()
            if not (current.next_id >= candidate.next_id and
                    current.records[:len(candidate.records)] == candidate.records):
                self._out('needs_queue_publish', error='Writer did not retain candidate')
                return False
        self.published = records
        self.published_ids += ids
        self.publication = None
        return True

    def advance(self, observation=None):
        if self.cancelled:
            return self._out('cancelled')
        if self.stepping:
            return self.result
        self.stepping = True
        try:
            # Resolve an uncertain prior write before consuming more observations.
            if not self._flush():
                return self.result
            try:
                self.action = self.frame.advance(observation)
            except (OSError, ValueError) as error:
                # The frame may already have appended an observed prefix.
                if not self._flush():
                    return self.result
                return self._out('needs_observation', error=str(error))
            if not self._flush():
                return self.result
            return self._out(self.action.status, self.action.complete)
        finally:
            self.stepping = False
