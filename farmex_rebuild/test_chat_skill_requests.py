import unittest
from dataclasses import replace
from chat_skill_requests import (SPECS,ROOTS,ChatSkillSetting as S,ChatSkillConfiguration as C,
    ChatSkillObservation as O,ChatSkillFrame,compile_chat_skills,plan_chat_skill_requests)
from chat_party_invite import ChatPartyMessage
from name_codec import WindowsNameCodec

MSG=ChatPartyMessage(2,0xffff1234,b'Alice',b'go')
def config(enabled=None):
    enabled={s[0] for s in SPECS} if enabled is None else set(enabled)
    return C(tuple(S(s[0],int(s[0] in enabled),b'go') for s in SPECS))
def sample(family='Mage',**values):
    v=dict(channel_first=2,channel_second=3,channel_for_pm_alarm=3,pm_alarm_flag=0,
           runtime_ready_byte=1,pending_byte=0,mage_probe_eax=int(family=='Mage'),
           rogue_probe_eax=int(family=='Rogue'),priest_probe_eax=int(family=='Priest'),priest_buff_gate_eax=2)
    v.update(values)
    r={k:True for k in ('pm_alarm_span','mage_probe_span','rogue_probe_span','priest_probe_span','priest_buff_gate')}
    r.update({'compare:'+s[0]:True for s in SPECS})
    return O(v,r)

