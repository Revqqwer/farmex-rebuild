import unittest
from dataclasses import replace
from source_coin import GuardedDwordSample as D,GuardedByteSample as B
from source_inn_cleanup import InnCleanupObservation as Obs,plan_inn_cleanup
from source_bank_item import BankItemObservation
from merchant_bank_count import BankCountObservation,plan_bank_count
from storage_inventory import StorageScanObservation
from storage_workers import INN_BASE,VIP_BASE,StorageObservation,storage_worker_step

def cleanup(value=1,api=0x12340001):
    return Obs(((0x553e80,0x1000),(0x5540bc,0x10),(0x5541fc,0x20)),
               (D(0x1000,1,0x2000),D(0x2010,1,0x3000)),B(0x3020,api,value))

def count():
    # Slot0 uses an actual operand chain, with a null record. Others have
    # independently supplied normal helper results; none are actual game reads.
    slot=BankItemObservation(((0x553e80,0),(0x5540bc,0),(0x5540c0,4)),(D(4,1,0),))
    return plan_bank_count(BankCountObservation((None,)+(1,)*190+(0,),(True,)*192,(slot,)))

class InnCleanupReadTests(unittest.TestCase):
    def test_order_and_full_eax_high_bits_do_not_change_exact_one_test(self):
        p=plan_inn_cleanup(cleanup())
        self.assertTrue(p.complete);self.assertEqual(p.open_byte,1)
        self.assertEqual(p.byte_plan.eax_dword,0x12340001)
        self.assertEqual(p.steps,(('global',0x553e80),('0045dc44',0x1000),
            ('global',0x5540bc),('0045dc44',0x2010),('global',0x5541fc),
            ('0045dbdc',0x3020),('MOV_CL_DEC_JNZ',1,0)))
        self.assertFalse(p.independently_verified)

    def test_null_chain_still_reads_offsets_and_consumes_no_dword_api_samples(self):
        o=Obs(((0x553e80,0),(0x5540bc,0),(0x5541fc,4)),(),B(4,1,2))
        p=plan_inn_cleanup(o)
        self.assertTrue(p.complete);self.assertEqual(p.open_byte,2)
        self.assertEqual([v.status for v in p.guarded_plans],['null_returns_zero']*2)

    def test_wrapped_addresses_and_null_byte_do_not_require_api_return(self):
        o=Obs(((0x553e80,0x1000),(0x5540bc,0xffffffff),(0x5541fc,8)),
              (D(0x1000,1,2),D(1,1,0xfffffff8)))
        p=plan_inn_cleanup(o)
        self.assertTrue(p.complete);self.assertEqual(p.open_byte,0)
        self.assertEqual(p.byte_plan.status,'null_returns_zero')

    def test_protection_failure_is_explicit_zero_and_unknown_is_not_zero(self):
        p=plan_inn_cleanup(cleanup(api=0))
        self.assertTrue(p.complete);self.assertEqual(p.open_byte,0)
        self.assertEqual(p.byte_plan.status,'protection_failure_returns_zero')
        self.assertFalse(p.byte_plan.native_effects_verified)
        for o in (replace(cleanup(),byte_sample=B(0x3020)),
                  replace(cleanup(),byte_sample=B(0x3020,1)),
                  replace(cleanup(),guarded_samples=(D(0x1000),))):
            p=plan_inn_cleanup(o);self.assertFalse(p.complete);self.assertIsNone(p.open_byte)

    def test_missing_globals_do_not_consume_later_samples(self):
        o=cleanup()
        for n in range(3):
            p=plan_inn_cleanup(replace(o,global_samples=o.global_samples[:n]))
            self.assertFalse(p.complete);self.assertIsNone(p.open_byte)
        p=plan_inn_cleanup(replace(o,global_samples=((0x553e80,None),)))
        self.assertEqual(p.guarded_plans,())

    def test_reached_address_order_and_types_rejected(self):
        for o in (replace(cleanup(),global_samples=((0x5540bc,0),)),
                  replace(cleanup(),guarded_samples=(D(0x9999,1,0),)),
                  replace(cleanup(),byte_sample=B(0x9999,1,1))):
            with self.assertRaises(ValueError):plan_inn_cleanup(o)
        with self.assertRaises(ValueError):Obs(byte_sample=D(1))
        with self.assertRaises(ValueError):Obs(global_samples=((0x553e80,True),))

