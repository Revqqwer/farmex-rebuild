import unittest
import copy
import json
from pathlib import Path
from dataclasses import replace
from priest_support import (PriestSupportSnapshot, PriestPartyRaw, automatic_skill,
    selected_skill_available, self_cure_disease, buff_ac, queued_support, support_skills)


def snapshot(**changes):
    checks={k:True for k in ('00464444','004643f8','004642d0','00464364','00463924:master:8e','00463924:master:8d')}
    for group,count in (('master',2),('resistance',4),('heal',9)):
        checks.update({'00464268:%s:%d'%(group,i):False for i in range(count)})
    checks.update({'00464490:'+kind:False for kind in ('self_disease','self_cure','master:8e','master:8d','resistance:8f','resistance:90','resistance:91','heal:b4')})
    base=dict(now_ms=700000,flags={i:False for i in range(0x130)},
        parameters={0xec:0x25e,0xf4:0x25b,0xfc:0x25e,0x104:0x25b},
        stats={k:100 for k in ('00462ddc','00462e08','00462e34','00462670')},
        timers={key:0 for key in ('0056fb60','0056fb5c','0056fb54','0056fb58','+94','+98','+a8','+9c','+a0','+a4','+bc','+b8')},
        checks=checks,locked=False,attack_enabled=True,alternate=False,self_id=1,
        raw_primary_pointer=0x10000000,party_count=0,party=(),queue_active=False)
    base['stats']['004611e0']=2000
    base.update(changes)
    return PriestSupportSnapshot(**base)


def enabled(*flags,**changes):
    s=snapshot(**changes)
    return replace(s,flags={k:k in flags for k in s.flags})


