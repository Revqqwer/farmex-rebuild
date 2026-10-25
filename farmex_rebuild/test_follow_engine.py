import unittest
from dataclasses import replace
from follow_engine import *
from source_unicode import UnicodeEqualityObservation as Eq

def equality(left,right):return Eq(helper_returned=True,use_owned_text_model=True,left_text=left,right_text=right)
def ready(**changes):
    returns={k:True for k in ('party_count','entity_lookup','coord_x','coord_y','distance','movement',
                             'initialize_previous_name','empty_temporary_cleanup','copy_previous_name','name_lookup')}
    return replace(FollowObservation(entry_reached=True,second_mode_dword=2,party_count_dword=1,
        leader_id_word=65535,pointer_dword=0x1000,name_id_dword=99,initialized_previous_name='',
        empty_equal=equality('Alice',''),previous_equal=equality('Alice','Alice'),
        coordinate_offsets=(0x10,0x20),coordinate_bits=(0x41200000,0x41a00000),
        distance_status_word=0,manual_y_after_add_bits=0x41c00000,helper_returns=returns),**changes)

class FollowTests(unittest.TestCase):
    def leader(self,o=None,c=None):return plan_follow_tail(c or FollowConfiguration(1,1,'Alice'),FollowState(),o or ready())
    def manual(self,o=None,state=None):return plan_follow_tail(FollowConfiguration(1,2,'Alice'),state or FollowState(1,'Alice',7),o or ready())

    def test_panel_reads_leader_radio_only_and_preserves_unicode(self):
        values={ROOT+'chFollow':True,ROOT+'rdFollowPartyLeader':True,ROOT+'rdFollowManuelNick':True,ROOT+'txtFollowNick':'A\0\U0001f600'}
        c=compile_follow_panel(values);self.assertEqual(c.mode_dword,1);self.assertEqual(c.nickname,values[ROOT+'txtFollowNick'])
        values[ROOT+'rdFollowPartyLeader']=False;values[ROOT+'rdFollowManuelNick']=False
        self.assertEqual(compile_follow_panel(values).mode_dword,2)

    def test_earlier_entry_and_disabled_gate_skip_later_observations(self):
        self.assertFalse(self.leader(FollowObservation()).complete)
        p=self.leader(FollowObservation(entry_reached=True),FollowConfiguration(0,1,'Alice'))
        self.assertTrue(p.complete);self.assertEqual(p.status,'disabled');self.assertIsNone(p.movement)

    def test_leader_signed_party_count_and_word_id_zero_extension(self):
        for count in (0,0xffffffff,0x80000000):
            p=self.leader(ready(party_count_dword=count,pointer_dword=None))
            self.assertTrue(p.complete);self.assertEqual(p.status,'no_positive_party_count')
        p=self.leader();self.assertIn(('00464a10',65535),p.steps)
        self.assertEqual(p.movement,(0x41200000,0x41a00000))

    def test_unsigned_nonzero_lookup_pointer_and_wrapped_coordinates(self):
        p=self.leader(ready(pointer_dword=0xfffffff0))
        self.assertTrue(p.complete);self.assertIn(('0045ddb8',0),p.steps);self.assertIn(('0045ddb8',0x10),p.steps)
        p=self.leader(ready(pointer_dword=0));self.assertEqual(p.status,'entity_not_found')

    def test_distance_strict_greater_mask_skips_equal_less_and_unordered(self):
        for status in (0x100,0x4000,0x4500,0x400):
            p=self.leader(ready(distance_status_word=status));self.assertEqual(p.status,'distance_gate_skipped');self.assertIsNone(p.movement)
        p=self.leader(ready(distance_status_word=0x200));self.assertEqual(p.status,'movement_span_returned')
        self.assertEqual(DISTANCE_THRESHOLD_BITS,0x40a00000)

    def test_manual_requires_fresh_second_mode_and_skips_other_modes(self):
        self.assertFalse(self.manual(ready(second_mode_dword=None)).complete)
        p=self.manual(ready(second_mode_dword=1));self.assertEqual(p.status,'other_mode')
        self.assertEqual(p.equality_plans,())

    def test_manual_cached_id_avoids_name_lookup_and_adds_four_y_observation(self):
        p=self.manual(ready(name_id_dword=None))
        self.assertTrue(p.complete);self.assertIn(('00464a10',7),p.steps)
        self.assertFalse(any(s[0]=='004656cc' for s in p.steps))
        self.assertEqual(p.movement,(0x41200000,0x41c00000))
        self.assertIn(('manual_y_add_observed',0x41a00000,0x40800000,0x41c00000),p.steps)

    def test_name_change_clears_cache_before_fresh_lookup_and_preserves_prefix(self):
        o=ready(previous_equal=equality('Alice','Bob'),helper_returns={**ready().helper_returns,'name_lookup':False})
        p=self.manual(o,FollowState(1,'Bob',7))
        self.assertFalse(p.complete);self.assertEqual(p.state,FollowState(1,'Alice',0))
        p=self.manual(replace(o,helper_returns=ready().helper_returns),FollowState(1,'Bob',7))
        self.assertTrue(p.complete);self.assertEqual(p.state.cached_id_dword,99)

    def test_zero_name_id_does_not_lookup_entity_and_zero_entity_clears_cache(self):
        p=self.manual(ready(name_id_dword=0),FollowState(1,'Alice',0))
        self.assertEqual(p.status,'name_not_found');self.assertFalse(any(s[0]=='00464a10' for s in p.steps))
        p=self.manual(ready(pointer_dword=0));self.assertEqual(p.state.cached_id_dword,0)

    def test_initialization_requires_post_name_and_retains_flag_on_later_gap(self):
        p=self.manual(ready(initialized_previous_name=None),FollowState())
        self.assertFalse(p.complete);self.assertEqual(p.state.initialized_byte,0)
        p=self.manual(ready(empty_equal=None),FollowState())
        self.assertFalse(p.complete);self.assertEqual(p.state.initialized_byte,1);self.assertEqual(p.state.previous_name,'')

    def test_empty_compare_cleanup_precedes_empty_early_exit(self):
        c=FollowConfiguration(1,2,'')
        o=ready(empty_equal=equality('',''),previous_equal=None)
        p=plan_follow_tail(c,FollowState(1,'Bob',7),o)
        self.assertEqual(p.status,'empty_name');self.assertEqual(p.state.cached_id_dword,7)
        p=plan_follow_tail(c,FollowState(1,'Bob',7),replace(o,helper_returns={}))
        self.assertFalse(p.complete);self.assertIn('empty_temporary_cleanup',p.missing)

    def test_helper_gaps_and_missing_float_operands_never_invent_movement(self):
        for key in ('party_count','entity_lookup','coord_x','coord_y','distance'):
            p=self.leader(ready(helper_returns={**ready().helper_returns,key:False}))
            self.assertFalse(p.complete);self.assertIsNone(p.movement)
        p=self.manual(ready(manual_y_after_add_bits=None));self.assertFalse(p.complete);self.assertIsNone(p.movement)
        p=self.leader(ready(helper_returns={**ready().helper_returns,'movement':False}))
        self.assertFalse(p.complete);self.assertIsNotNone(p.movement);self.assertFalse(p.native_execution_verified)

    def test_comparison_identity_unknown_results_and_input_types(self):
        with self.assertRaises(ValueError):self.manual(ready(empty_equal=equality('Bob','')))
        p=self.manual(ready(empty_equal=Eq(helper_returned=True)))
        self.assertFalse(p.complete);self.assertIn('zero flag',p.missing)
        for args in ({'leader_id_word':65536},{'distance_status_word':True},{'helper_returns':{'x':1}}):
            with self.assertRaises(ValueError):FollowObservation(**args)
        with self.assertRaises(ValueError):compile_follow_panel({})

if __name__=='__main__':unittest.main()
