import unittest
from dc_propagation import *

class DCPropagationTests(unittest.TestCase):
    def periodic(self,**values):
        v=dict(context_6e_byte=0,enabled_byte=1,tick_eax=300000,stamp=0,list_only_byte=1,post_tick_eax=300010)
        v.update(values)
        return JailObservation(True,v,dict(tick=True,consumer=True,post_tick=True))
    def consumer(self,kind='list',**extra):
        v={'payload_byte':1,'row0.count_initial_begin':0x1000,'row0.count_end':0x1004,
           'row0.count_sub_begin':0x1000,'row0.element_begin':0x2000,'row0.title_pointer':3,
           'row0.hwnd':4,'row0.pid_dword':5,'row0.handle':6,'row1.count_initial_begin':0,
           'row0.guard_root_slot':0x100,'row0.guard_root_eax':0xfffffff0,'row0.guard_offset':0x20,
           'row0.guard_eax':1,'row0.first.slot':0x200,'row0.first.root_eax':0x300,
           'row0.first.offset':0x10,'row0.first.eax':0,'row0.second.slot':0x400,
           'row0.second.root_eax':0x500,'row0.second.offset':0x30,'row0.second.eax':0,
           'snapshot_handle':1,'first_eax':1,'row0.search_eax':0,'row0.identity_address':7,
           'row0.identity_pointer':8,'row0.compare_eax':1,'row0.next_eax':0}
        v.update(extra)
        n={k:True for k in ('prologue','scratch_init','initial_text','snapshot','first','final_cleanup','epilogue')}
        n.update({'row0.'+k:True for k in ('string','window','pid','open','guard_root','guard_byte',
          'first.root','first.value','second.root','second.value','send','executable','search',
          'identity_read','identity_convert','compare','identity_cleanup','next','executable_cleanup')})
        return JailObservation(True,v,n)

    def test_context_branch_and_disabled_gate_skip_tick(self):
        p=DCPeriodicFrame().advance(self.periodic(context_6e_byte=1))
        self.assertTrue(p.complete);self.assertEqual(p.next_address,0x45998e)
        self.assertEqual(p.reads,((0x562202,1,'context_6e_byte'),));self.assertEqual(p.calls,())
        p=DCPeriodicFrame().advance(self.periodic(enabled_byte=0))
        self.assertEqual(p.next_address,0x459c5a);self.assertEqual(p.calls,())

    def test_unsigned_elapsed_boundary_wrap_and_post_stamp(self):
        p=DCPeriodicFrame().advance(self.periodic(tick_eax=299999))
        self.assertTrue(p.complete);self.assertEqual(p.stores,())
        for tick,stamp in ((300000,0),(299984,0xfffffff0),(0,1)):
            p=DCPeriodicFrame().advance(self.periodic(tick_eax=tick,stamp=stamp))
            self.assertEqual(p.stores,((0x553ce4,4,300010),))
        p=DCPeriodicFrame().advance(self.periodic(list_only_byte=0))
        self.assertEqual(p.calls[1][0],'0046d904')

    def test_post_tick_is_fresh_and_store_requires_its_result(self):
        f=DCPeriodicFrame();o=self.periodic();n=dict(o.normal_returns);n['consumer']=False
        p=f.advance(JailObservation(True,o.values,n))
        self.assertEqual(p.needed,('normal','consumer'));self.assertEqual(p.stores,())
        self.assertNotIn('post_tick_eax',f.values)
        p=f.advance(JailObservation(values={'post_tick_eax':900000},normal_returns={'consumer':True,'post_tick':True}))
        self.assertEqual(p.stores,((0x553ce4,4,900000),))

    def test_exact_guard_al_one_and_opaque_sender_payload(self):
        for value in (0,2,255,0x100):
            f=DCConsumerFrame('list');p=f.advance(self.consumer(**{'row0.guard_eax':value}))
            self.assertTrue(p.complete);self.assertEqual(p.payload_intents,())
            self.assertNotIn('row0.first.slot',f.values)
        p=DCConsumerFrame('list').advance(self.consumer(**{'row0.guard_eax':0x101,'payload_byte':0xa5}))
        self.assertEqual(p.payload_intents,((6,b'\xa5'),))
        self.assertEqual(next(c[1] for c in p.calls if c[2]=='row0.guard_byte'),(0x10,6))

    def test_second_chain_runs_before_first_nonzero_comparison(self):
        f=DCConsumerFrame('list');o=self.consumer(**{'row0.first.eax':1});n=dict(o.normal_returns);n['row0.second.value']=False
        p=f.advance(JailObservation(True,o.values,n))
        self.assertEqual(p.needed,('normal','row0.second.value'))
        p=f.advance(JailObservation(values={'row0.second.eax':0},normal_returns={'row0.second.value':True,
            'final_cleanup':True,'epilogue':True}))
        self.assertFalse(p.complete) #Still needs the fresh final vector check.
        self.assertEqual(p.needed,('value','row1.count_initial_begin'))
        self.assertEqual(p.payload_intents,())

    def test_each_secondary_nonzero_blocks_sender(self):
        for field in ('row0.first.eax','row0.second.eax'):
            p=DCConsumerFrame('list').advance(self.consumer(**{field:0xffffffff}))
            self.assertTrue(p.complete);self.assertEqual(p.payload_intents,())

    def test_list_window_pid_handle_zero_independent_gates(self):
        for field in ('row0.hwnd','row0.pid_dword','row0.handle'):
            f=DCConsumerFrame('list');p=f.advance(self.consumer(**{field:0}))
            self.assertTrue(p.complete);self.assertNotIn('row0.guard_root_slot',f.values)
            self.assertEqual(p.payload_intents,())

    def test_scan_zero_handle_and_next_before_cleanup(self):
        p=DCConsumerFrame('scan').advance(self.consumer('scan',**{'row0.handle':0}))
        self.assertTrue(p.complete);self.assertEqual(p.payload_intents,((0,b'\x01'),))
        labels=[c[2] for c in p.calls]
        self.assertLess(labels.index('row0.next'),labels.index('row0.executable_cleanup'))

    def test_scan_search_compare_and_snapshot_skips(self):
        for extra in ({'snapshot_handle':0xffffffff},{'first_eax':0},{'row0.search_eax':0xffffffff},{'row0.compare_eax':0x100}):
            f=DCConsumerFrame('scan');p=f.advance(self.consumer('scan',**extra))
            self.assertTrue(p.complete);self.assertEqual(p.payload_intents,())
            self.assertNotIn('row0.guard_eax',f.values)

    def test_pending_send_is_once_and_has_no_success_eax(self):
        f=DCConsumerFrame('list');o=self.consumer();n=dict(o.normal_returns);n['row0.send']=False
        p=f.advance(JailObservation(True,o.values,n))
        self.assertEqual(p.needed,('normal','row0.send'));self.assertEqual(p.payload_intents,((6,b'\x01'),))
        self.assertEqual(f.advance(JailObservation()).payload_intents,p.payload_intents)
        p=f.advance(self.consumer(**{'payload_byte':2}))
        self.assertTrue(p.complete);self.assertEqual(p.payload_intents,((6,b'\x01'),))
        self.assertIs(f.advance(JailObservation()),p)
        self.assertFalse(p.native_execution_verified or p.live_compatibility_verified or p.whole_function_verified)

    def test_cascade_child_cannot_be_skipped_and_parent_return_is_separate(self):
        f=DCCascadeFrame();p=f.advance(DCCascadeObservation(self.periodic()))
        self.assertEqual(p.needed,('consumer',('normal','prologue')));self.assertEqual(p.parent.stores,())
        parent=JailObservation(normal_returns={'consumer':False})
        p=f.advance(DCCascadeObservation(parent,self.consumer()))
        self.assertTrue(p.consumer.complete);self.assertEqual(p.needed,('parent',('normal','consumer')))
        p=f.advance(DCCascadeObservation(JailObservation(values={'post_tick_eax':42},normal_returns={'consumer':True,'post_tick':True})))
        self.assertTrue(p.complete);self.assertEqual(p.parent.stores,((0x553ce4,4,42),))
        self.assertIs(f.advance(DCCascadeObservation()),p)

    def test_cascade_scan_and_short_elapsed_do_not_create_wrong_child(self):
        f=DCCascadeFrame();p=f.advance(DCCascadeObservation(self.periodic(tick_eax=1)))
        self.assertTrue(p.complete);self.assertIsNone(f.consumer)
        f=DCCascadeFrame();p=f.advance(DCCascadeObservation(self.periodic(list_only_byte=0),
            self.consumer('scan',snapshot_handle=0xffffffff)))
        self.assertTrue(p.complete);self.assertEqual(p.consumer.kind,'scan')

if __name__=='__main__':unittest.main()
