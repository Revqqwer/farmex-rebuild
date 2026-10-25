import unittest
from message_list_delete import *

def empty():
    return MessageListObservation(True,{'row0.count_eax':0},
        {k:True for k in ('clear_end_iterator','clear_begin_iterator','clear_range','row0.count')})

class MessageListDeleteTests(unittest.TestCase):
    def test_correct_slots_and_no_compile_when_gate_zero(self):
        for action,slot,method,end in (('selected',0x148,'DeleteSelected',0x4b14d7),('clear',0x13c,'Clear',0x4b150f)):
            p=MessageListDeleteFrame(action).advance(MessageListDeleteObservation(True,True,0))
            self.assertTrue(p.complete);self.assertIsNone(p.producer);self.assertEqual(p.next_address,end)
            self.assertEqual(p.calls,(('VCL_TCustomListView_'+method,(LIST_PATH,slot),'ui_mutation'),))

    def test_ui_mutation_happens_before_even_zero_gate_is_accepted(self):
        frame=MessageListDeleteFrame('clear')
        p=frame.advance(MessageListDeleteObservation(True,False,0,empty(),True))
        self.assertEqual(p.needed,('normal','mutation_returned'));self.assertIsNone(frame.observation.compile_gate_byte)
        p=frame.advance(MessageListDeleteObservation(mutation_returned=True,compile_gate_byte=1))
        self.assertEqual(p.needed,('producer',('entry','0045c499')))

    def test_nonzero_raw_gate_uses_typed_child_and_parent_independently(self):
        for gate in (1,2,255):
            frame=MessageListDeleteFrame('selected')
            p=frame.advance(MessageListDeleteObservation(True,True,gate,empty()))
            self.assertTrue(p.producer.complete);self.assertFalse(p.complete)
            self.assertEqual(p.needed,('normal','producer_parent_returned'))
            p=frame.advance(MessageListDeleteObservation(producer_parent_returned=True))
            self.assertTrue(p.complete);self.assertEqual(len(p.calls),2)

    def test_parent_return_cannot_skip_incomplete_child(self):
        frame=MessageListDeleteFrame('selected')
        p=frame.advance(MessageListDeleteObservation(True,True,1,producer_parent_returned=True))
        self.assertEqual(p.needed,('producer',('entry','0045c499')))
        self.assertIsNone(frame.observation.producer_parent_returned)
        p=frame.advance(MessageListDeleteObservation(producer=empty()))
        self.assertEqual(p.needed,('normal','producer_parent_returned'))

    def test_accepted_gate_does_not_change_during_later_child_wait(self):
        frame=MessageListDeleteFrame('clear')
        frame.advance(MessageListDeleteObservation(True,True,1))
        p=frame.advance(MessageListDeleteObservation(compile_gate_byte=0,producer=empty(),producer_parent_returned=True))
        self.assertTrue(p.complete);self.assertIsNotNone(p.producer)
        self.assertEqual(frame.observation.compile_gate_byte,1)

    def test_entry_required_and_incoming_early_fields_not_consumed(self):
        frame=MessageListDeleteFrame('selected')
        p=frame.advance(MessageListDeleteObservation(mutation_returned=True,compile_gate_byte=1))
        self.assertEqual(p.needed,('entry','004b14b0'));self.assertIsNone(frame.observation.mutation_returned)

    def test_completed_callback_does_not_repeat_mutation_or_compilation(self):
        frame=MessageListDeleteFrame('clear')
        p=frame.advance(MessageListDeleteObservation(True,True,1,empty(),True))
        self.assertTrue(p.complete);self.assertTrue(p.producer.cleared)
        self.assertIs(frame.advance(MessageListDeleteObservation(True,True,0)),p)

    def test_native_effect_not_inferred_from_normal_receipt(self):
        p=MessageListDeleteFrame('selected').advance(MessageListDeleteObservation(True,True,0))
        self.assertFalse(p.native_mutation_verified);self.assertFalse(p.native_execution_verified)
        self.assertFalse(p.whole_function_verified);self.assertFalse(p.live_compatibility_verified)
        with self.assertRaises(ValueError):MessageListDeleteFrame('all')
        for kw in ({'compile_gate_byte':256},{'compile_gate_byte':True},{'producer':{}},{'mutation_returned':1}):
            with self.assertRaises(ValueError):MessageListDeleteObservation(**kw)

if __name__=='__main__':unittest.main()
