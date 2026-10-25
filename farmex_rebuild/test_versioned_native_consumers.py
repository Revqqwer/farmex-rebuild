import unittest
from dataclasses import replace
from native_profile_versions import *
from potion_packets import plan_alternate_potion
from potion_engine import PotionIntent
from storage_items import StorageSelection,StorageItemObservation,plan_storage_item
from storage_workers import VIP_BASE,INN_BASE,StorageObservation,storage_worker_step

def slot(returned=True,profile='us',helper='004fe290'):
    g=versioned_profile_globals(CURRENT_SOURCE_SHA256,profile,'storage');root=g[0x553e80];off=g[0x554128]
    table=g[0x55412c if helper=='004fe290' else 0x554130]
    return make_versioned_storage_observation(CURRENT_SOURCE_SHA256,profile,helper,0,
        protected_words={root:0x1000,0x1000+off:0x2000,0x2000+table:0x3000,0x3000:0x4000},
        direct_words={root:0x5000,0x5000+off:0x6000,0x6000:0x7000,0x7084:0x8000},normal_returned=returned)

def quantity(returned=True,sha=CURRENT_SOURCE_SHA256,profile='us'):
    return make_versioned_storage_observation(sha,profile,'004653a8',6,
        runtime_globals={0x553d20:0x9000},normal_returned=returned)

def confirmation():
    root=CURRENT_STORAGE_GLOBALS['us'][0x553f44]
    return make_versioned_storage_observation(CURRENT_SOURCE_SHA256,'us','00465334',1,
        protected_words={root:0x11000,0x11138:0xaa,0x1113c:0xbb},
        direct_words={root:0x12000,0x12000:0x13000,0x13084:0x14000},normal_returned=True)

def item(natives,dialogs=(1,0,0)):
    return StorageItemObservation('vip_stock_withdraw',0,StorageSelection(0,excluded_index_4e7be8=0),
        1,1,100,10,4,dialogs,native_observations=natives)

class VersionedPotionTests(unittest.TestCase):
    def intent(self,path='alternate',action=0x77a20):return PotionIntent('mp',0x172fe9c0,action,path,True)
    def obs(self,returned=None):
        return make_versioned_skill_observation(CURRENT_SOURCE_SHA256,'us',0x77a20,0x12345678,
            direct_words={0x1128a7c:0x100000,0x1004a8:0x200000},lookup_return=0x400000,native_return=returned)

    def test_matching_current_potion_keeps_source_identity_and_native_domain(self):
        p=plan_alternate_potion(self.intent(),self.obs(1))
        self.assertIsInstance(p,VersionedNativePlan)
        self.assertEqual(p.module_sha256,CURRENT_SOURCE_SHA256)
        self.assertEqual(p.plan.calls[0].target,0x5066b0);self.assertEqual(p.plan.calls[1].target,0x88eb50)
        self.assertEqual(p.plan.calls[1].push_order,(0x400000,0x12345678))
        self.assertFalse(p.native_execution_verified or p.game_image_verified)

    def test_missing_native_result_stays_unknown_and_does_not_become_packet(self):
        p=plan_alternate_potion(self.intent(),self.obs())
        self.assertIsNone(p.plan.returned_nonzero)
        self.assertFalse(hasattr(p,'payload'))

    def test_wrong_action_kind_and_direct_intent_are_rejected(self):
        for intent,o in ((self.intent(action=0x172fe9c0),self.obs()),(self.intent(path='direct'),self.obs()),(self.intent(),slot())):
            with self.assertRaises(ValueError):plan_alternate_potion(intent,o)

