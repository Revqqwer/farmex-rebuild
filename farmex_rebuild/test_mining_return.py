import unittest
from mining_return import *

def cfg(sell=1,bank=1,mode=1):return MiningPanelConfiguration('fixture',{0x6044:sell,0x6045:bank,0x5ff8:mode})
def obs(**kw):
    data=dict(sell_476c7c=1,bank_476d44=1,region_1_equal=0,region_2_equal=0,region_3_equal=1,
        distance_fpu_ah=0x40,use_constructor_defaults=1,**{'returned:004eb9f4':True})
    data.update(kw);return data

class MiningReturnTests(unittest.TestCase):
    def test_all16_source_selection_combinations(self):
        # Availability order: neither, sell-only, bank-only, both.
        expected={(0,0):(4,0,0,0),(1,0):(4,2,0,2),(0,1):(4,0,3,3),(1,1):(4,2,3,1)}
        for flags,row in expected.items():
            for availability,selector in zip(((0,0),(1,0),(0,1),(1,1)),row):
                with self.subTest(flags=flags,availability=availability):
                    p=plan_mining_return(cfg(*flags),obs(sell_476c7c=availability[0],bank_476d44=availability[1]))
                    self.assertTrue(p.complete);self.assertEqual(p.selector,selector)
                    self.assertEqual(p.route.name if p.route else '',('MoradonMiningRoute'+str(selector)) if selector else '')

    def test_emc_luferson_nearest_families_and_signed_tie(self):
        for region,first,second,family in ((1,10,9,'EMCRMiningRoute'),(1,10,10,'EMCMiningRoute'),
            (1,0xffffffff,0,'EMCMiningRoute'),(2,10,9,'LFCRMiningRoute'),(2,9,10,'LFCMiningRoute')):
            p=plan_mining_return(cfg(),obs(region_1_equal=int(region==1),region_2_equal=int(region==2),
                distance_first_ftol=first,distance_second_ftol=second))
            self.assertTrue(p.complete);self.assertEqual(p.family,family)
            self.assertEqual(p.route.name,family+'1')

    def test_manual_mode_still_reads_candidates_before_route(self):
        c=MiningPanelConfiguration('fixture',{0x5ff8:3})
        p=plan_mining_return(c,{})
        self.assertEqual(p.missing,'sell_476c7c')
        p=plan_mining_return(c,obs(**{'returned:004ebca0':True}))
        self.assertTrue(p.complete);self.assertEqual(p.selector,0)
        self.assertEqual(p.calls,(('004ebca0',(0x5687a8,('literal',0x5292b0))),))

    def test_manual_route_does_not_skip_town_segment(self):
        p=plan_mining_return(cfg(mode=3),obs(distance_fpu_ah=0,
            **{'returned:004ebca0':True,'returned:00465678':True}))
        self.assertTrue(p.complete);self.assertEqual([a for a,_ in p.calls],['004ebca0','00465678'])
        self.assertIsNone(p.route)

    def test_emc4_incomplete_constructor_stays_a_gap(self):
        p=plan_mining_return(cfg(),obs(sell_476c7c=0,bank_476d44=0,region_1_equal=1,
            distance_first_ftol=10,distance_second_ftol=20))
        self.assertFalse(p.complete);self.assertEqual(p.route.name,'EMCMiningRoute4')
        self.assertEqual(p.route.status,'incomplete_source_route')

    def test_default_constructor_not_silently_runtime_vector(self):
        o=obs();del o['use_constructor_defaults']
        self.assertEqual(plan_mining_return(cfg(),o).missing,'use_constructor_defaults')
        o['use_constructor_defaults']=0
        self.assertEqual(plan_mining_return(cfg(),o).missing,'fresh_return_route_vector')

    def test_no_candidate_skips_auto_flag_reads(self):
        c=MiningPanelConfiguration('fixture',{0x5ff8:1})
        p=plan_mining_return(c,obs(sell_476c7c=0,bank_476d44=0))
        self.assertTrue(p.complete);self.assertEqual(p.selector,4)

    def test_town_normal_return_needed_before_route_payload(self):
        p=plan_mining_return(cfg(),obs(distance_fpu_ah=0))
        self.assertFalse(p.complete);self.assertEqual(p.missing,'returned:00465678')
        self.assertIsNone(p.route)

    def test_noncanonical_al_values_are_nonzero(self):
        p=plan_mining_return(cfg(),obs(sell_476c7c=2,bank_476d44=255))
        self.assertTrue(p.complete);self.assertEqual(p.selector,1)

    def test_all20_dispatch_destinations_and_one_known_incomplete_route(self):
        for family,region,first,second in (('EMCMiningRoute',1,10,20),('EMCRMiningRoute',1,20,10),
            ('LFCMiningRoute',2,10,20),('LFCRMiningRoute',2,20,10),('MoradonMiningRoute',3,10,20)):
            for selector in range(1,5):
                flags={1:(1,1),2:(1,0),3:(0,1),4:(0,0)}[selector]
                available=0 if selector==4 else 1
                p=plan_mining_return(cfg(*flags),obs(sell_476c7c=available,bank_476d44=available,
                    region_1_equal=int(region==1),region_2_equal=int(region==2),
                    distance_first_ftol=first,distance_second_ftol=second))
                with self.subTest(family=family,selector=selector):
                    self.assertEqual(p.route.name,family+str(selector))
                    self.assertEqual(p.complete,p.route.name!='EMCMiningRoute4')

if __name__=='__main__':unittest.main()
