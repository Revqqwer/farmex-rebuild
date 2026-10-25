import unittest
from quest_row import QuestRow,QuestRowSink,QuestRowFrame,QuestRowObservation as Observation


def receipts(**changes):
    result={label:True for label,_ in QuestRowFrame.STEPS};result.update(changes)
    return result


class QuestRowTests(unittest.TestCase):
    def test_caption_is_collection_index_and_subitems_are_level_then_display(self):
        sink=QuestRowSink();frame=QuestRowFrame(sink,3,27,b'Gorev')
        plan=frame.advance(Observation(receipts(),1254))
        self.assertTrue(plan.complete)
        self.assertEqual(sink.rows,(QuestRow('3',('27','Gorev')),))
        self.assertFalse(plan.native_execution_verified)

    def test_index_uses_signed_int32_and_minimum_is_unsigned_byte(self):
        sink=QuestRowSink();frame=QuestRowFrame(sink,0xffffffff,255,b'')
        self.assertTrue(frame.advance(Observation(receipts())).complete)
        self.assertEqual(sink.rows,(QuestRow('-1',('255','')),))

    def test_parameter_copy_gap_does_not_create_row(self):
        sink=QuestRowSink();frame=QuestRowFrame(sink,0,1,b'')
        self.assertEqual(frame.advance().needed,('parameter_copy',))
        self.assertEqual(sink.rows,())

    def test_added_row_survives_index_format_gap_and_resume_does_not_duplicate(self):
        sink=QuestRowSink();frame=QuestRowFrame(sink,4,9,b'')
        p=frame.advance(Observation(receipts(index_format=False)))
        self.assertEqual((p.needed,sink.rows),(('index_format',),(QuestRow(),)))
        self.assertTrue(frame.advance(Observation(receipts())).complete)
        self.assertEqual(len(sink.rows),1)
        self.assertEqual(len(frame.calls),len(QuestRowFrame.STEPS))

    def test_each_cleanup_stops_before_next_mutation(self):
        for label,expected in (
            ('caption_cleanup',QuestRow('2')),
            ('level_cleanup',QuestRow('2',('7',))),
            ('display_cleanup',QuestRow('2',('7',''))),
            ('parameter_cleanup',QuestRow('2',('7',''))),
            ('epilogue',QuestRow('2',('7','')))):
            with self.subTest(label=label):
                sink=QuestRowSink();frame=QuestRowFrame(sink,2,7,b'')
                p=frame.advance(Observation(receipts(**{label:False})))
                self.assertFalse(p.complete);self.assertEqual(sink.rows,(expected,))
                self.assertTrue(frame.advance(Observation(receipts())).complete)
                self.assertEqual(sink.rows,(QuestRow('2',('7','')),))

    def test_future_receipts_are_not_consumed_before_reached_call(self):
        sink=QuestRowSink();frame=QuestRowFrame(sink,0,1,b'')
        frame.advance(Observation(receipts(caption_cleanup=False)))
        p=frame.advance(Observation({'caption_cleanup':True}))
        self.assertEqual(p.needed,('level_format',))
        self.assertEqual(sink.rows,(QuestRow('0'),))

    def test_nonempty_display_requires_explicit_codepage_after_known_prefix(self):
        sink=QuestRowSink();frame=QuestRowFrame(sink,0,2,b'\xdd')
        p=frame.advance(Observation(receipts()))
        self.assertEqual(p.needed,('code_page',))
        self.assertEqual(sink.rows,(QuestRow('0',('2',)),))
        p=frame.advance(Observation(receipts(),1254))
        self.assertTrue(p.complete)
        self.assertEqual(sink.rows[0].subitems,('2','\u0130'))

    def test_unknown_codepage_does_not_mean_host_default(self):
        sink=QuestRowSink();frame=QuestRowFrame(sink,0,2,b'x')
        with self.assertRaises(ValueError):frame.advance(Observation(receipts(),0))
        self.assertEqual(sink.rows,(QuestRow('0',('2',)),))
        self.assertTrue(frame.advance(Observation(receipts(),1252)).complete)

    def test_external_row_edit_is_not_overwritten(self):
        sink=QuestRowSink();frame=QuestRowFrame(sink,0,2,b'')
        frame.advance(Observation(receipts(display_add=False)))
        sink.rows=(QuestRow('edited'),)
        self.assertEqual(frame.advance(Observation(receipts())).status,'row_sink_conflict')
        self.assertEqual(sink.rows,(QuestRow('edited'),))

    def test_terminal_result_is_idempotent(self):
        sink=QuestRowSink();frame=QuestRowFrame(sink,0,2,b'')
        p=frame.advance(Observation(receipts()));before=(sink.rows,sink.revision)
        self.assertIs(frame.advance(),p)
        self.assertEqual((sink.rows,sink.revision),before)


if __name__=='__main__':unittest.main()
