import unittest
from dataclasses import replace
from test_quest_action import setup,capture
from test_quest_lookup import capture as lookup_capture
from quest_lookup import QuestLookupObservation


def composed(rows=None):
    return replace(capture(),lookup=lookup_capture([dict(record=0)]*5 if rows is None else rows))


class QuestLookupActionTests(unittest.TestCase):
    def test_take_and_give_use_completed_scan_return_in_first_payload(self):
        for method,count in (('take',3),('give',2)):
            _,frame=setup(method);p=frame.advance(composed())
            self.assertTrue(p.complete);self.assertEqual(len(p.queue.records),count)
            self.assertEqual(p.queue.records[0].payload,b'\x64\x07\xff\xff\0\0')
            self.assertEqual(p.lookup_plan.iteration,5)
            self.assertFalse(p.delivery_verified)

    def test_child_receipts_are_required_before_any_queue_prefix(self):
        _,frame=setup();o=composed();normal=dict(o.lookup.normal_returns)
        del normal[(2,'record')]
        p=frame.advance(replace(o,lookup=replace(o.lookup,normal_returns=normal)))
        self.assertFalse(p.complete);self.assertEqual(p.queue.records,())
        self.assertEqual(p.needed,('lookup','record',5,2,('normal',(2,'record'))))
        p=frame.advance(o);self.assertTrue(p.complete)
        self.assertEqual(len(p.lookup_plan.calls),len({token for _,_,token in p.lookup_plan.calls}))

    def test_argument_cleanup_gap_cannot_be_bypassed_by_raw_return(self):
        _,frame=setup();o=composed();normal=dict(o.lookup.normal_returns)
        del normal[(-1,'argument_cleanup')]
        p=frame.advance(replace(o,lookup=replace(o.lookup,normal_returns=normal)))
        self.assertIsNone(p.lookup_plan.eax);self.assertEqual(p.queue.records,())
        p=frame.advance(capture())
        self.assertFalse(p.complete);self.assertEqual(p.queue.records,())
        self.assertEqual(frame.lookup_mode,'composed')
        self.assertTrue(frame.advance(o).complete)

    def test_completed_child_waits_for_separate_outer_normal_return(self):
        _,frame=setup();o=composed();normal=dict(o.normal_returns);del normal['lookup_eax']
        p=frame.advance(replace(o,normal_returns=normal))
        self.assertTrue(p.lookup_plan.complete);self.assertFalse(p.complete)
        self.assertEqual(p.needed,('normal','lookup_eax'))
        calls=p.lookup_plan.calls
        p=frame.advance(capture())
        self.assertTrue(p.complete);self.assertEqual(p.lookup_plan.calls,calls)
        self.assertEqual(p.queue.records[0].payload[2:4],b'\xff\xff')

    def test_matching_row_does_not_short_circuit_remaining_rows(self):
        _,frame=setup();o=composed([{},dict(record=0),dict(record=0),dict(record=0),dict(record=0)])
        p=frame.advance(o)
        self.assertTrue(p.complete);self.assertEqual(p.lookup_plan.iteration,5)
        self.assertEqual(len(p.lookup_plan.mode_comparisons),1)
        self.assertEqual(frame.lookup_frame.name,b'Quest B')

    def test_inner_mode_is_different_for_take_and_give(self):
        for method,mode in (('take',4),('give',3)):
            _,frame=setup(method);frame.advance(composed())
            self.assertEqual(frame.lookup_frame.mode,mode)
            self.assertEqual((frame.lookup_frame.upper,frame.lookup_frame.iteration),(7,5))

    def test_raw_capture_remains_explicit_and_is_not_reinterpreted_mid_call(self):
        _,frame=setup();o=capture();normal=dict(o.normal_returns);del normal['lookup_eax']
        frame.advance(replace(o,normal_returns=normal))
        self.assertEqual(frame.lookup_mode,'captured')
        p=frame.advance(composed())
        self.assertTrue(p.complete);self.assertIsNone(p.lookup_plan)
        self.assertEqual(p.queue.records[0].payload[2:4],b'\x78\x56')

    def test_lookup_input_is_not_defaulted_when_both_sources_missing(self):
        _,frame=setup();o=capture();values=dict(o.values);del values['lookup_eax']
        p=frame.advance(replace(o,values=values))
        self.assertEqual(p.needed,('lookup_input',));self.assertEqual(p.queue.records,())
        self.assertIsNone(frame.lookup_mode)

    def test_early_give_status_exit_never_consumes_bad_lookup_input(self):
        _,frame=setup('give');o=capture();values=dict(o.values);values['status_eax']=2
        p=frame.advance(replace(o,values=values,lookup=object()))
        self.assertTrue(p.complete);self.assertEqual(p.status,'give_status_not3')
        self.assertIsNone(frame.lookup_frame)

    def test_invalid_nested_capture_is_rejected_without_queue(self):
        _,frame=setup()
        with self.assertRaises(ValueError):frame.advance(replace(capture(),lookup=object()))
        self.assertEqual(frame.queue.records,())


if __name__=='__main__':unittest.main()
