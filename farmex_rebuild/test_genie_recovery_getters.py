import unittest
from dataclasses import replace
from genie_recovery import GenieRecoveryFrame,RecoverySlotSample,GenieRecoveryObservation,plan_genie_recovery_scan,TARGET_NAME
from inventory_getter_frames import InventoryGetterFrame
from mining_slot_name import SlotNameObservation
from upgrade_packets import UpgradeItemObservation
from test_genie_recovery import sample
from test_mining_slot_name import fixture

def item(**kw):
    return replace(UpgradeItemObservation(0x1000,4,8,0x2000,0x3000,0x4000,0x5000,0x6000,1000,1002),**kw)

def bound():
    return replace(sample(),samples={14:RecoverySlotSample(comparison_eax=1,name_inputs=fixture(TARGET_NAME),item_inputs=item())})

class RecoveryGetterTests(unittest.TestCase):
    def test_both_generated_children_use_absolute_slot_but_fresh_ID(self):
        p=GenieRecoveryFrame(1).advance(bound());self.assertTrue(p.complete)
        self.assertEqual(p.scan.payload,bytes.fromhex('970101ea030000'))
        self.assertEqual([(s,k) for s,k,_ in p.scan.getter_executions],[(14,'name_inputs'),(14,'item_inputs')])
        self.assertEqual(p.scan.getter_executions[0][2].reads[2][1],0x368)
        self.assertEqual(p.scan.getter_executions[1][2].reads[2][1],0x3040)
        self.assertNotEqual(p.scan.getter_executions[0][2].item_id,1002)

    def test_bound_gap_blocks_raw_result_fallback(self):
        for field,rawfield,value,obs in (('name_inputs','name_bytes',TARGET_NAME,SlotNameObservation()),('item_inputs','item_id_eax',1002,UpgradeItemObservation())):
            o=bound();s=replace(o.samples[14],**{field:obs,rawfield:value});o=replace(o,samples={14:s})
            p=plan_genie_recovery_scan(o);self.assertFalse(p.complete);self.assertEqual(p.needed,('bound',14,field))
            p=GenieRecoveryFrame(1).advance(o);self.assertFalse(p.complete);self.assertEqual(p.queue.records,())

    def test_explicit_raw_mismatch_rejected_by_plan_and_frame(self):
        for changes in ({'name_bytes':b'Other'},{'item_id_eax':7}):
            o=bound();o=replace(o,samples={14:replace(o.samples[14],**changes)})
            with self.assertRaises(ValueError):plan_genie_recovery_scan(o)
            with self.assertRaises(ValueError):GenieRecoveryFrame(1).advance(o)

    def test_item_prefix_retained_as_late_variant_arrives(self):
        f=GenieRecoveryFrame(1);o=bound();o=replace(o,samples={14:replace(o.samples[14],item_inputs=item(variant_item=None))})
        p=f.advance(o);self.assertFalse(p.complete)
        o=replace(o,samples={14:replace(o.samples[14],item_inputs=item(base_item=9999,variant_item=1003))})
        p=f.advance(o);self.assertTrue(p.complete)
        self.assertEqual(p.scan.item_id,1003) #1000 retained, not replacement9999.

    def test_nested_name_capture_can_grow_but_consumed_metadata_cannot_change(self):
        f=GenieRecoveryFrame(1);o=bound();n=o.samples[14].name_inputs
        short=replace(n,name=replace(n.name,captured=b'Spirit'))
        p=f.advance(replace(o,samples={14:replace(o.samples[14],name_inputs=short)}));self.assertFalse(p.complete)
        changed=replace(n,base_item=0,name=replace(n.name,metadata_category=0))
        p=f.advance(replace(o,samples={14:replace(o.samples[14],name_inputs=changed)}));self.assertTrue(p.complete)
        self.assertEqual(p.scan.getter_executions[0][2].ansi_bytes,TARGET_NAME)
        self.assertEqual(p.scan.getter_executions[0][2].item_id,123456)

    def test_changed_capture_prefix_is_rejected(self):
        f=InventoryGetterFrame(14,name=True);n=fixture(TARGET_NAME)
        self.assertIsNone(f.advance(replace(n,name=replace(n.name,captured=b'Spirit'))).ansi_bytes)
        with self.assertRaises(ValueError):f.advance(replace(n,name=replace(n.name,captured=b'Wrong'+b'\0'*11)))

    def test_zero_record_and_unsafe_name_paths_do_not_invent_success(self):
        f=InventoryGetterFrame(14);p=f.advance(item(record=0));self.assertTrue(p.complete);self.assertEqual(len(p.reads),3)
        o=bound();n=o.samples[14].name_inputs;n=replace(n,name=replace(n.name,storage_dword=513))
        p=GenieRecoveryFrame(1).advance(replace(o,samples={14:replace(o.samples[14],name_inputs=n)}))
        self.assertFalse(p.complete);self.assertEqual(p.queue.records,())

    def test_nonmatching_name_never_consumes_item_getter(self):
        o=bound();s=replace(o.samples[14],comparison_eax=0,item_inputs=UpgradeItemObservation())
        p=plan_genie_recovery_scan(replace(o,samples={14:s}))
        self.assertEqual(p.visited_slots,(14,15));self.assertEqual(len(p.getter_executions),1)

if __name__=='__main__':unittest.main()