class PriestSupportTests(unittest.TestCase):
    def test_automatic_high_stat_no_mp_fallback(self):
        self.assertEqual(automatic_skill('buff',78,689),0)
        self.assertEqual(automatic_skill('buff',77,460),0x29e)

    def test_ac_auto1500_vs_selected150_source_difference(self):
        self.assertEqual(automatic_skill('ac',60,1499),0)
        self.assertEqual(automatic_skill('ac',60,1500),0x294)
        self.assertTrue(selected_skill_available(0x294,150))
        self.assertFalse(selected_skill_available(0x294,149))

    def test_selected_unknown_id_rejected(self):
        self.assertFalse(selected_skill_available(999,10000))

    def test_locked_short_circuits_unknown_config(self):
        for consumer in (self_cure_disease,buff_ac,support_skills):
            self.assertEqual(consumer(snapshot(locked=True,flags={})).status,'locked')

    def test_route_gates_distinct_flags(self):
        self.assertEqual(buff_ac(enabled(0x12e,attack_enabled=False)).status,'route_gate')
        self.assertEqual(support_skills(enabled(0x12f,attack_enabled=False)).status,'route_gate')
        self.assertEqual(self_cure_disease(enabled(0x12e,0x12f,attack_enabled=False)).status,'no_action')

    def test_disease_before_cure(self):
        self.assertEqual(self_cure_disease(enabled(0xfa,0xf9)).actions[0].skill_number,0x217)

    def test_disease_stat_and_2000ms_equality(self):
        s=enabled(0xfa,now_ms=2000)
        s.stats['00462ddc']=35
        self.assertEqual(self_cure_disease(s).status,'local_attempt')
        self.assertEqual(self_cure_disease(replace(s,now_ms=1999)).status,'no_action')
        s.stats['00462ddc']=34
        self.assertEqual(self_cure_disease(s).status,'no_action')

    def test_alternate_disease_zero_continues_cure(self):
        s=enabled(0xfa,0xf9,alternate=True)
        s.checks['004655e8:self_disease:1']=False
        s.checks['004655e8:self_cure:1']=True
        result=self_cure_disease(s)
        self.assertEqual([a.kind for a in result.actions],['self_disease','self_cure'])
        self.assertEqual(result.timer_updates,(('0056fb5c',s.now_ms),))
        self.assertEqual(result.local_lock_ms,2000)

    def test_unknown_disease_return_never_assumed(self):
        result=self_cure_disease(enabled(0xfa,alternate=True))
        self.assertEqual(result.status,'needs_observation')
        self.assertIn('004655e8',result.reason)

    def test_self_buff_before_self_ac_and_party(self):
        result=buff_ac(enabled(0xe8,0xf0,0xfb,party_count=None))
        self.assertEqual(result.actions[0].kind,'self_buff')
        self.assertEqual(result.timer_updates,(('0056fb54',700000),))

    def test_self_timer_exact3000_and_ready_gate(self):
        s=enabled(0xe8,now_ms=3000)
        self.assertEqual(buff_ac(s).status,'local_attempt')
        self.assertEqual(buff_ac(replace(s,now_ms=2999)).status,'no_action')
        s.checks['004642d0']=False
        self.assertEqual(buff_ac(s).status,'no_action')

    def test_party_buff2500_source_index_priority(self):
        a=PriestPartyRaw(3,100,50,1,0,0);b=PriestPartyRaw(2,100,50,1,0,0)
        result=buff_ac(enabled(0xfb,now_ms=2500,party_count=2,party=(a,b)))
        self.assertEqual(result.actions[0].target_argument,3)
        self.assertEqual(result.timer_updates,(('party:1:5696e4',2500),))

    def test_party_self_skipped(self):
        party=(PriestPartyRaw(1,100,50,1,0,0),PriestPartyRaw(2,100,50,1,0,0))
        self.assertEqual(buff_ac(enabled(0xfb,party_count=2,party=party)).actions[0].target_argument,2)

    def test_mirror_update_under3000_even_without_attempt(self):
        party=(PriestPartyRaw(2,0x10002,1,0,0,0),PriestPartyRaw(1,1,1,1,0,0))
        result=buff_ac(enabled(0xfb,now_ms=2999,party_count=2,party=party))
        self.assertEqual(result.mirror_updates,((1,2),))
        self.assertEqual(result.actions,())

    def test_party_ac_strict603000(self):
        party=(PriestPartyRaw(2,0,0,0,0,0),PriestPartyRaw(1,0,0,0,0,0))
        s=enabled(0x100,now_ms=603000,party_count=2,party=party)
        self.assertEqual(buff_ac(s).status,'no_action')
        self.assertEqual(buff_ac(replace(s,now_ms=603001)).actions[0].kind,'party_ac')

    def test_incomplete_party_needs_observation(self):
        self.assertEqual(buff_ac(enabled(0xfb,party_count=2,party=())).status,'needs_observation')

    def queued(self,mode,**changes):
        return snapshot(queue_active=True,queue_mode=mode,queue_target=2,
            queue_party_index=0,queue_party_index_after=0,party_count=2,target_exists=True,
            distance_truncated=28,**changes)

    def test_all_six_queue_modes_source_skill_arguments(self):
        for mode,skill in enumerate((0x25e,0x25b,0x28e,4,0x20d,0x217),1):
            result=queued_support(self.queued(mode))
            self.assertEqual(result.actions[0].skill_number,skill)
            self.assertTrue(result.queue_clear)

    def test_queue_target_optional_only_modes1_3(self):
        for mode in (1,3):
            self.assertEqual(queued_support(replace(self.queued(mode),target_exists=False)).status,'local_attempt')
        for mode in (2,4,5,6):
            self.assertEqual(queued_support(replace(self.queued(mode),target_exists=False)).status,'queue_cancel')

    def test_queue_distance28_vs29(self):
        self.assertEqual(queued_support(self.queued(2)).status,'local_attempt')
        self.assertEqual(queued_support(replace(self.queued(2),distance_truncated=29)).status,'queue_cancel')

    def test_queue_positive_selected_skill_no_mp_validation(self):
        s=self.queued(2);s.stats['004611e0']=0
        self.assertEqual(queued_support(s).actions[0].skill_number,0x25b)

    def test_queue_alt_zero_preserves_active_and_no_timer(self):
        s=self.queued(5,alternate=True);s.checks['004655e8:queued:5:2']=False
        result=queued_support(s)
        self.assertFalse(result.queue_clear);self.assertEqual(result.timer_updates,())
        self.assertEqual(result.status,'local_return_zero')

    def test_queue_alt_post_lookup_timer(self):
        s=self.queued(5,alternate=True);s.checks['004655e8:queued:5:2']=True
        result=queued_support(s)
        self.assertEqual(result.timer_updates,(('queue_party:0:56970c',700000),))

    def test_support_multiple_calls_and_final_heal(self):
        s=enabled(0x8e,0x8f,0xb3)
        result=support_skills(s)
        self.assertEqual([a.skill_number for a in result.actions],[20,0x211,0x23f])
        self.assertEqual(result.timer_updates[-1],('+bc',701500))

    def test_support_master_timer_failure_no_lower_fallback(self):
        s=enabled(0x8e,0x8d,now_ms=5499)
        self.assertEqual(support_skills(s).actions,())
        self.assertEqual(support_skills(replace(s,now_ms=5500)).actions[0].skill_number,20)

    def test_heal_top_timer_failure_no_lower_fallback(self):
        s=enabled(0xb4,0xb3,now_ms=119999)
        self.assertEqual(support_skills(s).actions,())
        self.assertEqual(support_skills(replace(s,now_ms=120000)).actions[0].skill_number,0x244)

    def test_244_shadowed_b8_write_not_invented(self):
        result=support_skills(enabled(0xb4))
        self.assertEqual(result.timer_updates,(('+bc',701500),))

    def test_future_dword_timer_wrap_preserved(self):
        s=enabled(0xb3,now_ms=1000);s.timers['+bc']=2500
        self.assertEqual(support_skills(s).status,'local_attempt')

    def test_basic4_goto_prevents_heal_override(self):
        result=support_skills(enabled(0x8c,0xb4))
        self.assertEqual(result.actions[0].skill_number,4)
        self.assertEqual(result.timer_updates,(('+a8',701500),))

    def test_effect_checks_shortcircuit_unknown_later(self):
        s=enabled(0xb3);s.checks['00464268:heal:0']=True
        s.checks.pop('00464268:heal:1')
        self.assertEqual(support_skills(s).status,'no_action')

    def test_alternate_support_does_not_require_source_timers(self):
        s=enabled(0xb3,timers={});s.checks['004655e8:support_heal:1']=True
        result=support_skills(s,alternate_consumer=True)
        self.assertEqual(result.status,'local_attempt');self.assertEqual(result.timer_updates,())
        self.assertEqual(result.local_lock_ms,2000)

    def test_unknown_eager_stat_is_not_fabricated(self):
        s=snapshot(stats={})
        self.assertEqual(support_skills(s).status,'needs_observation')

    def test_invalid_snapshot_types(self):
        with self.assertRaises(ValueError):snapshot(now_ms=-1)
        with self.assertRaises(ValueError):snapshot(locked=1)
        with self.assertRaises(ValueError):snapshot(timers={'+bc':-1})

    def test_actual_profile_compiler_to_self_buff(self):
        from profiles import Profiles
        from class_configuration import compile_priest, _MAP
        profiles=Profiles(json.loads((Path(__file__).parent/'ui_model.json').read_text(encoding='utf-8')))
        values=copy.deepcopy(profiles.defaults)
        path=next(p for p,o in _MAP['priest']['booleans'].items() if o==0xe8)
        values[path]=True
        combo=next(p for p,spec in _MAP['priest']['combos'].items() if spec['offset']==0xec)
        values[combo]=1
        config=compile_priest(values,profiles.list_defaults)
        result=buff_ac(snapshot(flags=config.flags,parameters=config.parameters))
        self.assertEqual(result.actions[0].kind,'self_buff')
        self.assertEqual(result.actions[0].skill_number,0x25e)


if __name__=='__main__':unittest.main()
