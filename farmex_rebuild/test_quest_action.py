import unittest,struct
from dataclasses import replace
from quest_collection import QuestCollection
from quest_record import QuestRecord
from quest_row import QuestRow
from quest_action import QuestActionFrame,QuestActionObservation as Observation


def rec(script=b'q',**changes):
    r=QuestRecord(7,0x4000,script,257,5,b'Quest B',b'NPC B')
    return replace(r,**changes)


def setup(method='take',script=b'q',selected=0,caption='1',owned=True):
    c=QuestCollection((rec(b'wrong',source_index=99,npc_bytes=b'Wrong'),rec(script)))
    f=QuestActionFrame(method,c,(QuestRow(caption),),selected,
        use_owned_scalar_model=owned,use_owned_cstring_model=owned,use_owned_float_model=owned)
    return c,f


def f32(value):return struct.unpack('<I',struct.pack('<f',value))[0]


def capture(**changes):
    labels=('selection','caption','caption_parse','caption_cleanup','npc_cpp','npc_id','npc_pointer',
        'coord_a','coord_b','distance_bits','current_target','retarget','prepare','data20','status',
        'data1c_unused','lookup_eax','first_copy','script_cpp','opcode','zero','length','script_copy',
        'terminal','script_cleanup','epilogue')
    normal={label:True for label in labels};normal.update({('enqueue',i):True for i in range(3)})
    values=dict(npc_id=0x1004,npc_pointer=0x2000,coord_a_offset=0x10,coord_b_offset=0x20,
                coord_a_bits=f32(1),coord_b_bits=f32(2),distance_bits=f32(5),current_target=0x1004,
                data20=777,status_eax=3,lookup_eax=0x12345678)
    fields=dict(values=values,normal_returns=normal,enqueue_gates={i:1 for i in range(3)},enqueue_ticks={0:10,1:20,2:30},enqueue_prefix_returns={i:True for i in range(3)})
    fields.update(changes);return Observation(**fields)


