import unittest
from npc_sell_packets import NpcSellRecord,SellCacheSlot,VENDORS,CACHE_BASES,plan_npc_sell_packet


class SellPacketTests(unittest.TestCase):
    def cache(self):return {slot:SellCacheSlot(0x10000000+slot,100,20) for slot in range(14,42)}
    def vendor(self,name='Sundries'):return {key:key==name for key,value in VENDORS}
    def record(self):return NpcSellRecord(0x12345678,2,0x3456)

    def test_exact_header_item_slot_quantity_bytes(self):
        r=plan_npc_sell_packet([self.record()],0x90abcdef,self.vendor(),self.cache())
        self.assertEqual(r.payload.hex(),'210218e40300efcdab900178563412025634')
        self.assertEqual(r.status,'planned');self.assertEqual(r.queue_delay_ms,0)

    def test_all_five_vendor_script_ids(self):
        for name,script in VENDORS:
            r=plan_npc_sell_packet([self.record()],1,self.vendor(name),self.cache())
            self.assertEqual(int.from_bytes(r.payload[2:6],'little'),script)

    def test_independent_vendor_comparisons_last_true_wins(self):
        r=plan_npc_sell_packet([self.record()],1,{name:True for name,value in VENDORS},self.cache())
        self.assertEqual(int.from_bytes(r.payload[2:6],'little'),0x43df0)

    def test_zero_npc_empty_list_or_unmatched_vendor_skip_cache(self):
        for rows,npc,vendor in (([],1,self.vendor()),([self.record()],0,self.vendor()),
                                ([self.record()],1,self.vendor('DC Sundries'))):
            r=plan_npc_sell_packet(rows,npc,vendor)
            self.assertEqual(r.status,'no_queue');self.assertEqual(r.cache_writes,())

    def test_count256_wrap_zero_source_guard_precedes_large_batch_status(self):
        r=plan_npc_sell_packet([self.record()]*256,1,self.vendor())
        self.assertEqual(r.status,'no_queue')

    def test_large_nonzero_batch_does_not_claim_native_equivalence(self):
        r=plan_npc_sell_packet([self.record()]*15,1,self.vendor())
        self.assertEqual(r.status,'unresolved_outside_observed_batch_limit');self.assertIsNone(r.payload)

    def test14_records_complete109_bytes(self):
        rows=[NpcSellRecord(100+i,i,i+1) for i in range(14)]
        r=plan_npc_sell_packet(rows,1,self.vendor(),self.cache())
        self.assertEqual(len(r.payload),109);self.assertEqual(r.payload[10],14)

    def test28_cache_slots_five_dword_stores_then_selected_slot_zeroes(self):
        r=plan_npc_sell_packet([self.record()],1,self.vendor(),self.cache())
        self.assertEqual(len(r.cache_writes),145)
        self.assertEqual(r.cache_writes[:5],tuple(zip(CACHE_BASES,(0x1000000e,100,20,0,0))))
        self.assertEqual(r.cache_writes[-5:],tuple((base+8,0) for base in CACHE_BASES))

    def test_cache_zero_id_does_not_short_circuit_other_metadata(self):
        cache=self.cache();cache[14]=SellCacheSlot(0)
        r=plan_npc_sell_packet([self.record()],1,self.vendor(),cache)
        self.assertEqual(r.status,'needs_observation');self.assertEqual(len(r.cache_writes),1)
        self.assertEqual(r.missing,'cache slot14 durability')

    def test_missing_final_cache_slot_keeps_partial_writes_but_no_payload(self):
        cache=self.cache();del cache[41]
        r=plan_npc_sell_packet([self.record()],1,self.vendor(),cache)
        self.assertEqual(len(r.cache_writes),135);self.assertIsNone(r.payload)

    def test_unknown_vendor_comparison_not_inferred_from_another_match(self):
        vendor=self.vendor();del vendor['Amore']
        r=plan_npc_sell_packet([self.record()],1,vendor,self.cache())
        self.assertEqual(r.status,'needs_observation');self.assertIsNone(r.payload)
