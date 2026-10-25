import unittest
from session_status_wire import FIELDS
from session_status_selection import (SessionSelectionObservation as O,SessionSelectionFrame,
    SessionSourceWireFrame,select_session_fields)

class SessionStatusSelectionTests(unittest.TestCase):
    def values(self,**extra):
        v=dict(exclusive_byte=0,mode0=0,special_initial_byte=0,connection_eax=1,
               bot_byte=0,special_fresh_byte=0);v.update(extra);return v
    def plan(self,**extra):return select_session_fields(O(self.values(**extra),{'connection':True},True))
    def source(self,denominator=3):
        derived={'ratio_division_eax','exclusive_byte','mode_byte','status_byte'}
        return SessionSourceWireFrame({k:0 for k in FIELDS if k not in derived},b'',numerator=1,denominator=denominator)

    def test_fresh_mode_reads_and_first_match_short_circuit(self):
        for index in range(4):
            v=self.values()
            for i in range(index):v['mode%d'%i]=99
            v['mode%d'%index]=index
            p=SessionSelectionFrame().advance(O(v,{'connection':True},True))
            self.assertTrue(p.complete);self.assertEqual(p.fields['mode_byte'],index+1)
            self.assertEqual([r[2] for r in p.reads if r[0]==0x561f58],['mode%d'%i for i in range(index+1)])

    def test_no_matching_mode_is_ff_and_not_last_observed_value(self):
        p=self.plan(mode0=4,mode1=4,mode2=4,mode3=4)
        self.assertTrue(p.complete);self.assertEqual(p.fields['mode_byte'],255)

    def test_initial_special_read_is_required_before_connection_call(self):
        v=self.values();del v['special_initial_byte']
        p=select_session_fields(O(v,{'connection':True},True))
        self.assertEqual(p.needed,('value','special_initial_byte'));self.assertEqual(p.calls,())

    def test_normal_helper_receipt_precedes_eax_and_branch_reads(self):
        f=SessionSelectionFrame();p=f.advance(O(self.values(bot_byte=255),{},True))
        self.assertEqual(p.needed,('normal','connection'))
        self.assertNotIn('bot_byte',f.observation.values)
        p=f.advance(O({'connection_eax':0,'special_fresh_byte':1},{'connection':True}))
        self.assertTrue(p.complete);self.assertEqual(p.fields['status_byte'],0x33)
        self.assertNotIn('bot_byte',f.observation.values)

    def test_full_connection_eax_must_equal_exactly_one(self):
        for value in (0,2,0x101,0x10000001,0xffffffff):
            p=self.plan(connection_eax=value)
            self.assertEqual(p.fields['status_byte'],10)
            self.assertFalse(any(r[0]==0x561f60 for r in p.reads))

    def test_status_branch_matrix(self):
        for connected,bot,secondary,special,expected in (
            (0,0,0,0,10),(0,0,0,1,0x33),
            (1,0,0,0,9),(1,0,0,1,0x35),
            (1,1,0,0,2),(1,1,0,1,0x34),
            (1,1,1,0,1),(1,1,1,1,1)):
            p=self.plan(connection_eax=connected,bot_byte=bot,secondary_byte=secondary,special_fresh_byte=special)
            self.assertTrue(p.complete);self.assertEqual(p.fields['status_byte'],expected)

    def test_secondary_active_skips_fresh_special_read(self):
        v=self.values(bot_byte=128,secondary_byte=255,exclusive_byte=128);del v['special_fresh_byte']
        p=SessionSelectionFrame().advance(O(v,{'connection':True},True))
        self.assertTrue(p.complete);self.assertEqual(dict(p.fields),dict(exclusive_byte=1,mode_byte=1,status_byte=1))
        self.assertEqual([r[2] for r in p.reads if r[0]==0x56209c],['special_initial_byte'])

    def test_consumed_prefix_and_terminal_selection_are_preserved(self):
        f=SessionSelectionFrame();p=f.advance(O(self.values(),{},True))
        self.assertEqual(p.needed,('normal','connection'))
        p=f.advance(O(self.values(exclusive_byte=1,mode0=4,special_initial_byte=1,
                                connection_eax=0,special_fresh_byte=128),{'connection':True}))
        self.assertEqual(dict(p.fields),dict(exclusive_byte=0,mode_byte=1,status_byte=0x33))
        self.assertIs(f.advance(O(self.values(),{'connection':True})),p)

    def test_entry_and_input_shapes(self):
        p=select_session_fields(O(self.values(),{'connection':True}))
        self.assertEqual(p.reads,());self.assertEqual(p.calls,())
        with self.assertRaises(ValueError):O({'exclusive_byte':True})
        with self.assertRaises(ValueError):O({'exclusive_byte':256})
        with self.assertRaises(ValueError):O({'unrecognized':0})
        with self.assertRaises(ValueError):O({}, {'connection':1})
        p=self.plan()
        with self.assertRaises(TypeError):p.fields['mode_byte']=7

    def test_ratio_fault_blocks_all_selector_reads(self):
        f=self.source(0);p=f.advance(O(self.values(),{'connection':True},True),transform_length_word=42)
        self.assertFalse(p.complete);self.assertIsNone(p.selection);self.assertIsNone(p.wire)
        self.assertEqual(dict(f.selector.observation.values),{})

    def test_compound_keeps_selector_across_serialization_gaps(self):
        f=self.source();o=O(self.values(exclusive_byte=255),{'connection':True},True)
        p=f.advance(o);self.assertFalse(p.complete);self.assertTrue(p.selection.complete)
        self.assertEqual(p.wire.length_word,42)
        p=f.advance(O(),transform_length_word=42)
        self.assertTrue(p.complete);self.assertEqual(p.wire.plain_frame[7:9],bytes([1,9]))
        self.assertEqual(p.wire.plain_frame[12],33);self.assertEqual(p.wire.plain_frame[39],1)
        self.assertIs(f.advance(O(),transform_length_word=43),p)
        self.assertFalse(p.full_builder_verified or p.native_execution_verified or p.live_compatibility_verified)

    def test_compound_rejects_independent_derived_fields(self):
        values={k:0 for k in FIELDS}
        with self.assertRaises(ValueError):SessionSourceWireFrame(values,b'',numerator=1,denominator=3)

if __name__=='__main__':unittest.main()
