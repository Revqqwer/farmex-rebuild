import unittest
from dataclasses import replace
from callback_replacement import CallbackReplacementFrame,RelogReplacementFrame,RelogReplacementObservation
from jail_protection import JailObservation
import test_relog_gate as gate_fixture
import test_relog_controller as controller_fixture


def child(saved=0,old=0x1234):
    return JailObservation(True,dict(saved_original=saved,original_eax=old),
                          {k:True for k in ('prologue','original_reader','copy4','epilogue')})


class CallbackReplacementTests(unittest.TestCase):
    def frame(self,**extra):
        args=dict(saved_cell=0x1000,target_slot=0x2000,replacement=0x12345678)
        args.update(extra);return CallbackReplacementFrame(**args)

    def test_explicit_entry_and_prologue_before_saved_cell_read(self):
        f=self.frame();p=f.advance(replace(child(),entry_reached=False))
        self.assertEqual(p.needed,('entry','0046b8fc'))
        p=f.advance(JailObservation(True));self.assertEqual(p.needed,('normal','prologue'))
        self.assertEqual(p.reads,())

    def test_saved_zero_reads_original_then_records_old_before_copy(self):
        f=self.frame();o=child();p=f.advance(replace(o,normal_returns={'prologue':True,'original_reader':True}))
        self.assertEqual(p.needed,('normal','copy4'))
        self.assertEqual(p.stores,((0x1000,4,0x1234),))
        self.assertEqual(p.copy_intents,((0x2000,b'\x78\x56\x34\x12'),))
        self.assertEqual(p.calls[-1],('memcpy',(4,('source_stack_replacement_argument',0x12345678),0x2000),'copy4'))

    def test_saved_nonzero_skips_reader_but_always_copies_replacement(self):
        p=self.frame().advance(child(saved=0xffffffff))
        self.assertTrue(p.complete)
        self.assertNotIn('original_reader',[c[2] for c in p.calls])
        self.assertEqual(p.stores,((0x2000,4,0x12345678),))

    def test_zero_original_is_stored_without_fictional_success_or_fallback(self):
        p=self.frame().advance(child(old=0))
        self.assertEqual(p.stores[0],(0x1000,4,0))
        self.assertEqual(p.stores[-1],(0x2000,4,0x12345678))
        self.assertFalse(p.memory_effects_verified or p.native_execution_verified)

    def test_copy_receipt_then_epilogue_are_separate_and_prefixes_retained(self):
        f=self.frame();o=child();n=dict(o.normal_returns);n['copy4']=False
        p=f.advance(replace(o,normal_returns=n));self.assertEqual(len(p.stores),1)
        p=f.advance(JailObservation(normal_returns={'copy4':True}))
        self.assertEqual(p.needed,('normal','epilogue'));self.assertEqual(len(p.stores),2)
        p=f.advance(JailObservation(normal_returns={'epilogue':True}));self.assertTrue(p.complete)
        self.assertIs(f.advance(JailObservation()),p)

    def test_aliasing_saved_cell_and_slot_preserves_ordered_writes(self):
        p=self.frame(saved_cell=0x2000).advance(child())
        self.assertEqual(p.stores,((0x2000,4,0x1234),(0x2000,4,0x12345678)))

    def test_zero_replacement_and_raw_parameters_are_source_supported_records(self):
        p=self.frame(replacement=0,target_slot=0).advance(child(saved=1))
        self.assertTrue(p.complete);self.assertEqual(p.copy_intents,((0,b'\0'*4),))
        for value in (-1,1<<32,True):
            with self.assertRaises(ValueError):self.frame(replacement=value)
        with self.assertRaises(ValueError):self.frame().advance({})


class RelogReplacementBindingTests(unittest.TestCase):
    def test_controller_call_physical_push_order_derives_formal_arguments(self):
        f=RelogReplacementFrame('controller')
        p=f.advance(RelogReplacementObservation(controller_fixture.sample(bootstrap_done_byte=0),child()))
        self.assertTrue(p.complete)
        self.assertEqual((f.replacement.saved_cell,f.replacement.target_slot,f.replacement.replacement),
                         (0x554224,0x111,0x412874))
        self.assertEqual(p.replacement.stores[-1],(0x111,4,0x412874))

    def test_gate_uses_fresh_slot_and_separate_saved_original_cell(self):
        f=RelogReplacementFrame('gate')
        p=f.advance(RelogReplacementObservation(gate_fixture.sample(install_attempted_byte=0),child()))
        self.assertTrue(p.complete)
        self.assertEqual((f.replacement.saved_cell,f.replacement.target_slot,f.replacement.replacement),
                         (0x554228,0x7777,0x46f520))
        self.assertEqual(p.parent.stores[0],(0x554218,4,0x20))
        self.assertEqual(p.replacement.stores[-1],(0x7777,4,0x46f520))

    def test_child_entry_derived_but_cannot_skip_missing_child_prologue(self):
        f=RelogReplacementFrame('gate');o=RelogReplacementObservation(gate_fixture.sample(install_attempted_byte=0))
        p=f.advance(o);self.assertEqual(p.needed,('replacement',('normal','prologue')))
        self.assertNotIn((0x553c84,1,1),p.parent.stores)
        p=f.advance(o);self.assertFalse(p.complete)

    def test_complete_replacement_still_waits_for_outer_helper_return(self):
        f=RelogReplacementFrame('gate');parent=gate_fixture.sample(install_attempted_byte=0)
        n=dict(parent.normal_returns);n['install_replace']=False
        p=f.advance(RelogReplacementObservation(replace(parent,normal_returns=n),child()))
        self.assertTrue(p.replacement.complete);self.assertEqual(p.needed,('parent',('normal','install_replace')))
        self.assertNotIn((0x553c84,1,1),p.parent.stores)
        old=p.replacement
        p=f.advance(RelogReplacementObservation(parent))
        self.assertTrue(p.complete);self.assertIs(p.replacement,old)

    def test_unreached_helper_never_creates_child(self):
        for kind,parent in (('controller',controller_fixture.sample()),
                            ('gate',gate_fixture.sample(install_attempted_byte=0,install_probe_local=90))):
            f=RelogReplacementFrame(kind);p=f.advance(RelogReplacementObservation(parent,child()))
            self.assertTrue(p.complete);self.assertIsNone(f.replacement)
            self.assertIsNone(p.replacement)

    def test_typed_parent_and_child_required(self):
        with self.assertRaises(ValueError):RelogReplacementObservation(replacement={})
        with self.assertRaises(ValueError):RelogReplacementFrame('other')
        with self.assertRaises(ValueError):RelogReplacementFrame('gate').advance(JailObservation())


if __name__=='__main__':unittest.main()