class QuestActionTests(unittest.TestCase):
    def test_take_three_exact_requests_and_independent_ticks(self):
        c,f=setup();p=f.advance(capture())
        self.assertTrue(p.complete);self.assertEqual(p.record_index,1)
        self.assertEqual([r.payload for r in p.queue.records],[b'\x64\x07\x78\x56\0\0',b'\x55\0\x01q',b'\x55\0\x01q\xff'])
        self.assertEqual([r.delay_dword for r in p.queue.records],[500,1000,1500])
        self.assertEqual([r.created_tick for r in p.queue.records],[10,20,30])
        self.assertFalse(p.delivery_verified);self.assertFalse(p.live_compatibility_verified)

    def test_give_two_requests_status_low_byte_and_terminal02(self):
        c,f=setup('give');o=capture();values=dict(o.values);values['status_eax']=0x10000003
        p=f.advance(replace(o,values=values));self.assertTrue(p.complete)
        self.assertEqual([r.payload for r in p.queue.records],[b'\x64\x07\x78\x56\0\0',b'\x55\0\x01q\x02'])
        self.assertEqual([r.delay_dword for r in p.queue.records],[1000,2000])
        self.assertEqual(len(p.queue_calls),2)

    def test_give_non3_exits_after_prepare_but_before_unused_read_and_lookup(self):
        c,f=setup('give');o=capture();values=dict(o.values);values['status_eax']=2
        p=f.advance(replace(o,values=values))
        self.assertEqual((p.complete,p.status,len(p.queue.records)),(True,'give_status_not3',0))
        self.assertIn('prepare',[label for _,label,_ in p.calls])
        self.assertNotIn('data1c_unused',[label for _,label,_ in p.calls])

    def test_take_does_not_require_unused_status_eax(self):
        c,f=setup();o=capture();values=dict(o.values);values['status_eax']=object()
        self.assertTrue(f.advance(replace(o,values=values)).complete)

    def test_lookup_mode_and_wrapping_lower_bound_are_different_for_each_action(self):
        for method,mode in (('take',4),('give',3)):
            c,f=setup(method);c.records=(c.records[0],rec(source_index=2))
            p=f.advance(capture())
            args=next(args for helper,label,args in p.calls if label=='lookup_eax')
            self.assertEqual(args,('owned_quest_context',b'Quest B',mode,0xfffffffe,2))

    def test_zero_lookup_identifier_is_not_an_exit_condition(self):
        c,f=setup();o=capture();values=dict(o.values);values['lookup_eax']=0
        p=f.advance(replace(o,values=values));self.assertTrue(p.complete)
        self.assertEqual(p.queue.records[0].payload,b'\x64\x07\0\0\0\0')

    def test_negative_selection_skips_every_lookup(self):
        c,f=setup(selected=-1)
        p=f.advance(Observation(normal_returns={'selection':True,'epilogue':True}))
        self.assertEqual((p.complete,p.status,len(p.queue.records)),(True,'no_selection',0))
        self.assertEqual(len(p.calls),2)

    def test_invalid_caption_and_outside_record_never_become_record_zero(self):
        for text,status in (('bad','needs_native_StrToInt_exception_path'),('-1','needs_observation')):
            c,f=setup(caption=text);p=f.advance(capture())
            self.assertEqual(p.status,status);self.assertEqual(p.queue.records,())
            self.assertNotIn('npc_id',[label for _,label,_ in p.calls])

    def test_npc_id_or_pointer_zero_shortcircuits_unreached_values(self):
        for key,status in (('npc_id','npc_not_found'),('npc_pointer','npc_pointer_missing')):
            c,f=setup();o=capture();values=dict(o.values);values[key]=0;values['distance_bits']=object()
            p=f.advance(replace(o,values=values))
            self.assertEqual((p.complete,p.status,p.queue.records),(True,status,()))

    def test_float32_boundaries_negative_zero_nan_and_infinity(self):
        for distance,allowed in ((0,True),(-0.0,True),(10,True),(10.000001,False),(-.001,False),(float('nan'),False),(float('inf'),False)):
            with self.subTest(distance=distance):
                c,f=setup();o=capture();values=dict(o.values);values['distance_bits']=f32(distance)
                p=f.advance(replace(o,values=values));self.assertTrue(p.complete)
                self.assertEqual(p.status,'locally_prepared' if allowed else 'out_of_range')

    def test_captured_fpu_outcome_and_cpp_results_are_explicit_in_default_mode(self):
        c,f=setup(owned=False);o=capture();values=dict(o.values)
        values.update(record_index=1,npc_cpp_bytes=b'NPC B',script_cpp_bytes=b'a\0b',
                      distance_lower_reject=False,distance_upper_reject=False)
        p=f.advance(replace(o,values=values));self.assertTrue(p.complete)
        self.assertEqual(p.queue.records[1].payload,b'\x55\0\x03a\0b')

    def test_own_cstring_mode_uses_nul_terminated_script_not_storage_dword(self):
        c,f=setup(script=b'ab\0ignored');p=f.advance(capture())
        self.assertEqual(p.queue.records[1].payload,b'\x55\0\x02ab')
        self.assertNotEqual(c.records[1].script_storage_dword,2)

    def test_length_low_byte_wrap_does_not_truncate_copied_script(self):
        c,f=setup(script=b'x'*256);p=f.advance(capture())
        self.assertEqual(p.queue.records[1].payload,b'\x55\0\0'+b'x'*256)

    def test_retarget_receives_pointer_not_lookup_id(self):
        c,f=setup();o=capture();values=dict(o.values);values['current_target']=0
        p=f.advance(replace(o,values=values))
        self.assertEqual(next(args for _,label,args in p.calls if label=='retarget'),(0x2000,))

    def test_normal_return_gaps_do_not_repeat_effect_requests(self):
        c,f=setup();o=capture();values=dict(o.values);values['current_target']=0
        normal=dict(o.normal_returns);normal['retarget']=False
        p=f.advance(replace(o,values=values,normal_returns=normal))
        self.assertEqual(p.needed,('normal','retarget'));self.assertEqual(p.queue.records,())
        p=f.advance(replace(o,values=values));self.assertTrue(p.complete)
        self.assertEqual(sum(label=='retarget' for _,label,_ in p.calls),1)

    def test_queue_prefix_is_visible_before_outer_helper_return_and_not_duplicated(self):
        c,f=setup();o=capture();normal=dict(o.normal_returns);normal[('enqueue',0)]=False
        p=f.advance(replace(o,normal_returns=normal))
        self.assertEqual(p.needed,('normal',('enqueue',0)));self.assertEqual(len(p.queue.records),1)
        p=f.advance(o);self.assertTrue(p.complete)
        self.assertEqual([r.record_id for r in p.queue.records],[1,2,3])

    def test_gate_capture_freezes_while_tick_is_missing(self):
        c,f=setup();o=capture();p=f.advance(replace(o,enqueue_ticks={1:20,2:30}))
        self.assertEqual(p.needed,('enqueue_tick',0));self.assertEqual(p.queue.records,())
        p=f.advance(replace(o,enqueue_gates={0:0,1:1,2:1}))
        self.assertTrue(p.complete);self.assertEqual(p.queue.records[0].created_tick,10)

    def test_each_gate_is_fresh_and_zero_gate_skips_its_clock(self):
        c,f=setup();o=capture();p=f.advance(replace(o,enqueue_gates={0:0,1:1,2:1},enqueue_ticks={0:object(),1:20,2:30}))
        self.assertTrue(p.complete);self.assertEqual(len(p.queue.records),2)
        self.assertEqual(p.queue_calls[0][-1],'not_enqueued')
        self.assertEqual([r.created_tick for r in p.queue.records],[20,30])

    def test_clock_is_frozen_while_queue_append_span_is_unknown(self):
        c,f=setup();o=capture();p=f.advance(replace(o,enqueue_prefix_returns={1:True,2:True}))
        self.assertEqual(p.needed,('enqueue_append_span',0));self.assertEqual(p.queue.records,())
        p=f.advance(replace(o,enqueue_ticks={0:99,1:20,2:30}))
        self.assertTrue(p.complete);self.assertEqual(p.queue.records[0].created_tick,10)

    def test_data_pointer_is_fresh_after_status_gap(self):
        c,f=setup();o=capture();normal=dict(o.normal_returns);normal['status']=False
        f.advance(replace(o,normal_returns=normal));c.records=(c.records[0],rec(data_pointer_dword=0x6000))
        p=f.advance(o)
        self.assertEqual(next(args for _,label,args in p.calls if label=='data20'),(0x4020,))
        self.assertEqual(next(args for _,label,args in p.calls if label=='data1c_unused'),(0x601c,))

    def test_script_is_read_after_first_queue_call_returns(self):
        c,f=setup();o=capture();normal=dict(o.normal_returns);normal[('enqueue',0)]=False
        f.advance(replace(o,normal_returns=normal));c.records=(c.records[0],rec(b'new'))
        p=f.advance(o);self.assertEqual(p.queue.records[1].payload,b'\x55\0\x03new')

    def test_overflow_does_not_retract_known_queue_prefix(self):
        for method,length,count in (('take',508,3),('take',509,2),('take',510,1),('give',508,2),('give',509,1)):
            with self.subTest(method=method,length=length):
                c,f=setup(method,script=b'x'*length);p=f.advance(capture())
                self.assertEqual(len(p.queue.records),count)
                self.assertEqual(p.complete,length==508)
                if length!=508:self.assertEqual(p.status,'unresolved_source_stack_overflow')

    def test_captured_string_gap_is_not_assumed_success(self):
        c,f=setup(owned=False);o=capture();values=dict(o.values);values['record_index']=1
        p=f.advance(replace(o,values=values));self.assertEqual(p.needed,('value','npc_cpp_bytes'))
        self.assertNotIn('npc_id',[label for _,label,_ in p.calls])

    def test_terminal_cleanup_gap_and_terminal_resume_are_idempotent(self):
        c,f=setup();o=capture();normal=dict(o.normal_returns);normal['script_cleanup']=False
        p=f.advance(replace(o,normal_returns=normal));self.assertEqual(len(p.queue.records),3)
        p=f.advance(o);self.assertTrue(p.complete);self.assertIs(f.advance(),p)
        self.assertEqual(len(p.queue.records),3)


if __name__=='__main__':unittest.main()