class InnCleanupWorkerTests(unittest.TestCase):
    def state(self,cached=0,mode=0):
        return {INN_BASE:1,INN_BASE+8:1,INN_BASE+0x14:cached,0x561f60:0,0x561f58:mode}
    def obs(self,**changes):
        return replace(StorageObservation(10,bank_count_execution=count(),bank_count_returned=True,cleanup_inputs=cleanup(),cleanup_close_returned=True),**changes)
    def run_worker(self,state=None,obs=None):
        return storage_worker_step(INN_BASE,self.state() if state is None else state,self.obs() if obs is None else obs)

    def test_slot_operand_to_count_to_inn_cleanup_and_npc_projection(self):
        p=self.run_worker()
        self.assertEqual(p.status,'finished_plan');self.assertEqual(p.globals[INN_BASE+0x14],2)
        self.assertEqual(p.globals[INN_BASE],0);self.assertEqual(p.globals[INN_BASE+8],0)
        self.assertEqual([v.address for v in p.calls],['0046ff6c','0046fd90'])
        self.assertEqual(p.bank_count_plans[0].zero_slots,(0,191))
        self.assertEqual(len(p.bank_count_plans[0].item_plans),1)
        self.assertEqual(p.cleanup_plans[0].open_byte,1)
        from npc_route_engine import NpcRouteFrame
        frame=p.apply_to_npc(NpcRouteFrame(0))
        self.assertEqual(frame.globals[INN_BASE+0x14],2)

    def test_count_normal_return_gap_prevents_count_store_and_cleanup_read(self):
        for returned in (None,False):
            p=self.run_worker(self.state(mode=4),self.obs(bank_count_returned=returned))
            self.assertEqual(p.status,'needs_observation');self.assertIn('normal return',p.missing)
            self.assertEqual(p.globals[0x569870],1)
            self.assertEqual(p.globals[INN_BASE+0x14],0);self.assertEqual(p.globals[INN_BASE],1)
            self.assertEqual(p.cleanup_plans,());self.assertEqual(p.bank_count_plans,())

    def test_partial_count_does_not_store_prefix_or_reach_cleanup(self):
        partial=plan_bank_count(BankCountObservation((0,),(True,)))
        p=self.run_worker(obs=self.obs(bank_count_execution=partial))
        self.assertEqual(p.status,'needs_observation');self.assertEqual(p.globals[INN_BASE+0x14],0)
        self.assertEqual(p.bank_count_plans,(partial,));self.assertEqual(p.cleanup_plans,())

    def test_count_store_survives_later_cleanup_gap_and_cached_retry_skips_count(self):
        p=self.run_worker(obs=self.obs(cleanup_inputs=Obs()))
        self.assertEqual(p.status,'needs_observation');self.assertEqual(p.globals[INN_BASE+0x14],2)
        self.assertEqual(p.globals[INN_BASE],1);self.assertEqual(p.globals[INN_BASE+8],1)
        retry=self.run_worker(p.globals,self.obs(bank_count_returned=None))
        self.assertEqual(retry.status,'finished_plan');self.assertEqual(retry.bank_count_plans,())
        self.assertEqual([v.address for v in retry.calls],['0046fd90'])

    def test_only_exact_one_calls_close_and_zero_count_is_recounted_next_attempt(self):
        for value in (0,1,2,255):
            p=self.run_worker(obs=self.obs(cleanup_inputs=cleanup(value)))
            self.assertEqual('0046fd90' in [v.address for v in p.calls],value==1)
        empty=plan_bank_count(BankCountObservation((1,)*192,(True,)*192))
        p=self.run_worker(obs=self.obs(bank_count_execution=empty,cleanup_inputs=Obs()))
        self.assertEqual(p.globals[INN_BASE+0x14],0)
        retry=self.run_worker(p.globals,self.obs(bank_count_returned=None))
        self.assertIn('normal return',retry.missing);self.assertEqual(retry.cleanup_plans,())

    def test_reached_conflicts_rejected_but_cached_counter_skips_them(self):
        for extra in ({'helpers':{'0046ff6c':9}},
                      {'scan_observations':{'0046ff6c':StorageScanObservation('inn_free')}}):
            with self.assertRaises(ValueError):self.run_worker(obs=self.obs(**extra))
            p=self.run_worker(self.state(cached=9),self.obs(**extra))
            self.assertEqual(p.status,'finished_plan');self.assertEqual(p.bank_count_plans,())
        with self.assertRaises(ValueError):self.run_worker(obs=self.obs(cleanup_open_byte=1))

    def test_noncleanup_inn_and_vip_do_not_consume_bound_inn_inputs(self):
        o=self.obs(cleanup_open_byte=1,helpers={'0046ff6c':9})
        state=self.state();state.update({0x561f60:1,INN_BASE+4:1,INN_BASE+0xc:0})
        p=self.run_worker(state,replace(o,open_byte=1,busy_byte=0))
        self.assertEqual(p.status,'slot_planned');self.assertEqual(p.cleanup_plans,())
        p=storage_worker_step(VIP_BASE,{VIP_BASE:1,0x561f60:0},o)
        self.assertEqual(p.status,'finished_plan');self.assertEqual(p.bank_count_plans,());self.assertEqual(p.cleanup_plans,())

    def test_observation_rejects_untyped_bindings(self):
        for changes in ({'bank_count_execution':{}},{'bank_count_returned':1},{'cleanup_inputs':{}},{'cleanup_close_returned':1}):
            with self.assertRaises(ValueError):self.obs(**changes)

    def test_close_return_is_separate_from_known_open_byte_before_flag_clears(self):
        for returned in (None,False):
            p=self.run_worker(obs=self.obs(cleanup_close_returned=returned))
            self.assertEqual(p.status,'needs_observation');self.assertIn('close helper normal return',p.missing)
            self.assertEqual(p.globals[INN_BASE+0x14],2)
            self.assertEqual(p.globals[INN_BASE],1);self.assertEqual(p.globals[INN_BASE+8],1)
            self.assertEqual([v.address for v in p.calls],['0046ff6c','0046fd90'])

    def test_non_one_cleanup_skips_unused_close_return_receipt(self):
        for value in (0,2,255):
            p=self.run_worker(obs=self.obs(cleanup_inputs=cleanup(value),cleanup_close_returned=None))
            self.assertEqual(p.status,'finished_plan')
            self.assertEqual([v.address for v in p.calls],['0046ff6c'])

if __name__=='__main__':unittest.main()
