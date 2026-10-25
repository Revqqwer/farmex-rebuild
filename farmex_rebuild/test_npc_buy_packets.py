import unittest
from dataclasses import replace
from npc_buy_packets import NpcBuyRecord,NpcBuyPacketObservation,plan_npc_buy_packet,BUY_VENDORS
from npc_sell_packets import SellCacheSlot

class BuyPacketTests(unittest.TestCase):
    def obs(self,**changes):
        return replace(NpcBuyPacketObservation(0,1000,
                       {name:name=='Sundries' for name,value in BUY_VENDORS},
                       {slot:SellCacheSlot(0,0,0) for slot in range(14,42)},
                       {index:1000 for index in range(120)}),**changes)
    def row(self,**changes):return replace(NpcBuyRecord(0x12345678,10,2,3,5,7),**changes)
    def plan(self,rows=None,obs=None,npc=9):
        return plan_npc_buy_packet((self.row(),) if rows is None else rows,npc,self.obs() if obs is None else obs)

    def test_exact_header_and_nine_byte_record(self):
        r=self.plan()
        self.assertEqual(r.payload,bytes.fromhex('210118e40300090000000178563412000a000203'))
        self.assertEqual(r.accepted,((0,0,10),));self.assertEqual(len(r.cache_writes),145)
        self.assertEqual(r.cache_writes[-5:],((0x568e84,0x12345678),(0x568ef4,1),(0x568f64,10),(0x568fd4,0),(0x569044,0)))

    def test_first_existing_stack_overrides_earlier_empty_slot(self):
        obs=self.obs();cache=dict(obs.cache_slots)
        cache[16]=SellCacheSlot(0x12345678,22,4);cache[18]=SellCacheSlot(0x12345678,22,5)
        r=self.plan(obs=replace(obs,cache_slots=cache))
        self.assertEqual(r.accepted,((0,2,6),));self.assertEqual(r.payload[15:18],b'\x02\x06\x00')

    def test_existing_quantity_equal_or_above_target_skips(self):
        for quantity in (10,11,0x7fffffff):
            obs=self.obs();cache=dict(obs.cache_slots);cache[14]=SellCacheSlot(0x12345678,1,quantity)
            r=self.plan(obs=replace(obs,cache_slots=cache))
            self.assertEqual(r.status,'no_queue');self.assertEqual(len(r.cache_writes),140)

    def test_duplicate_requested_rows_observe_updated_cache(self):
        r=self.plan([self.row(),self.row(desired_quantity=12)])
        self.assertEqual(r.accepted,((0,0,10),(1,0,2)));self.assertEqual(r.payload[10],2)

    def test_no_empty_slot_skips_without_currency_observation(self):
        cache={slot:SellCacheSlot(slot,1,1) for slot in range(14,42)}
        self.assertEqual(self.plan(obs=self.obs(cache_slots=cache,currency_by_record={})).status,'no_queue')

    def test_weight_equality_rejected_currency_equality_accepted(self):
        r=self.plan(obs=self.obs(maximum_weight=50,currency_by_record={}))
        self.assertEqual(r.status,'no_queue')
        r=self.plan(obs=self.obs(maximum_weight=51,currency_by_record={0:70}))
        self.assertEqual(r.status,'planned')
        self.assertEqual(self.plan(obs=self.obs(currency_by_record={0:69})).status,'no_queue')

    def test_cumulative_weight_and_cost_across_distinct_items(self):
        rows=[self.row(),self.row(item_id=99)]
        r=self.plan(rows,self.obs(maximum_weight=100,currency_by_record={0:1000}))
        self.assertEqual(r.accepted,((0,0,10),))
        r=self.plan(rows,self.obs(currency_by_record={0:70,1:139}))
        self.assertEqual(r.accepted,((0,0,10),))

    def test_currency_is_fresh_per_eligible_record(self):
        r=self.plan([self.row(),self.row(item_id=99)],self.obs(currency_by_record={0:1000}))
        self.assertEqual(r.status,'needs_observation');self.assertIsNone(r.payload)
        self.assertEqual(r.accepted,((0,0,10),));self.assertIn('record1',r.missing)

    def test_uint32_weight_cost_and_cumulative_wrap_preserved(self):
        row=self.row(desired_quantity=2,unit_weight=0x80000001,unit_cost=0x80000001)
        r=self.plan([row],self.obs(current_weight=0xffffffff,maximum_weight=2,currency_by_record={0:2}))
        self.assertEqual(r.status,'planned');self.assertEqual(r.accepted,((0,0,2),))

    def test_signed_quantity_compare_and_positive_delta_guard(self):
        obs=self.obs();cache=dict(obs.cache_slots)
        cache[14]=SellCacheSlot(0x12345678,1,0xffffffff)
        r=self.plan(obs=replace(obs,cache_slots=cache));self.assertEqual(r.accepted,((0,0,11),))
        # Source cache update wraps11 + FFFFFFFF to10.
        self.assertEqual(r.cache_writes[-3],(0x568f64,10))
        cache[14]=SellCacheSlot(0x12345678,1,0x80000000)
        self.assertEqual(self.plan(obs=replace(obs,cache_slots=cache)).status,'no_queue')

    def test_vendor_independent_ifs_last_match_wins_and_dc_exists(self):
        r=self.plan(obs=self.obs(vendor_matches={name:True for name,value in BUY_VENDORS}))
        self.assertEqual(r.payload[2:6],(0x43df0).to_bytes(4,'little'))
        r=self.plan(obs=self.obs(vendor_matches={name:name=='DC Sundries' for name,value in BUY_VENDORS}))
        self.assertEqual(r.payload[2:6],(0x412f8).to_bytes(4,'little'))

    def test_zero_vendor_and_npc_have_no_source_early_guard(self):
        r=self.plan(obs=self.obs(vendor_matches={name:False for name,value in BUY_VENDORS}),npc=0)
        self.assertEqual(r.status,'planned');self.assertEqual(r.payload[2:10],b'\0'*8)

    def test_zero_item_matches_first_empty_slot(self):
        r=self.plan([self.row(item_id=0)])
        self.assertEqual(r.accepted,((0,0,10),));self.assertEqual(r.payload[11:15],b'\0'*4)

    def test_empty_batch_still_refreshes_cache(self):
        r=self.plan([]);self.assertEqual(r.status,'no_queue');self.assertEqual(len(r.cache_writes),140)

    def test_missing_metadata_includes_partial_cache_intents(self):
        obs=self.obs();cache=dict(obs.cache_slots);cache[15]=SellCacheSlot(0,None,0)
        r=self.plan(obs=replace(obs,cache_slots=cache))
        self.assertEqual(r.status,'needs_observation');self.assertEqual(len(r.cache_writes),6)
        self.assertIsNone(r.payload)

    def test_missing_weight_vendor_or_cache_is_not_zero(self):
        for obs in (self.obs(current_weight=None),self.obs(vendor_matches={}),self.obs(cache_slots={})):
            self.assertEqual(self.plan(obs=obs).status,'needs_observation')

    def test_local_serializer_limit_explicitly_unresolved(self):
        # ID0 continually matches empty ID0; negative quantity permits repeated source additions.
        cache={slot:SellCacheSlot(0,0,0xffffffff) for slot in range(14,42)}
        # Vary targets to force each row to add one after the first wraps the cache.
        rows=[self.row(item_id=0,desired_quantity=i+1,unit_weight=0,unit_cost=0) for i in range(114)]
        r=self.plan(rows,self.obs(cache_slots=cache))
        self.assertEqual(r.status,'unresolved_serializer_limit');self.assertIsNone(r.payload)

    def test_observation_copies_and_typed_boundaries(self):
        currency={0:100};obs=self.obs(currency_by_record=currency);currency[0]=0
        self.assertEqual(obs.currency_by_record[0],100)
        for changes in ({'desired_quantity':65536},{'selector_a':256},{'unit_cost':-1}):
            with self.assertRaises(ValueError):self.row(**changes)
        with self.assertRaises(ValueError):self.plan(obs=self.obs(vendor_matches={'Sundries':1}))
