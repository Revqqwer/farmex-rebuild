import unittest
from jail_protection import JailFrame, JailObservation, source_vector_count
from teleport_protection import TPObservation
from tp_jail_protection import TPJailFrame, TPJailObservation

class JailProtectionTests(unittest.TestCase):
    def list_observation(self, values=None, blocked=()):
        v = dict(initial_unused_byte=0)
        v.update({'row0.count_initial_begin':0x1000, 'row0.count_end':0x1004,
                  'row0.count_sub_begin':0x1000, 'row0.element_begin':0x2000,
                  'row0.title_pointer':0x3000, 'row0.hwnd':7,
                  'row0.pid':8, 'row0.handle':9, 'row1.count_initial_begin':0})
        v.update(values or {})
        n = {k:True for k in ('prologue','initial_string','final_cleanup','epilogue')}
        n.update({'row0.'+k:True for k in ('string_assign','find_window','window_pid','open','terminate')})
        n.update({k:False for k in blocked})
        return JailObservation(True, v, n)

    def scan_observation(self, values=None, blocked=()):
        v = dict(snapshot_handle=1, process_first_eax=1)
        v.update({'row0.search_eax':0, 'row0.pid':2, 'row0.handle':3,
                  'row0.identity_address':4, 'row0.remote_pointer':5,
                  'row0.compare_eax':1, 'row0.process_next_eax':0})
        v.update(values or {})
        n = {k:True for k in ('prologue','initial_text_span','snapshot','process_first','final_cleanup','epilogue')}
        n.update({'row0.'+k:True for k in ('executable_text','search','open','remote_text',
                  'unicode_convert','compare','terminate','unicode_cleanup','process_next','executable_cleanup')})
        n.update({k:False for k in blocked})
        return JailObservation(True, v, n)

    def test_entry_and_unused_initial_byte_are_required(self):
        f = JailFrame('list')
        self.assertEqual(f.advance(JailObservation()).needed, ('entry','0046dc5c'))
        p = f.advance(JailObservation(True, normal_returns={'prologue':True,'initial_string':True}))
        self.assertEqual(p.needed, ('value','initial_unused_byte'))
        self.assertEqual(p.reads, ((0x526fa9,1,'initial_unused_byte'),))

    def test_empty_vector_skips_end_and_element_reads(self):
        p = JailFrame('list').advance(self.list_observation({'row0.count_initial_begin':0}))
        self.assertTrue(p.complete)
        self.assertEqual(p.iterations, 0)
        self.assertEqual([c[2] for c in p.calls], ['prologue','initial_string','final_cleanup','epilogue'])

    def test_raw_count_arithmetic_and_unsigned_comparison(self):
        for end,begin,want in ((0x1004,0x1000,1),(0x1003,0x1000,0),(0xffc,0x1000,0xffffffff),
                               (0xfff,0x1000,0),(0x1000,0x1000,0),(0,0xfffffffc,1)):
            self.assertEqual(source_vector_count(end,begin),want)
        f = JailFrame('list')
        p = f.advance(self.list_observation({'row0.count_end':0xffc}, blocked=('row0.string_assign',)))
        self.assertEqual(p.needed, ('normal','row0.string_assign'))

    def test_fresh_begin_for_count_and_element_and_wrapped_pointer(self):
        p = JailFrame('list', context=0xffffff80).advance(self.list_observation())
        self.assertTrue(p.complete)
        self.assertIn((0x50,4,'row0.count_sub_begin'),p.reads)
        self.assertEqual(next(c[1] for c in p.calls if c[2]=='row0.string_assign'), (0x2000,'local_string'))
        f = JailFrame('list')
        p = f.advance(self.list_observation({'row0.count_sub_begin':0x1004}))
        self.assertTrue(p.complete)
        self.assertEqual(p.iterations,0)

    def test_list_null_title_and_api_physical_push_order(self):
        p = JailFrame('list').advance(self.list_observation({'row0.title_pointer':0}))
        calls = {c[2]:c for c in p.calls}
        self.assertEqual(calls['row0.find_window'][1],(0x52704b,0))
        self.assertEqual(calls['row0.window_pid'][1],('local_pid',7))
        self.assertEqual(calls['row0.open'][1],(8,0,0x1fffff))
        self.assertEqual(calls['row0.terminate'][1],(0,9))
        self.assertEqual(p.process_termination_calls_executed,0)

    def test_list_gates_window_pid_and_handle_independently(self):
        for key, absent in (('row0.hwnd','row0.window_pid'),('row0.pid','row0.open'),('row0.handle','row0.terminate')):
            p=JailFrame('list').advance(self.list_observation({key:0}))
            self.assertTrue(p.complete)
            self.assertNotIn(absent,[c[2] for c in p.calls])

    def test_consumed_prefix_is_stable_and_pending_call_is_not_duplicated(self):
        f=JailFrame('list')
        p=f.advance(self.list_observation(blocked=('row0.terminate',)))
        self.assertEqual(p.needed,('normal','row0.terminate'))
        self.assertEqual(f.advance(JailObservation()).calls,p.calls)
        p=f.advance(JailObservation(values={'row0.handle':99,'row1.count_initial_begin':0},
                                    normal_returns={'row0.terminate':True,'final_cleanup':True,'epilogue':True}))
        self.assertTrue(p.complete)
        self.assertEqual(next(c[1] for c in p.calls if c[2]=='row0.terminate'),(0,9))
        self.assertIs(f.advance(JailObservation()),p)

    def test_future_bounds_can_shrink_without_reusing_prior_length(self):
        f=JailFrame('list')
        p=f.advance(self.list_observation(blocked=('row0.terminate',)))
        self.assertNotIn('row1.count_initial_begin',f.values)
        p=f.advance(JailObservation(values={'row1.count_initial_begin':0x1000,'row1.count_end':0x1004,'row1.count_sub_begin':0x1000},
                   normal_returns={'row0.terminate':True,'final_cleanup':True,'epilogue':True}))
        self.assertTrue(p.complete)
        self.assertEqual(p.iterations,1)

    def test_snapshot_minus_one_skips_first_and_iteration(self):
        p=JailFrame('scan').advance(self.scan_observation({'snapshot_handle':0xffffffff}))
        self.assertTrue(p.complete)
        self.assertNotIn('process_first',[c[2] for c in p.calls])
        self.assertEqual(next(c[1] for c in p.calls if c[2]=='snapshot'),(0,2))

    def test_list_second_element_uses_fresh_begin_and_dword_wrap(self):
        o=self.list_observation({'row0.count_end':0x1008,'row0.hwnd':0,
            'row1.count_initial_begin':0x1000,'row1.count_end':0x1008,'row1.count_sub_begin':0x1000,
            'row1.element_begin':0xfffffffe,'row1.title_pointer':0,'row1.hwnd':0,'row2.count_initial_begin':0})
        n=dict(o.normal_returns);n.update({'row1.string_assign':True,'row1.find_window':True})
        p=JailFrame('list').advance(JailObservation(True,o.values,n))
        self.assertTrue(p.complete)
        self.assertEqual(p.iterations,2)
        self.assertEqual(next(c[1] for c in p.calls if c[2]=='row1.string_assign'),(2,'local_string'))

    def test_first_process_zero_skips_scan_and_final_cleanup_is_required(self):
        f=JailFrame('scan')
        p=f.advance(self.scan_observation({'process_first_eax':0},blocked=('final_cleanup',)))
        self.assertEqual(p.needed,('normal','final_cleanup'))
        self.assertNotIn('row0.search_eax',f.values)
        self.assertEqual(p.iterations,0)
        p=f.advance(JailObservation(normal_returns={'final_cleanup':True,'epilogue':True}))
        self.assertTrue(p.complete)

    def test_scan_search_minus_one_skips_open_and_next_precedes_cleanup(self):
        p=JailFrame('scan').advance(self.scan_observation({'row0.search_eax':0xffffffff}))
        labels=[c[2] for c in p.calls]
        self.assertTrue(p.complete)
        self.assertNotIn('row0.open',labels)
        self.assertLess(labels.index('row0.process_next'),labels.index('row0.executable_cleanup'))

    def test_scan_zero_handle_is_not_list_handle_gate(self):
        p=JailFrame('scan').advance(self.scan_observation({'row0.handle':0}))
        self.assertTrue(p.complete)
        self.assertEqual(next(c[1] for c in p.calls if c[2]=='row0.remote_text'),(0xff,4,0))
        self.assertEqual(next(c[1] for c in p.calls if c[2]=='row0.terminate'),(0,0))
        self.assertFalse(p.native_execution_verified or p.whole_function_verified or p.live_compatibility_verified)

    def test_scan_compare_uses_low_al_and_missing_cleanup_keeps_prefix(self):
        p=JailFrame('scan').advance(self.scan_observation({'row0.compare_eax':0x100}))
        self.assertNotIn('row0.terminate',[c[2] for c in p.calls])
        f=JailFrame('scan')
        p=f.advance(self.scan_observation({'row0.compare_eax':0x102}, blocked=('row0.unicode_cleanup',)))
        self.assertEqual(p.needed,('normal','row0.unicode_cleanup'))
        self.assertIn('row0.terminate',[c[2] for c in p.calls])
        self.assertNotIn('row0.process_next_eax',f.values)

    def tp(self, list_only=1, outer=False):
        return TPObservation(True,dict(first_area_eax=0x5c,tick_eax=1,start_low=0,start_high=0,
             third_area_eax=0x15c,jail_enabled_byte=1,jail_list_only_byte=list_only),
             dict(first_area=True,tick=True,third_area=True,jail_list=outer,jail_all=outer))

    def test_tp_child_cannot_be_bypassed_by_outer_receipt(self):
        f=TPJailFrame(packet=b'\x27\x03\x5c')
        p=f.advance(TPJailObservation(self.tp(outer=True)))
        self.assertFalse(p.complete)
        self.assertEqual(p.needed,('child',('normal','prologue')))
        self.assertEqual(p.parent.stores,((0x561f6e,1,1),(0x561f70,1,1)))

    def test_completed_child_still_requires_separate_parent_return(self):
        f=TPJailFrame(packet=b'\x27\x03\x5c')
        p=f.advance(TPJailObservation(self.tp(),self.list_observation({'row0.count_initial_begin':0})))
        self.assertTrue(p.child.complete)
        self.assertEqual(p.needed,('parent',('normal','jail_list')))
        p=f.advance(TPJailObservation(TPObservation(normal_returns={'jail_list':True})))
        self.assertTrue(p.complete)
        self.assertIs(f.advance(TPJailObservation()),p)

    def test_tp_selects_scan_and_unrelated_packet_does_not_create_child(self):
        f=TPJailFrame(packet=b'\x27\x03\x5c')
        p=f.advance(TPJailObservation(self.tp(0,True),self.scan_observation({'snapshot_handle':0xffffffff})))
        self.assertTrue(p.complete)
        self.assertEqual(p.child.kind,'scan')
        f=TPJailFrame(packet=b'\x26')
        p=f.advance(TPJailObservation(TPObservation(True)))
        self.assertTrue(p.complete)
        self.assertIsNone(f.child)

    def test_observations_are_immutable_and_reject_implicit_values(self):
        v={'initial_unused_byte':0};o=JailObservation(values=v);v['initial_unused_byte']=2
        self.assertEqual(o.values['initial_unused_byte'],0)
        with self.assertRaises(TypeError):o.values['x']=1
        for values in ({'initial_unused_byte':256},{'x':True},{'x':-1}):
            with self.assertRaises(ValueError):JailObservation(values=values)
        with self.assertRaises(ValueError):JailFrame('other')
        with self.assertRaises(ValueError):TPJailObservation(jail={})

if __name__=='__main__':
    unittest.main()
