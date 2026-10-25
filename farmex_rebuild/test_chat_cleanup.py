import unittest
from dataclasses import replace
from chat_cleanup import ChatCleanupArgs as A,ChatCleanupObservation as O,ChatCleanupFrame,plan_chat_cleanup

ARGS=A(0x1000,0x2000,0,0x3000,7,0x4000)
LABELS=('free_fefc','free_fef8','free_ff0c','helper_4040f8','reset_local_50','reset_local_28','epilogue')
def done():return O({k:True for k in LABELS})
class ChatCleanupTests(unittest.TestCase):
 def test_exact_free_flags_reset_pushes_and_local_writes(self):
  p=plan_chat_cleanup(ARGS,done());self.assertTrue(p.complete)
  self.assertEqual([c[:2] for c in p.calls],[('CRT:_free',(0x2000,)),('CRT:_free',(0,)),('CRT:_free',(0x3000,)),
   ('004040f8',(2,0xfac)),('00403860',(0,1,0xfb0)),('00403860',(0,1,0xfd8))])
  self.assertEqual(p.stores,((0xf34,4,5),(0xf34,4,4),(0xf34,4,3)));self.assertEqual(p.fs_store,('FS:0',4,0x4000))
  self.assertFalse(p.heap_effect_verified);self.assertFalse(p.returned_EAX_verified)

 def test_each_normal_gap_stops_before_later_effects(self):
  for index,label in enumerate(LABELS):
   r={k:True for k in LABELS[:index]};r[label]=False;p=plan_chat_cleanup(ARGS,O(r))
   self.assertFalse(p.complete);self.assertEqual(p.needed,label)
   self.assertEqual(len(p.calls),min(index+1,6))
   self.assertEqual(len(p.stores),max(0,min(index-2,3)))
   self.assertEqual(p.fs_store is not None,index==6)

 def test_frame_caches_completed_calls_and_final_result(self):
  f=ChatCleanupFrame(ARGS);p=f.advance(O({'free_fefc':True,'free_fef8':True}))
  self.assertEqual(p.needed,'free_ff0c')
  p=f.advance(O({'free_fefc':False,**{k:True for k in LABELS[2:]}}))
  self.assertTrue(p.complete);self.assertIs(f.advance(O()),p);self.assertEqual(len(p.calls),6)

 def test_counter_and_frame_relative_addresses_keep_DWORD_wrap(self):
  p=plan_chat_cleanup(replace(ARGS,ebp_dword=0x10,local_ff34=0),done())
  self.assertEqual(p.stores,((0xffffff44,4,0xfffffffe),(0xffffff44,4,0xfffffffd),(0xffffff44,4,0xfffffffc)))
  self.assertEqual(p.calls[3][1],(2,0xffffffbc))

 def test_zero_pointers_do_not_skip_source_helper_receipts(self):
  p=plan_chat_cleanup(A(0,0,0,0,0,0),O())
  self.assertFalse(p.complete);self.assertEqual(p.needed,'free_fefc');self.assertEqual(p.calls[0][1],(0,))

 def test_input_types_are_not_coerced(self):
  with self.assertRaises(ValueError):replace(ARGS,local_ff34=True)
  with self.assertRaises(ValueError):O({'epilogue':1})
  with self.assertRaises(ValueError):plan_chat_cleanup(ARGS,{})

if __name__=='__main__':unittest.main()
