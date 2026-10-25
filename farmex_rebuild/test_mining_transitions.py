import unittest
from mining_transitions import *

def cfg(extract=0,vip=0):return MiningPanelConfiguration('fixture',{0x6046:extract,0x604c:vip})

class MiningTransitionTests(unittest.TestCase):
    def test_start_resets_only_source_execution_fields(self):
        p=plan_mining_ore_start(cfg(),{'gate_4631a8':2,'start_tick':77})
        self.assertTrue(p.complete);self.assertEqual(p.calls,())
        self.assertEqual(p.writes,(('global+561f6c',0,8),('object+5f54',1,8),('object+5f58',0,32),
                                  ('object+5f68',14,32),('object+5f60',77,32),('object+5f64',0,32)))

    def test_gate_exact1_calls_stop_action_before_extract(self):
        p=plan_mining_ore_start(cfg(),{'gate_4631a8':1,'start_tick':77})
        self.assertFalse(p.complete);self.assertEqual(p.calls,(('004c806c',(0x561ef8,0)),))
        self.assertEqual(p.writes,())

    def test_extract_lowword_ff_only_sentinel(self):
        o=dict(gate_4631a8=0,name_first_equal=1,free_slot_463a8c=0x100ff,start_tick=99)
        p=plan_mining_ore_start(cfg(1),o)
        self.assertTrue(p.complete);self.assertEqual(p.writes[0],('object+5f70',255,32))
        self.assertEqual(p.calls,())

    def test_extract_ffff_not_sentinel_and_fixed_equipment_slot6(self):
        o=dict(gate_4631a8=0,name_first_equal=0,name_second_equal=1,free_slot_463a8c=0xffffffff,
               fresh_slot6_name=b'changed name',start_tick=99,**{'returned:0046526c':True})
        p=plan_mining_ore_start(cfg(1),o)
        self.assertTrue(p.complete);self.assertEqual(p.calls,(('0046526c',(6,0)),))
        self.assertEqual(p.writes[:3],(('object+5f70',65535,32),('object+5f74',b'changed name','ansi'),('object+5f70',65549,32)))

    def test_missing_clock_exposes_known_prefix_only(self):
        p=plan_mining_ore_start(cfg(),{'gate_4631a8':0})
        self.assertFalse(p.complete);self.assertEqual(p.missing,'start_tick')
        self.assertEqual(p.writes[-1],('object+5f68',14,32))

    def test_vip_short_circuit_needs_no_inventory(self):
        for kind in ('sell','bank'):
            p=plan_mining_candidates(kind,cfg(vip=2),{})
            self.assertTrue(p.complete);self.assertTrue(p.available);self.assertEqual(p.checked_slots,())

    def test_candidate_rule_offsets_and_first_match(self):
        slots={14:MiningCandidateSlot(0xffffffff),15:MiningCandidateSlot(2,255)}
        for kind,offset in (('sell',6),('bank',4)):
            p=plan_mining_candidates(kind,cfg(),slots)
            self.assertTrue(p.complete);self.assertTrue(p.available)
            self.assertEqual(p.checked_slots,(14,15));self.assertEqual(p.rule_reads,((2,offset),))

    def test_negative_indices_skip_flags_and_all28_slots(self):
        p=plan_mining_candidates('sell',cfg(),{i:MiningCandidateSlot(0x80000000) for i in range(14,42)})
        self.assertTrue(p.complete);self.assertFalse(p.available)
        self.assertEqual(p.checked_slots,tuple(range(14,42)));self.assertEqual(p.rule_reads,())

    def test_missing_slot_is_not_absence(self):
        p=plan_mining_candidates('sell',cfg(),{})
        self.assertFalse(p.complete);self.assertIsNone(p.available)
        self.assertEqual(p.missing,'slot14 classifier index')

    def test_unbounded_positive_index_requires_explicit_flag(self):
        p=plan_mining_candidates('bank',cfg(),{14:MiningCandidateSlot(0x7fffffff)})
        self.assertFalse(p.complete);self.assertEqual(p.rule_reads,((0x7fffffff,4),))
        self.assertEqual(p.missing,'slot14 rule BYTE')

if __name__=='__main__':unittest.main()