class VersionedItemTests(unittest.TestCase):
    def test_versioned_slot_plan_still_requires_separate_helper_normal_return(self):
        for returned in (None,False):
            p=plan_storage_item(VIP_BASE,item((slot(returned),)))
            self.assertEqual(p.status,'needs_observation');self.assertIn('normal return0',p.reason)
            self.assertIsNone(p.returned_value)
            self.assertEqual(p.native_plans[0].source_helper,'004fe290')
            self.assertEqual(p.native_plans[0].plan.status,'call_planned')

    def test_slot_quantity_confirm_chain_preserves_current_identity_on_every_leaf(self):
        p=plan_storage_item(VIP_BASE,item((slot(),quantity(),confirmation())))
        self.assertEqual(p.status,'native_calls_planned');self.assertEqual(p.returned_value,1)
        self.assertEqual([v.module_sha256 for v in p.native_plans],[CURRENT_SOURCE_SHA256]*3)
        self.assertEqual(p.native_plans[1].plan.memory_writes[1],(0x9000,b'6'))
        self.assertEqual(p.native_plans[2].plan.call.push_order,(1,0xaa))

    def test_quantity_return_gap_stops_before_next_confirmation(self):
        p=plan_storage_item(VIP_BASE,item((slot(),quantity(False),confirmation())))
        self.assertEqual(p.status,'needs_observation');self.assertIn('normal return1',p.reason)
        self.assertEqual(len(p.native_plans),2);self.assertEqual(p.calls[-1].address,'004653a8')

    def test_reached_version_or_profile_mix_is_rejected_but_unreached_mix_ignored(self):
        for other in (quantity(sha=LEGACY_SOURCE_SHA256),quantity(profile='steam'),quantity().observation):
            with self.assertRaises(ValueError):plan_storage_item(VIP_BASE,item((slot(),other)))
            p=plan_storage_item(VIP_BASE,item((slot(),other),dialogs=(0,0,0)))
            self.assertEqual(p.status,'native_calls_planned');self.assertEqual(len(p.native_plans),1)

    def test_wrong_role_rejected_only_after_source_early_skip(self):
        o=item((slot(helper='004fe318'),),dialogs=(0,0,0))
        with self.assertRaises(ValueError):plan_storage_item(VIP_BASE,o)
        p=plan_storage_item(VIP_BASE,replace(o,item_pointer=0))
        self.assertEqual(p.status,'skip');self.assertEqual(p.native_plans,())

class VersionedWorkerTests(unittest.TestCase):
    def page(self,returned):
        root=CURRENT_STORAGE_GLOBALS['us'][0x553e80]
        return make_versioned_storage_observation(CURRENT_SOURCE_SHA256,'us','0046fdf8',2,
            protected_words={root:0x1000,0x126c:0x2000,0x249c:0xaa,0x24a0:0xbb},
            direct_words={root:0x3000,0x326c:0x4000,0x4000:0x5000,0x5084:0x6000},normal_returned=returned)

    def test_page_keeps_prior_counter_but_blocks_on_helper_return(self):
        state={INN_BASE:1,INN_BASE+4:2,INN_BASE+0x10:23,0x561f60:1}
        o=StorageObservation(0,1,0,native_observations={'0046fdf8':self.page(None)})
        p=storage_worker_step(INN_BASE,state,o)
        self.assertEqual(p.status,'needs_observation');self.assertIn('page helper normal return',p.missing)
        self.assertEqual(p.globals[INN_BASE+0x10],24)
        self.assertEqual(p.native_plans[0].module_sha256,CURRENT_SOURCE_SHA256)
        p=storage_worker_step(INN_BASE,state,replace(o,native_observations={'0046fdf8':self.page(True)}))
        self.assertEqual(p.status,'page_planned');self.assertEqual(p.native_plans[0].plan.call.push_order,(1,0xbb))

    def test_worker_item_chain_cannot_advance_slot_on_missing_versioned_return(self):
        state={VIP_BASE:1,VIP_BASE+4:2,VIP_BASE+9:0,VIP_BASE+0x10:0,VIP_BASE+0x14:0,
               0x561f60:1,0x561f6f:0,0x561f58:0}
        selection=StorageSelection(0,excluded_4e7c60=False,list_index_41a5cc=1,list_checked_e2=True,protect_grade_5622cf=False)
        i=StorageItemObservation('vip_withdraw',0,selection,1,1,11,dialog_bytes=(0,0,0),native_observations=(slot(None),))
        o=StorageObservation(0,1,0,helpers={'004611a0':1,'004fe420':0},item_observations={'004ff074':i})
        p=storage_worker_step(VIP_BASE,state,o)
        self.assertEqual(p.status,'needs_observation');self.assertEqual(p.globals[VIP_BASE+0x10],0)
        self.assertEqual(p.item_plans[0].native_plans[0].source_helper,'004fe290')
        p=storage_worker_step(VIP_BASE,state,replace(o,item_observations={'004ff074':replace(i,native_observations=(slot(True),))}))
        self.assertEqual(p.status,'slot_planned');self.assertEqual(p.globals[VIP_BASE+0x10],1)

if __name__=='__main__':unittest.main()
