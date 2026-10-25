import unittest
from dataclasses import replace
from storage_native_plans import NativeHelperObservation,plan_native_helper,SLOTS
from storage_items import StorageSelection,StorageItemObservation,plan_storage_item
from storage_workers import INN_BASE,StorageObservation,storage_worker_step

class NativePlanTests(unittest.TestCase):
    def slot_obs(self,helper='004fe274',argument=0):
        context_key,slots_key,preserve=SLOTS[helper]
        return NativeHelperObservation(helper,argument,{0x553e80:0x1000,context_key:0x20,slots_key:0x100,0x554200:0x24},
          {0x1000:0x2000,0x2020:0x3000,(0x3100+(argument*4&0xffffffff))&0xffffffff:0x8000,0x8000:0x9000},
          {0x1000:0x4000,0x4020:0x5000,0x5000:0x6000,0x6024:0x7000})
    def button_obs(self,helper='00465334',argument=1):
        if helper=='00465334':
            return NativeHelperObservation(helper,argument,{0x553f44:0x1000,0x554138:0x10,0x55413c:0x14,0x554200:0x24},
                {0x1000:0x2000,0x2010:0xaa,0x2014:0xbb},
                {0x1000:0x3000,0x3000:0x4000,0x4024:0x7000})
        return NativeHelperObservation(helper,argument,{0x553e80:0x1000,0x5540bc:0x20,0x5540cc:0x10,0x5540d0:0x14,0x554200:0x24},
            {0x1000:0x2000,0x2020:0x3000,0x3010:0xaa,0x3014:0xbb},
            {0x1000:0x4000,0x4020:0x5000,0x5000:0x6000,0x6024:0x7000})

    def test_slot_helpers_ecx_push_order_and_two_distinct_root_observations(self):
        for helper in SLOTS:
            r=plan_native_helper(self.slot_obs(helper))
            self.assertEqual(r.status,'call_planned');self.assertEqual(r.call.target,0x7000)
            self.assertEqual(r.call.ecx,0x5000);self.assertEqual(r.call.push_order,(0x04000000,0x9000))
            self.assertFalse(r.call.abi_verified)
            self.assertEqual(r.call.preserve_gprs_and_flags,helper.startswith('0046'))
            self.assertEqual(r.reads,(('protected',0x1000),('protected',0x2020),('protected',0x3100),
                                     ('protected',0x8000),('direct',0x1000),('direct',0x4020),
                                     ('direct',0x5000),('direct',0x6024)))

    def test_guard_null_slot_or_first_word_exits_before_direct_root(self):
        for address in (0x3100,0x8000):
            obs=self.slot_obs();words=dict(obs.protected_words);words[address]=0
            r=plan_native_helper(replace(obs,protected_words=words,direct_words={}))
            self.assertEqual(r.status,'no_call');self.assertIsNone(r.call)

    def test_slot_index_shift_and_pointer_addition_wrap(self):
        r=plan_native_helper(self.slot_obs(argument=0x40000000))
        self.assertEqual(r.reads[2],('protected',0x3100));self.assertEqual(r.status,'call_planned')

    def test_missing_direct_root_is_not_guard_root_reuse(self):
        r=plan_native_helper(replace(self.slot_obs(),direct_words={}))
        self.assertEqual(r.status,'needs_observation');self.assertIn('direct DWORD00001000',r.missing)

    def test_null_target_is_only_a_source_call_plan_never_abi_verified(self):
        obs=self.slot_obs();words=dict(obs.direct_words);words[0x6024]=0
        r=plan_native_helper(replace(obs,direct_words=words))
        self.assertEqual(r.call.target,0);self.assertFalse(r.call.abi_verified)

    def test_confirm_low_byte_zero_or_nonzero_selects_button(self):
        for argument,button in ((0,0xbb),(1,0xaa),(2,0xaa),(256,0xbb)):
            r=plan_native_helper(self.button_obs(argument=argument))
            self.assertEqual(r.call.ecx,0x3000);self.assertEqual(r.call.push_order,(1,button))

    def test_confirm_reads_both_buttons_even_when_one_selected(self):
        obs=self.button_obs();words=dict(obs.protected_words);del words[0x2014]
        self.assertEqual(plan_native_helper(replace(obs,protected_words=words)).status,'needs_observation')

    def test_page_low_byte_exact1_other_values_choose_second(self):
        for argument,button in ((1,0xaa),(257,0xaa),(0,0xbb),(2,0xbb)):
            r=plan_native_helper(self.button_obs('0046fdf8',argument))
            self.assertEqual(r.call.ecx,0x5000);self.assertEqual(r.call.push_order,(1,button))

    def test_quantity_signed_int_to_str_and_four_write_intents(self):
        r=plan_native_helper(NativeHelperObservation('004653a8',0xffffffff,{0x553d20:0x9000}))
        self.assertEqual(r.status,'writes_planned');self.assertEqual(r.text,'-1')
        self.assertEqual(r.memory_writes,((0x9000,b'\0'*14),(0x9000,b'-1'),(0x9010,b'\x02'),(0x9028,b'\0')))
        self.assertEqual(r.reads,());self.assertIsNone(r.call)

    def test_quantity_cached_address_derivation_updates_only_model_globals(self):
        obs=NativeHelperObservation('004653a8',42,{0x553d20:0,0x553f48:0x1000,0x554134:0x40},{0x1000:0x9000})
        r=plan_native_helper(obs)
        self.assertEqual(r.globals[0x553d20],0x9040);self.assertEqual(obs.globals[0x553d20],0)
        self.assertEqual(r.memory_writes[1],(0x9040,b'42'))

    def test_quantity_zero_formats_one_character(self):
        r=plan_native_helper(NativeHelperObservation('004653a8',0,{0x553d20:0x9000}))
        self.assertEqual(r.memory_writes[1],(0x9000,b'0'));self.assertEqual(r.memory_writes[2],(0x9010,b'\x01'))

    def test_quantity_eight_bytes_fit_longer_values_unresolved_before_game_write(self):
        for value in (99999999,(-9999999)&0xffffffff):
            r=plan_native_helper(NativeHelperObservation('004653a8',value,{0x553d20:0x9000}))
            self.assertEqual(r.status,'writes_planned');self.assertEqual(len(r.text),8)
        for value in (100000000,0x7fffffff,0x80000000):
            r=plan_native_helper(NativeHelperObservation('004653a8',value))
            self.assertEqual(r.status,'unresolved_stack_buffer_overwrite');self.assertEqual(r.memory_writes,())

    def test_quantity_missing_cache_or_root_stays_unknown(self):
        for obs in (NativeHelperObservation('004653a8',1),NativeHelperObservation('004653a8',1,{0x553d20:0,0x553f48:0x1000,0x554134:0x40})):
            self.assertEqual(plan_native_helper(obs).status,'needs_observation')

    def item(self,native=()):
        return StorageItemObservation('vip_stock_withdraw',0,StorageSelection(0,excluded_index_4e7be8=0),1,1,100,10,4,(1,0,0),native_observations=native)

    def test_item_operation_quantity_and_confirm_native_bindings(self):
        native=(self.slot_obs(),NativeHelperObservation('004653a8',6,{0x553d20:0x9000}),self.button_obs())
        r=plan_storage_item(0x5690b8,self.item(native))
        self.assertEqual(r.returned_value,1);self.assertEqual(len(r.native_plans),3)
        self.assertEqual(r.native_plans[1].memory_writes[1],(0x9000,b'6'))

    def test_item_missing_later_native_observation_not_success(self):
        r=plan_storage_item(0x5690b8,self.item((self.slot_obs(),)))
        self.assertEqual(r.status,'needs_observation');self.assertIsNone(r.returned_value)

    def test_item_native_helper_argument_conflict_rejected(self):
        for supplied in (self.slot_obs(argument=1),self.slot_obs('004fe2fc')):
            with self.assertRaises(ValueError):plan_storage_item(0x5690b8,self.item((supplied,)))

    def test_outer_inn_page_binding_uses_second_button(self):
        state={INN_BASE:1,INN_BASE+4:2,INN_BASE+0x10:23,0x561f60:1}
        obs=StorageObservation(0,1,0,native_observations={'0046fdf8':self.button_obs('0046fdf8',2)})
        r=storage_worker_step(INN_BASE,state,obs)
        self.assertEqual(r.status,'page_planned');self.assertEqual(r.globals[INN_BASE+0x10],24)
        self.assertEqual(r.native_plans[0].call.push_order,(1,0xbb))

    def test_outer_page_missing_direct_read_keeps_explicit_partial_source_counter(self):
        state={INN_BASE:1,INN_BASE+4:2,INN_BASE+0x10:23,0x561f60:1}
        supplied=replace(self.button_obs('0046fdf8',2),direct_words={})
        r=storage_worker_step(INN_BASE,state,StorageObservation(0,1,0,native_observations={'0046fdf8':supplied}))
        self.assertEqual(r.status,'needs_observation');self.assertEqual(r.globals[INN_BASE+0x10],24)
        self.assertIsNone(r.native_plans[0].call)

    def test_observations_copy_and_reject_non_dwords(self):
        words={0x1000:0x9000};obs=NativeHelperObservation('004653a8',1,{0x553d20:0,0x553f48:0x1000,0x554134:0},words)
        words.clear();self.assertEqual(plan_native_helper(obs).status,'writes_planned')
        with self.assertRaises(ValueError):NativeHelperObservation('004653a8',-1)
        with self.assertRaises(ValueError):NativeHelperObservation('004653a8',1,{0:True})
