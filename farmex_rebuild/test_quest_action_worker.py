import unittest
from dataclasses import replace
from action_queue import QueueState, enqueue
from quest_action_worker import QuestActionWorker
from test_quest_action import setup, capture


class QuestActionWorkerTests(unittest.TestCase):
    def worker(self, method='take'):
        _, frame = setup(method)
        box = [QueueState()]
        writes = []
        def write(queue):
            writes.append(queue)
            box[0] = queue
        return QuestActionWorker(frame, lambda: box[0], write), box, writes

    def test_complete_take_and_give_publish_and_do_not_repeat(self):
        for method, count in (('take', 3), ('give', 2)):
            worker, box, writes = self.worker(method)
            result = worker.advance(capture())
            self.assertTrue(result.complete)
            self.assertEqual(result.published_ids, tuple(range(1, count+1)))
            self.assertEqual(box[0].records, worker.frame.queue.records)
            worker.advance(capture())
            self.assertEqual(len(writes), 1)
            self.assertFalse(result.delivery_verified)

    def test_prefix_published_before_missing_outer_return(self):
        worker, box, writes = self.worker()
        observation = capture()
        normal = dict(observation.normal_returns)
        del normal[('enqueue', 0)]
        result = worker.advance(replace(observation, normal_returns=normal))
        self.assertFalse(result.complete)
        self.assertEqual(len(box[0].records), 1)
        worker.advance(capture())
        self.assertEqual(len(box[0].records), 3)
        self.assertEqual([r.record_id for r in box[0].records], [1, 2, 3])

    def test_failure_before_write_retries_candidate_before_frame_progress(self):
        worker, box, writes = self.worker()
        normal_writer = worker.writer
        worker.writer = lambda queue: (_ for _ in ()).throw(OSError('offline'))
        result = worker.advance(capture())
        self.assertEqual(result.status, 'needs_queue_publish')
        self.assertFalse(result.complete)
        self.assertEqual(box[0], QueueState())
        worker.writer = normal_writer
        self.assertTrue(worker.advance().complete)
        self.assertEqual(len(writes), 1)

    def test_failure_after_write_does_not_duplicate(self):
        worker, box, writes = self.worker()
        def write(queue):
            writes.append(queue)
            box[0] = queue
            raise OSError('after commit')
        worker.writer = write
        self.assertFalse(worker.advance(capture()).complete)
        self.assertTrue(worker.advance().complete)
        self.assertEqual(len(writes), 1)
        self.assertEqual(len(box[0].records), 3)

    def test_interleaved_append_after_uncertain_commit_is_preserved(self):
        worker, box, writes = self.worker()
        def write(queue):
            writes.append(queue)
            box[0] = enqueue(queue, b'other', 5, 0, 1, 99).state
            raise OSError('after commit and interleave')
        worker.writer = write
        worker.advance(capture())
        self.assertTrue(worker.advance().complete)
        self.assertEqual(len(writes), 1)
        self.assertEqual(box[0].records[-1].payload, b'other')

    def test_conflicting_change_during_uncertain_write_is_not_overwritten(self):
        worker, box, writes = self.worker()
        worker.writer = lambda queue: (_ for _ in ()).throw(OSError('offline'))
        worker.advance(capture())
        box[0] = enqueue(box[0], b'other', 5, 0, 1, 99).state
        self.assertEqual(worker.advance().status, 'queue_conflict')
        self.assertEqual(len(box[0].records), 1)
        self.assertEqual(box[0].records[0].payload, b'other')

    def test_noop_writer_never_claims_complete(self):
        worker, box, writes = self.worker()
        worker.writer = lambda queue: None
        self.assertEqual(worker.advance(capture()).status, 'needs_queue_publish')
        self.assertEqual(box[0], QueueState())

    def test_cancel_does_not_retry_uncertain_write(self):
        worker, box, writes = self.worker()
        worker.writer = lambda queue: (_ for _ in ()).throw(OSError('offline'))
        worker.advance(capture())
        worker.cancel()
        worker.writer = lambda queue: self.fail('Cancelled writer called')
        self.assertEqual(worker.advance().status, 'cancelled')
        self.assertEqual(box[0], QueueState())

    def test_existing_shared_records_and_ids_are_preserved(self):
        worker, box, writes = self.worker()
        box[0] = enqueue(box[0], b'prior', 5, 0, 1, 99).state
        result = worker.advance(capture())
        self.assertEqual(result.published_ids, (2, 3, 4))
        self.assertEqual(box[0].records[0].payload, b'prior')

    def test_reentrant_writer_does_not_advance_frame_again(self):
        worker, box, writes = self.worker()
        def write(queue):
            worker.advance(capture())
            writes.append(queue)
            box[0] = queue
        worker.writer = write
        self.assertTrue(worker.advance(capture()).complete)
        self.assertEqual(len(writes), 1)

    def test_no_selection_produces_no_queue_write(self):
        worker, box, writes = self.worker()
        worker.frame.selected = -1
        self.assertTrue(worker.advance(capture()).complete)
        self.assertEqual(writes, [])


if __name__ == '__main__':
    unittest.main()