class ChatSkillRequestTests(unittest.TestCase):
    def test_all_nine_request_kinds_and_full_sender_dword(self):
        for spec in SPECS:
            key,family,*_=spec;p=plan_chat_skill_requests(config((key,)),MSG,sample(family))
            self.assertTrue(p.complete,key);self.assertEqual(p.queued_request.key,key)
            self.assertEqual(p.queued_request.kind,spec[-1]);self.assertEqual(p.queued_request.sender_dword,0xffff1234)
            self.assertEqual(p.queued_request.context_stores,((0x180,1,1),(0x184,4,spec[-1]),(0x188,4,0xffff1234)))
            self.assertFalse(p.queued_request.skill_execution_verified)

    def test_family_probe_order_and_low_al_not_config_selected_job(self):
        p=plan_chat_skill_requests(config(),MSG,sample('Priest',mage_probe_eax=0x101,rogue_probe_eax=1))
        self.assertEqual(p.queued_request.key,'mage_tp')
        self.assertFalse(any(s==('normal_return','rogue_probe_span') for s in p.steps))
        p=plan_chat_skill_requests(config(),MSG,sample('Rogue',mage_probe_eax=0x100))
        self.assertEqual(p.queued_request.key,'rogue_sw')

    def test_disabled_mage_branch_does_not_fall_through_to_other_family(self):
        p=plan_chat_skill_requests(config(('rogue_sw',)),MSG,sample('Mage',rogue_probe_eax=1))
        self.assertTrue(p.complete);self.assertIsNone(p.queued_request)
        self.assertFalse(any(s[0]=='own_exact_compare' for s in p.steps))

    def test_first_matching_rogue_and_priest_wins(self):
        self.assertEqual(plan_chat_skill_requests(config(),MSG,sample('Rogue')).queued_request.key,'rogue_sw')
        self.assertEqual(plan_chat_skill_requests(config(),MSG,sample('Priest')).queued_request.key,'priest_buff')
        self.assertEqual(plan_chat_skill_requests(config(('priest_cure','priest_disease')),MSG,sample('Priest')).queued_request.key,'priest_cure')

    def test_priest_buff_signed_threshold_and_fallback(self):
        for raw,key in ((0,'priest_ac'),(1,'priest_ac'),(2,'priest_buff'),(0x7fffffff,'priest_buff'),(0xffffffff,'priest_ac'),(0x80000000,'priest_ac')):
            p=plan_chat_skill_requests(config(),MSG,sample('Priest',priest_buff_gate_eax=raw))
            self.assertTrue(p.complete);self.assertEqual(p.queued_request.key,key)
        p=plan_chat_skill_requests(config(('priest_ac',)),MSG,replace(sample('Priest'),values={k:v for k,v in sample('Priest').values.items() if k!='priest_buff_gate_eax'}))
        self.assertEqual(p.queued_request.key,'priest_ac')

    def test_disabled_keyword_is_not_compared_and_matching_is_case_sensitive(self):
        o=sample('Rogue');r=dict(o.normal_returns);del r['compare:rogue_sw']
        p=plan_chat_skill_requests(config(('rogue_wolf',)),MSG,O(o.values,r));self.assertEqual(p.queued_request.key,'rogue_wolf')
        p=plan_chat_skill_requests(config(),replace(MSG,message=b'GO'),sample('Rogue'))
        self.assertTrue(p.complete);self.assertIsNone(p.queued_request)

    def test_pm_alarm_precedes_runtime_and_pending_gates(self):
        o=sample(channel_for_pm_alarm=2,pm_alarm_flag=1,runtime_ready_byte=0)
        p=plan_chat_skill_requests(config(),MSG,replace(o,normal_returns={}))
        self.assertEqual(p.missing,'pm_alarm_span normal return')
        p=plan_chat_skill_requests(config(),MSG,o);self.assertEqual(p.status,'runtime_gate_closed')
        self.assertIsNone(p.queued_request)

    def test_pending_request_is_not_overwritten(self):
        p=plan_chat_skill_requests(config(),MSG,sample(pending_byte=255))
        self.assertTrue(p.complete);self.assertEqual(p.status,'pending_request_preserved');self.assertIsNone(p.queued_request)

    def test_channel_reads_are_fresh_and_non_pm_party_exits_to_notice_span(self):
        o=sample(channel_first=1,channel_second=3,channel_for_pm_alarm=3)
        self.assertIsNotNone(plan_chat_skill_requests(config(),MSG,o).queued_request)
        p=plan_chat_skill_requests(config(),MSG,sample(channel_first=1,channel_second=7))
        self.assertEqual(p.status,'outside_pm_party_span');self.assertEqual(p.next_address,'00457014')
        v=dict(sample().values);del v['channel_second']
        self.assertTrue(plan_chat_skill_requests(config(),MSG,O(v,sample().normal_returns)).complete)

    def test_every_reached_normal_and_value_gap_blocks(self):
        o=sample('Priest',channel_for_pm_alarm=2,pm_alarm_flag=1);p=plan_chat_skill_requests(config(),MSG,o)
        for step in p.steps:
            kind,label=step[:2]
            if kind=='source_value':
                v=dict(o.values);del v[label];self.assertFalse(plan_chat_skill_requests(config(),MSG,O(v,o.normal_returns)).complete,label)
            elif kind=='normal_return':
                r=dict(o.normal_returns);r[label]=False;self.assertFalse(plan_chat_skill_requests(config(),MSG,O(o.values,r)).complete,label)

    def test_frame_keeps_prior_family_probes_and_does_not_repeat_request(self):
        c=config(('priest_cure',));f=ChatSkillFrame(c,MSG);o=sample('Priest')
        p=f.advance(replace(o,normal_returns={**o.normal_returns,'compare:priest_cure':False}))
        self.assertFalse(p.complete)
        p=f.advance(O(normal_returns={'compare:priest_cure':True}))
        self.assertTrue(p.complete);self.assertEqual(p.queued_request.key,'priest_cure')
        self.assertIs(f.advance(O()),p)

    def test_real_panel_compiler_codepage_and_crossed_priest_text_fields(self):
        values={}
        for key,family,check,text,*_ in SPECS:
            values[ROOTS[family]+check]=True;values[ROOTS[family]+text]='şifa\0suffix'
        c=compile_chat_skills(values,WindowsNameCodec(1254))
        self.assertTrue(all(s.command==b'\xfeifa' for s in c.settings))
        ac=next(s for s in SPECS if s[0]=='priest_ac');und=next(s for s in SPECS if s[0]=='priest_und')
        self.assertEqual((ac[7],und[7]),(0x1124,0x111c))
        with self.assertRaises(ValueError):compile_chat_skills(values,None)

if __name__=='__main__':unittest.main()
