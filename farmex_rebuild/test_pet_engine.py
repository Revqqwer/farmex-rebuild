import unittest
from dataclasses import replace
from pet_engine import FOOD_IDS,PetFrame,PetObservation,plan_pet

def sample(extra=None,normal=None):
    v=dict(auto_initial=1,busy_vip_eax=0,busy_supply_eax=0,
        state_root_slot=0x1000,state_root_eax=0x2000,state_offset=0x10,state_eax=0,
        float_gate_root_slot=0x1000,float_gate_root_eax=0x2000,float_gate_offset=0x20,
        float_compare_status=0x4000,pet_exists_eax=1,auto_present=0,food_present=1,
        food_clock_eax=5000,food_last=0,hunger_eax=10,food_threshold=10,food_post_clock_eax=5010)
    v.update(extra or {})
    n={key[:-4]:True for key in v if key.endswith('_eax')};n['float_gate']=True
    n.update(normal or {})
    return PetObservation(v,n)

class PetEngineTests(unittest.TestCase):
    def test_disabled_and_vip_low_byte_short_circuit(self):
        p=plan_pet(PetObservation({'auto_initial':0,'food_initial':0}));self.assertEqual(p.status,'disabled');self.assertEqual(p.calls,())
        p=plan_pet(sample({'busy_vip_eax':0x100}));self.assertNotEqual(p.status,'vip_busy')
        self.assertEqual(plan_pet(sample({'busy_vip_eax':0x101})).status,'vip_busy')
    def test_float_status_is_explicit_and_separate(self):
        self.assertEqual(plan_pet(sample({'float_compare_status':0})).status,'character_float_gate')
        p=plan_pet(sample(normal={'float_gate':False}));self.assertEqual(p.needed,('normal_returns','float_gate'))
    def test_first_matching_food_slot_and_fresh_post_clock(self):
        p=plan_pet(sample({'food_item_14_eax':1,'food_item_15_eax':FOOD_IDS[2]}, {'feed':True}))
        self.assertEqual(p.status,'feed_returned');self.assertEqual(p.stores,((0x553c58,4,5010),))
        self.assertIn(('feed','00464ff8',(15,)),p.calls)
        self.assertFalse(any(c[0]=='food_item_16' for c in p.calls))
    def test_food_scan_inclusive_41_and_no_item_still_stamps(self):
        o=sample({'food_item_%d_eax'%i:0 for i in range(14,42)})
        p=plan_pet(o);self.assertEqual(p.status,'food_checked');self.assertEqual(p.calls[-2][2],(41,))
        self.assertEqual(p.stores,((0x553c58,4,5010),))
    def test_signed_threshold_word_hunger_and_timer_boundary(self):
        p=plan_pet(sample({'food_threshold':0xffffffff}));self.assertEqual(p.status,'food_checked')
        self.assertFalse(any(c[0].startswith('food_item_') for c in p.calls));self.assertEqual(len(p.stores),1)
        self.assertEqual(plan_pet(sample({'food_clock_eax':4999})).status,'food_timer')
        p=plan_pet(sample({'food_clock_eax':3,'food_last':0xffffec7b,'food_threshold':0}))
        self.assertEqual(p.status,'food_checked') # unsigned elapsed5000, hunger above threshold
    def test_mode_has_fresh_send_value_and_skips_food(self):
        p=plan_pet(sample(dict(auto_present=1,pet_mode_eax=1,mode_compare=2,mode_clock_eax=1000,
            mode_last=0,mode_send=3,mode_post_clock_eax=1009),{'set_mode':True}))
        self.assertEqual(p.status,'mode_returned');self.assertIn(('set_mode','004c7fe4',(0x561ef8,3)),p.calls)
        self.assertEqual(p.stores,((0x553c54,4,1009),));self.assertFalse(any(c[0]=='food_clock' for c in p.calls))
    def test_mode_timer_below_boundary_falls_through(self):
        p=plan_pet(sample(dict(auto_present=1,pet_mode_eax=1,mode_compare=2,mode_clock_eax=999,
            mode_last=0,food_present=0)))
        self.assertEqual(p.status,'food_disabled');self.assertEqual(p.stores,())
    def summon_sample(self,extra=None,normal=None):
        v=dict(pet_exists_eax=0,auto_absent=1,class_root_slot=0x1000,class_root_eax=0x2000,
          class_offset=0x30,class_eax=1,summon_item_eax=1,actor_root_slot=0x1000,
          actor_root_eax=0x2000,actor_offset=0x40,actor_eax=0,target_initial_eax=0,
          target_flag_root_slot=0x1000,target_flag_root_eax=0x2000,target_flag_offset=0x50,
          target_flag_eax=0,summon_ready_eax=0,summon_clock_eax=8000,self_id_eax=7)
        v.update(extra or {});return sample(v,{'summon':True,**(normal or {})})
    def test_absent_paths_and_test_clears_carry(self):
        self.assertEqual(plan_pet(self.summon_sample({'class_eax':6})).status,'class_six')
        p=plan_pet(self.summon_sample({'target_initial_eax':0xffffffff}))
        self.assertEqual(p.status,'summon_returned')
        self.assertIn(('target_flag','0045dc44',(0x2050,)),p.calls)
        self.assertEqual(p.stores,((0x561f80,4,0x2904),(0x561f84,4,8000),(0x561f7e,1,1)))
    def test_clear_target_rereads_and_does_not_use_initial_target(self):
        p=plan_pet(self.summon_sample({'actor_eax':3,'target_initial_eax':5,'target_flag_eax':1,
            'target_fresh_eax':9},{'cancel_actor':True,'clear_target':True}))
        self.assertIn(('clear_target','00465ef8',(9,0)),p.calls);self.assertEqual(p.status,'summon_returned')
    def test_partial_summon_keeps_prefix_and_consumed_clock(self):
        frame=PetFrame();o=self.summon_sample(normal={'summon':False})
        p=frame.advance(o);self.assertFalse(p.complete);self.assertEqual(len(p.stores),3)
        p=frame.advance(self.summon_sample({'summon_clock_eax':9999}))
        self.assertTrue(p.complete);self.assertEqual(p.stores[1][2],8000)
    def test_feed_return_and_post_clock_do_not_repeat_on_resume(self):
        frame=PetFrame();o=sample({'food_item_14_eax':FOOD_IDS[0]}, {'feed':True,'food_post_clock':False})
        p=frame.advance(o);self.assertEqual(p.needed,('normal_returns','food_post_clock'));self.assertEqual(p.stores,())
        p=frame.advance(sample({'food_item_14_eax':0,'food_post_clock_eax':6000}))
        self.assertEqual(p.status,'feed_returned');self.assertEqual(p.stores,((0x553c58,4,6000),))
        self.assertEqual(sum(c[0]=='feed' for c in p.calls),1)
    def test_captures_are_typed_and_copied(self):
        d={'auto_initial':0,'food_initial':0};o=PetObservation(d);d['auto_initial']=1
        self.assertEqual(plan_pet(o).status,'disabled')
        with self.assertRaises(ValueError):PetObservation({'auto_initial':True})
        with self.assertRaises(ValueError):plan_pet(PetObservation({'auto_initial':256}))

if __name__=='__main__':unittest.main()
