import unittest
from dataclasses import replace
from genie_coupon_sync import *
from genie_settings import OPS


def sample(enabled=1,current=0,**extra):
    values=dict(root_slot=0x1000,root_eax=0xfffffff0,table_offset=0x30,
                table_eax=0xffffff00,byte_offset=0x200,coupon_flag_byte=enabled,byte_read_eax=current)
    values.update(extra)
    return JailObservation(True,values,{k:True for k in ('root','table','byte_read','byte_write')})


def settings(value=0):
    return GenieSettingsObservation(True,{'checked_%03x'%slot:value for _,slot,_ in OPS},
                                    {'checked_%03x'%slot:True for _,slot,_ in OPS})


class GenieCouponSyncTests(unittest.TestCase):
    def test_explicit_middle_entry_without_fake_prologue(self):
        f=GenieCouponSyncFrame();p=f.advance(JailObservation())
        self.assertEqual(p.needed,('entry','00458143'));self.assertFalse(p.calls)

    def test_address_chain_wrap_and_physical_push_order(self):
        p=GenieCouponSyncFrame().advance(sample())
        self.assertTrue(p.complete);self.assertEqual(p.next_address,0x4581b9)
        self.assertIn(('0045dc44',(0x20,),'table'),p.calls)
        self.assertEqual(p.write_intents,((0x100,1,1),))
        self.assertEqual(p.calls[-1],('0045de4c',(1,0x100),'byte_write'))

    def test_exact_byte_branch_matrix(self):
        for enabled,current,wanted in ((1,0,1),(2,0,1),(1,1,None),(1,2,None),
                                       (0,1,0),(0,0,None),(0,2,None)):
            p=GenieCouponSyncFrame().advance(sample(enabled,current))
            self.assertEqual(p.write_intents,() if wanted is None else ((0x100,1,wanted),))

    def test_only_low_al_of_reader_is_used(self):
        p=GenieCouponSyncFrame().advance(sample(1,0x100));self.assertEqual(p.write_intents,((0x100,1,1),))
        p=GenieCouponSyncFrame().advance(sample(0,0xffffff01));self.assertEqual(p.write_intents,((0x100,1,0),))

    def test_no_invented_null_root_guard(self):
        p=GenieCouponSyncFrame().advance(sample(root_eax=0,table_eax=0))
        self.assertIn(('0045dc44',(0x30,),'table'),p.calls)
        self.assertEqual(p.write_intents,((0x200,1,1),))

    def test_flag_is_read_after_both_guarded_chain_calls(self):
        f=GenieCouponSyncFrame();o=sample()
        p=f.advance(replace(o,normal_returns={**o.normal_returns,'table':False}))
        self.assertEqual(p.needed,('normal','table'))
        self.assertFalse(any(label=='coupon_flag_byte' for _,_,label in p.reads))

    def test_cached_address_survives_native_reader_return_gap(self):
        f=GenieCouponSyncFrame();o=sample()
        p=f.advance(replace(o,normal_returns={**o.normal_returns,'byte_read':False}))
        self.assertEqual(p.needed,('normal','byte_read'))
        p=f.advance(sample(root_eax=0x999,table_eax=0x888,byte_offset=1))
        self.assertEqual(p.write_intents,((0x100,1,1),))

    def test_write_intent_precedes_helper_return_and_never_certifies_effect(self):
        f=GenieCouponSyncFrame();o=sample()
        p=f.advance(replace(o,normal_returns={**o.normal_returns,'byte_write':False}))
        self.assertEqual(p.needed,('normal','byte_write'));self.assertEqual(len(p.write_intents),1)
        self.assertIsNone(p.next_address);self.assertFalse(p.byte_effects_verified)
        p=f.advance(o);self.assertTrue(p.complete);self.assertFalse(p.byte_effects_verified)

    def test_header_completion_derives_sync_entry_but_not_fresh_flag(self):
        o=sample(0,1);o=replace(o,values={k:v for k,v in o.values.items() if k!='coupon_flag_byte'})
        f=GenieSettingsSyncFrame();p=f.advance(GenieSettingsSyncObservation(settings(1),o))
        self.assertTrue(p.settings.complete);self.assertEqual(p.needed,('sync',('value','coupon_flag_byte')))
        p=f.advance(GenieSettingsSyncObservation(settings(1),sample(0,1)))
        self.assertTrue(p.complete);self.assertEqual(p.sync.write_intents,((0x100,1,0),))

    def test_unreached_header_does_not_construct_sync(self):
        f=GenieSettingsSyncFrame();p=f.advance(GenieSettingsSyncObservation(sync=sample()))
        self.assertFalse(p.complete);self.assertIsNone(f.sync)

    def test_context_byte_read_wrap_and_raw_validation(self):
        p=GenieCouponSyncFrame(context=0xffffff80).advance(sample())
        self.assertIn((0x3a,1,'coupon_flag_byte'),p.reads)
        with self.assertRaises(ValueError):GenieCouponSyncFrame(context=True)
        with self.assertRaises(ValueError):GenieCouponSyncFrame(source_sha256='unknown')
        with self.assertRaises(ValueError):GenieSettingsSyncObservation(sync={})
        with self.assertRaises(ValueError):sample(enabled=256)
