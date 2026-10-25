import struct,unittest
import test_dc_propagation as consumer_fixture
from dc_sender_template import *

class DCTransferTests(unittest.TestCase):
    def observation(self,values=None,blocked=()):
        v=dict(payload_allocation_eax=0x2000,copied_root_dword=0x3000,copied_target_dword=0x4000,
               stub_allocation_eax=0x5000,thread_eax=0x6000);v.update(values or {})
        n={k:True for k in ('prologue','template_copy','payload.allocate','payload.write','copy.root',
          'copy.length','copy.pointer','copy.target','stub.prologue','stub.allocate','stub.write',
          'stub.thread','stub.wait','stub.close','stub.free','stub.epilogue','stub_outer','payload.free','epilogue')}
        n.update({k:False for k in blocked});return JailObservation(True,v,n)

    def test_pure_template_fields_and_invalid_raw_inputs(self):
        b=patched_sender_template(0x11223344,1,0x55667788,0x99aabbcc)
        self.assertEqual(len(b),26)
        self.assertEqual([struct.unpack_from('<I',b,at)[0] for at in (3,8,13,18)],
                         [0x11223344,1,0x55667788,0x99aabbcc])
        self.assertEqual(b[:3],b'\x60\x8b\x0d');self.assertEqual(b[-4:],b'\xff\xd7\x61\xc3')
        with self.assertRaises(ValueError):patched_sender_template(True,0,0,0)
        with self.assertRaises(ValueError):DCTransferFrame(1,bytearray(b'1'))

    def test_entry_and_first_allocation_zero_do_not_invent_cleanup(self):
        f=DCTransferFrame(7,b'\x01')
        self.assertEqual(f.advance(JailObservation()).needed,('entry','00464834'))
        p=f.advance(self.observation({'payload_allocation_eax':0}))
        self.assertTrue(p.complete);self.assertEqual(p.write_intents,());self.assertEqual(p.patches,())
        self.assertNotIn('payload.free',[c[2] for c in p.calls])
        self.assertEqual(p.stub_bytes,SENDER_TEMPLATE)

    def test_positive_bytes_and_exact_api_pushes(self):
        p=DCTransferFrame(7,b'\x01').advance(self.observation())
        self.assertTrue(p.complete);self.assertEqual(p.stub_bytes,patched_sender_template(0x3000,1,0x2000,0x4000))
        calls={c[2]:c for c in p.calls}
        self.assertEqual(calls['payload.allocate'][1],(0x40,0x1000,1,0,7))
        self.assertEqual(calls['stub.thread'][1],(0,0,0,0x5000,0,0,7))
        self.assertEqual(calls['stub.wait'][1],(0xffffffff,0x6000))
        self.assertEqual(p.write_intents,(('payload',0x2000,b'\x01'),('stub',0x5000,p.stub_bytes)))

    def test_second_allocation_zero_skips_thread_but_frees_payload(self):
        p=DCTransferFrame(7,b'\x01').advance(self.observation({'stub_allocation_eax':0}))
        labels=[c[2] for c in p.calls]
        self.assertTrue(p.complete);self.assertNotIn('stub.thread',labels)
        self.assertNotIn('stub.free',labels);self.assertIn('payload.free',labels)

    def test_zero_thread_skips_wait_but_still_closes_and_frees(self):
        p=DCTransferFrame(7,b'\x01').advance(self.observation({'thread_eax':0}))
        labels=[c[2] for c in p.calls]
        self.assertTrue(p.complete);self.assertNotIn('stub.wait',labels)
        self.assertEqual(next(c[1] for c in p.calls if c[2]=='stub.close'),(0,))
        self.assertLess(labels.index('stub.close'),labels.index('stub.free'))
        self.assertLess(labels.index('stub.free'),labels.index('payload.free'))

    def test_write_receipt_required_without_invented_BOOL_success_field(self):
        f=DCTransferFrame(7,b'\x01');p=f.advance(self.observation(blocked=('payload.write',)))
        self.assertEqual(p.needed,('normal','payload.write'));self.assertEqual(p.patches,())
        self.assertEqual(p.write_intents,(('payload',0x2000,b'\x01'),))
        p=f.advance(self.observation());self.assertTrue(p.complete)
        self.assertNotIn('write_success_eax',f.values)

    def test_partial_patches_retained_and_root_capture_latched(self):
        f=DCTransferFrame(7,b'\x01');p=f.advance(self.observation(blocked=('copy.target',)))
        self.assertEqual([v[0] for v in p.patches],[3,8,13])
        self.assertNotIn('copied_target_dword',f.values)
        p=f.advance(self.observation({'copied_root_dword':0xdeadbeef,'copied_target_dword':0xabcdef01}))
        self.assertEqual(p.stub_bytes,patched_sender_template(0x3000,1,0x2000,0xabcdef01))

    def test_copy_normal_and_captured_input_are_separate(self):
        f=DCTransferFrame(7,b'1');o=self.observation();v=dict(o.values);del v['copied_root_dword']
        p=f.advance(JailObservation(True,v,o.normal_returns))
        self.assertEqual(p.needed,('value','copied_root_dword'));self.assertEqual(p.patches,())
        self.assertEqual(p.stub_bytes,SENDER_TEMPLATE)

    def test_complete_child_does_not_manufacture_outer_return(self):
        f=DCTransferFrame(7,b'1');p=f.advance(self.observation(blocked=('stub_outer',)))
        self.assertEqual(p.needed,('normal','stub_outer'))
        self.assertIn('stub.epilogue',[c[2] for c in p.calls])
        self.assertNotIn('payload.free',[c[2] for c in p.calls])
        p=f.advance(JailObservation(normal_returns={'stub_outer':True,'payload.free':True,'epilogue':True}))
        self.assertTrue(p.complete);self.assertIs(f.advance(JailObservation()),p)

    def test_wait_gap_blocks_close_and_frees_without_duplicate_write(self):
        f=DCTransferFrame(7,b'1');p=f.advance(self.observation(blocked=('stub.wait',)))
        self.assertEqual(p.needed,('normal','stub.wait'))
        self.assertNotIn('stub.close',[c[2] for c in p.calls])
        self.assertEqual(f.advance(JailObservation()).write_intents,p.write_intents)
        p=f.advance(self.observation());self.assertTrue(p.complete);self.assertEqual(len(p.write_intents),2)

    def test_isolated_zero_length_and_zero_handle_not_real_allocation_proof(self):
        p=DCTransferFrame(0,b'').advance(self.observation())
        self.assertTrue(p.complete)
        self.assertEqual(struct.unpack_from('<I',p.stub_bytes,8)[0],0)
        self.assertFalse(p.native_execution_verified or p.live_compatibility_verified or p.whole_function_verified)

    def test_consumer_sender_entry_is_derived_but_cannot_be_bypassed(self):
        f=DCSenderConsumerFrame('list');source=consumer_fixture.DCPropagationTests().consumer()
        p=f.advance(DCSenderObservation(source))
        self.assertEqual(p.needed,('sender','row0.send',('normal','prologue')))
        self.assertEqual(f.children['row0.send'].handle,6)
        self.assertEqual(f.children['row0.send'].payload,b'\x01')

    def test_consumer_outer_return_remains_separate_from_transfer_complete(self):
        source=consumer_fixture.DCPropagationTests().consumer();n=dict(source.normal_returns);n['row0.send']=False
        f=DCSenderConsumerFrame('list')
        p=f.advance(DCSenderObservation(JailObservation(True,source.values,n),{'row0.send':self.observation()}))
        self.assertTrue(p.transfers['row0.send'].complete)
        self.assertEqual(p.needed,('consumer',('normal','row0.send')))
        p=f.advance(DCSenderObservation(source))
        self.assertTrue(p.complete)
        self.assertIs(f.advance(DCSenderObservation()),p)

    def test_guard_skip_does_not_consume_unreached_transfer(self):
        source=consumer_fixture.DCPropagationTests().consumer(**{'row0.guard_eax':2})
        f=DCSenderConsumerFrame('list');p=f.advance(DCSenderObservation(source))
        self.assertTrue(p.complete);self.assertEqual(dict(p.transfers),{})
        self.assertEqual(f.children,{})

    def test_two_sender_calls_get_distinct_latched_children(self):
        source=consumer_fixture.DCPropagationTests().consumer()
        values=dict(source.values);normals=dict(source.normal_returns)
        values.update({k.replace('row0.','row1.',1):v for k,v in source.values.items() if k.startswith('row0.')})
        normals.update({k.replace('row0.','row1.',1):v for k,v in source.normal_returns.items() if k.startswith('row0.')})
        values.update({'row0.count_end':0x1008,'row1.count_initial_begin':0x1000,
                       'row1.count_end':0x1008,'row1.handle':9,'row2.count_initial_begin':0})
        f=DCSenderConsumerFrame('list')
        p=f.advance(DCSenderObservation(JailObservation(True,values,normals),
          {'row0.send':self.observation(),'row1.send':self.observation({'payload_allocation_eax':0x8000})}))
        self.assertTrue(p.complete);self.assertEqual(set(p.transfers),{'row0.send','row1.send'})
        self.assertIsNot(f.children['row0.send'],f.children['row1.send'])
        self.assertEqual(f.children['row0.send'].handle,6);self.assertEqual(f.children['row1.send'].handle,9)
        self.assertEqual(p.transfers['row1.send'].write_intents[0],('payload',0x8000,b'\x01'))

if __name__=='__main__':unittest.main()
