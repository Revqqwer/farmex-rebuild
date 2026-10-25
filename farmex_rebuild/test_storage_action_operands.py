import unittest
from dataclasses import replace
from source_coin import GuardedDwordSample as D
from storage_action_operands import StorageActionSamples as Samples,plan_storage_action
from storage_native_plans import SLOTS,NativeHelperObservation as Native,plan_native_helper
from storage_items import StorageItemObservation,StorageSelection,plan_storage_item
from storage_workers import INN_BASE,VIP_BASE,StorageObservation,storage_worker_step

def slot(helper='004fe274',argument=0):
    context_key,slots_key,_=SLOTS[helper]
    return Samples(((0x553e80,0x1000),(context_key,0x20),(slots_key,0x100),
        (0x553e80,0x1100),(context_key,0x30),(0x554200,0x24)),
        (D(0x1000,1,0x2000),D(0x2020,1,0x3000),D((0x3100+(argument<<2))&0xffffffff,1,0x8000),D(0x8000,1,0x9000)),
        ((0x1100,0x4000),(0x4030,0x5000),(0x5000,0x6000),(0x6024,0x7000)))

def buttons(page=False):
    if page:
        return Samples(((0x553e80,0x1000),(0x5540bc,0x20),(0x5540cc,0x10),(0x5540d0,0x14),
                         (0x553e80,0x1100),(0x5540bc,0x30),(0x554200,0x24)),
                       (D(0x1000,1,0x2000),D(0x2020,1,0x3000),D(0x3010,1,0xaa),D(0x3014,1,0xbb)),
                       ((0x1100,0x4000),(0x4030,0x5000),(0x5000,0x6000),(0x6024,0x7000)))
    return Samples(((0x553f44,0x1000),(0x554138,0x10),(0x55413c,0x14),(0x553f44,0x1100),(0x554200,0x24)),
                   (D(0x1000,1,0x2000),D(0x2010,1,0xaa),D(0x2014,1,0xbb)),
                   ((0x1100,0x3000),(0x3000,0x4000),(0x4024,0x7000)))

class OrderedActionTests(unittest.TestCase):
    def test_all_four_helpers_use_fresh_global_root_and_context(self):
        for helper in SLOTS:
            p=plan_storage_action(helper,0,slot(helper))
            self.assertTrue(p.complete);self.assertEqual(p.status,'call_planned')
            self.assertEqual((p.call.target,p.call.ecx,p.call.push_order),(0x7000,0x5000,(0x4000000,0x9000)))
            self.assertEqual(p.call.preserve_gprs_and_flags,helper.startswith('0046'))
            self.assertFalse(p.call.abi_verified);self.assertFalse(p.independently_verified)
            self.assertEqual([s for s in p.steps if s[0]=='direct'],
                [('direct',0x1100),('direct',0x4030),('direct',0x5000),('direct',0x6024)])
            self.assertEqual(('PUSHAD',) in p.steps,helper.startswith('0046'))

    def test_slot_shift_wrap_and_push_before_indirect_call(self):
        p=plan_storage_action('0046fd04',0x40000000,slot('0046fd04',0x40000000))
        self.assertIn(('slot_shift_low32',0x40000000,0),p.steps)
        self.assertEqual(p.steps[-5:],(('PUSH',0x4000000),('PUSH',0x9000),
                         ('indirect_call_plan',0x7000,0x5000),('POPFD',),('POPAD',)))

    def test_same_direct_address_can_change_between_two_source_reads(self):
        o=slot();o=replace(o,direct_samples=((0x1100,0x10d0),(0x1100,0x5000),
                                           (0x5000,0x6000),(0x6024,0x7000)))
        p=plan_storage_action('004fe274',0,o)
        self.assertTrue(p.complete);self.assertEqual(p.call.ecx,0x5000)
        self.assertEqual([s for s in p.steps if s[0]=='direct'][:2],[('direct',0x1100)]*2)

    def test_zero_slot_or_zero_first_value_skip_dispatch_tail(self):
        o=slot()
        for n in (2,3):
            guards=o.guarded_samples[:n]+(replace(o.guarded_samples[n],value_dword=0),)
            p=plan_storage_action('004fe274',0,replace(o,guarded_samples=guards,global_samples=o.global_samples[:3],direct_samples=()))
            self.assertTrue(p.complete);self.assertEqual(p.status,'no_call');self.assertIsNone(p.call)

    def test_guarded_nulls_continue_offsets_and_failed_protection_can_skip(self):
        o=Samples(((0x553e80,0),(0x5540bc,0),(0x5540c0,4)),(D(4,0),))
        p=plan_storage_action('0046fd04',0,o)
        self.assertEqual(p.status,'no_call')
        self.assertEqual([g.status for g in p.guarded_plans],['null_returns_zero','null_returns_zero','protection_failure_returns_zero'])

    def test_every_slot_prefix_gap_stays_unknown_instead_of_reusing_old_reads(self):
        o=slot()
        for field,count in (('global_samples',6),('guarded_samples',4),('direct_samples',4)):
            for n in range(count):
                p=plan_storage_action('004fe274',0,replace(o,**{field:getattr(o,field)[:n]}))
                self.assertFalse(p.complete);self.assertIsNone(p.call)

    def test_reached_global_guard_and_direct_order_mismatch_rejected(self):
        o=slot()
        for changed in (replace(o,global_samples=((0x554128,0),)),
                        replace(o,guarded_samples=(D(0x1100,1,0),)),
                        replace(o,direct_samples=((0x1000,0x4000),))):
            with self.assertRaises(ValueError):plan_storage_action('004fe274',0,changed)

    def test_confirm_and_page_have_distinct_low_byte_selection(self):
        for page,helper in ((False,'00465334'),(True,'0046fdf8')):
            for arg in (0,1,2,256,257):
                first=(arg&255)==1 if page else bool(arg&255)
                p=plan_storage_action(helper,arg,buttons(page))
                self.assertTrue(p.complete);self.assertEqual(p.call.push_order,(1,0xaa if first else 0xbb))
                self.assertEqual(p.call.ecx,0x5000 if page else 0x3000)
                pushes=[i for i,s in enumerate(p.steps) if s[0]=='PUSH']
                offset=p.steps.index(('global',0x554200))
                self.assertTrue(all(i<offset for i in pushes))

    def test_both_buttons_are_read_before_selection_even_if_unused(self):
        for page,helper in ((False,'00465334'),(True,'0046fdf8')):
            o=buttons(page)
            p=plan_storage_action(helper,1,replace(o,guarded_samples=o.guarded_samples[:-1]))
            self.assertFalse(p.complete);self.assertIsNone(p.call)
            self.assertFalse(any(s[0]=='select_first' for s in p.steps))

    def test_direct_null_requires_observation_and_zero_target_is_not_abi_proof(self):
        o=buttons();o=replace(o,direct_samples=((0x1100,0),))
        p=plan_storage_action('00465334',1,o)
        self.assertFalse(p.complete);self.assertIn('00000000',p.missing)
        o=replace(o,direct_samples=((0x1100,0),(0,0),(0x24,0)))
        p=plan_storage_action('00465334',1,o)
        self.assertTrue(p.complete);self.assertEqual(p.call.target,0);self.assertFalse(p.call.abi_verified)

    def test_protected_api_unknown_is_distinct_from_zero_failure(self):
        o=slot()
        for changed in (replace(o,guarded_samples=(D(0x1000),)),
                        replace(o,guarded_samples=(D(0x1000,1),))):
            p=plan_storage_action('004fe274',0,changed)
            self.assertFalse(p.complete);self.assertIsNone(p.call)

class OrderedActionBindingTests(unittest.TestCase):
    def item(self,natives):
        return StorageItemObservation('vip_stock_withdraw',0,StorageSelection(0,excluded_index_4e7be8=0),
            1,1,100,10,4,(1,0,0),native_observations=natives)
    def native(self,helper='004fe274',argument=0,returned=True):
        return Native(helper,argument,operand_samples=slot(helper,argument),normal_returned=returned)

    def test_native_facade_retains_exact_ordered_child_and_returns_no_writes(self):
        p=plan_native_helper(self.native())
        self.assertEqual(p.status,'call_planned');self.assertTrue(p.ordered_plan.complete)
        self.assertEqual(p.memory_writes,());self.assertEqual(dict(p.globals),{})
        self.assertEqual(p.call.ecx,0x5000)

    def test_item_binding_requires_separate_action_normal_return_before_dialog(self):
        for returned in (None,False):
            p=plan_storage_item(VIP_BASE,self.item((self.native(returned=returned),)))
            self.assertEqual(p.status,'needs_observation');self.assertIn('normal return0',p.reason)
            self.assertEqual(p.calls[-1].address,'004fe274');self.assertIsNone(p.returned_value)
            self.assertTrue(p.native_plans[0].ordered_plan.complete)

    def test_item_ordered_slot_quantity_and_confirm_chain(self):
        natives=(self.native(),Native('004653a8',6,{0x553d20:0x9000}),
                 Native('00465334',1,operand_samples=buttons(),normal_returned=True))
        p=plan_storage_item(VIP_BASE,self.item(natives))
        self.assertEqual(p.status,'native_calls_planned');self.assertEqual(p.returned_value,1)
        self.assertEqual(p.native_plans[1].memory_writes[1],(0x9000,b'6'))
        self.assertEqual(p.native_plans[2].call.push_order,(1,0xaa))
        p=plan_storage_item(VIP_BASE,self.item(natives[:2]+(replace(natives[2],normal_returned=None),)))
        self.assertEqual(p.status,'needs_observation');self.assertIn('normal return2',p.reason)

    def test_outer_page_prefix_counter_retained_on_action_return_gap(self):
        state={INN_BASE:1,INN_BASE+4:2,INN_BASE+0x10:23,0x561f60:1}
        n=Native('0046fdf8',2,operand_samples=buttons(True))
        o=StorageObservation(0,1,0,native_observations={'0046fdf8':n})
        p=storage_worker_step(INN_BASE,state,o)
        self.assertEqual(p.status,'needs_observation');self.assertEqual(p.globals[INN_BASE+0x10],24)
        self.assertIn('page helper normal return',p.missing)
        p=storage_worker_step(INN_BASE,state,replace(o,native_observations={'0046fdf8':replace(n,normal_returned=True)}))
        self.assertEqual(p.status,'page_planned');self.assertEqual(p.native_plans[0].call.push_order,(1,0xbb))

    def test_wrong_helper_argument_and_stable_map_conflicts_rejected(self):
        with self.assertRaises(ValueError):Native('004fe274',0,{0x553e80:0},operand_samples=slot())
        with self.assertRaises(ValueError):Native('004653a8',0,operand_samples=slot())
        with self.assertRaises(ValueError):Native('004fe274',0,operand_samples={})
        with self.assertRaises(ValueError):Native('004fe274',0,normal_returned=1)
        with self.assertRaises(ValueError):plan_storage_item(VIP_BASE,self.item((self.native(argument=1),)))

    def test_unreached_empty_item_ignores_native_action(self):
        p=plan_storage_item(VIP_BASE,replace(self.item((self.native(),)),item_pointer=0))
        self.assertEqual(p.status,'skip');self.assertEqual(p.native_plans,())

if __name__=='__main__':unittest.main()
