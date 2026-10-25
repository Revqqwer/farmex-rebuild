import unittest
from rogue_attack import RogueDecision,SPECIAL_ROWS
from rogue_special_execution import *

def decision(skill=0x276,alt=False):
    row=next(r for r in SPECIAL_ROWS if r.skill_number==skill)
    return RogueDecision('selected_requires_helpers',row,lock_interval_ms=(2100 if skill!=0x290 else 1800) if alt else (1600 if skill!=0x290 else 1300))

def observations(alt=False,**kw):
    v={'normal.caller_20_dword':0,'normal.helper_20_byte':0,'normal.context_553e80':100,
        'preparation.3c_dword':0,'preparation.target_462630':0,'preparation.lookup_464a10':0,'preparation.context_553e80':200,
        'alternate.target_562040':55,'alternate.prefix_46256c':102,'alternate.lookup_464990':123,
        'alternate.context_5540a0':400,'alternate.return_553ee4':1,
        'normal.target_pointer_56203c':500,'clock.lock':1000,'clock.after_send':1100}
    v.update(kw);return SpecialObservation(alt,v)

class SpecialTests(unittest.TestCase):
    def test_normal_all_four_lock_and_future_timer(self):
        for skill,offset in ((0x262,0x54),(0x276,0x60),(0x28a,0x6c),(0x290,None)):
            with self.subTest(skill=skill):
                p=plan_rogue_special_execution(decision(skill),observations())
                self.assertEqual(p.status,'local_return_one');self.assertEqual(p.source_return,1)
                duration=1300 if skill==0x290 else 1600
                expected=(('00561f80',duration),('00561f84',1000),('00561f7e',1))
                if offset is not None:expected+=(('object:+%x'%offset,1100+duration),)
                self.assertEqual(p.local_writes,expected)
    def test_normal_preparation_full_trace_order(self):
        o=observations(**{'normal.caller_20_dword':256,'normal.helper_20_byte':1,'preparation.3c_dword':1,'preparation.target_462630':0,'preparation.lookup_464a10':900})
        p=plan_rogue_special_execution(decision(),o)
        helpers=[x[0] for x in p.trace]
        self.assertEqual(helpers,['0045dc44:caller_root_plus_554020','00464714','0045dbdc:helper_root_plus_554020','00465f30','indirect:00553f50','00462630:initial','0045dc44:root_plus_55403c','00462630:repeat','00465ef8','00464a10','indirect:00553ef0','004dfd7c'])
        self.assertIn(('00465ef8',(0,0)),p.trace)
        self.assertIn(('indirect:00553ef0',(200,0,900)),p.trace)
    def test_byte_gate_independent_of_caller_dword(self):
        p=plan_rogue_special_execution(decision(),observations(**{'normal.caller_20_dword':256,'normal.helper_20_byte':0}))
        self.assertIn('00464714',[x[0] for x in p.trace]);self.assertNotIn('00465f30',[x[0] for x in p.trace])
    def test_preparation_lookup_zero_skips_indirect(self):
        p=plan_rogue_special_execution(decision(),observations(**{'preparation.3c_dword':1,'preparation.target_462630':55,'preparation.lookup_464a10':0,'preparation.context_553e80':None}))
        self.assertEqual(p.status,'local_return_one');self.assertNotIn('indirect:00553ef0',[x[0] for x in p.trace])
    def test_alternate_zero_result_never_locks(self):
        p=plan_rogue_special_execution(decision(alt=True),observations(True,**{'alternate.return_553ee4':0,'clock.lock':None}))
        self.assertEqual(p.status,'local_return_zero');self.assertEqual(p.local_writes,());self.assertEqual(p.source_return,0)
    def test_alternate_all_skills_no_row_timer_write(self):
        for skill in (0x262,0x276,0x28a,0x290):
            with self.subTest(skill=skill):
                p=plan_rogue_special_execution(decision(skill,True),observations(True))
                self.assertEqual(p.status,'local_return_one');self.assertEqual(len(p.local_writes),3)
                self.assertEqual(p.local_writes[0],('00561f80',1800 if skill==0x290 else 2100))
                self.assertNotIn('004dfd7c',[x[0] for x in p.trace])
                self.assertIn(('00464990',(102000+skill,123)),p.trace)
    def test_alternate_return_unknown_preserves_prior_call(self):
        p=plan_rogue_special_execution(decision(alt=True),observations(True,**{'alternate.return_553ee4':None}))
        self.assertEqual(p.status,'needs_observation');self.assertEqual(p.local_writes,());self.assertEqual(p.trace[-1][0],'indirect:00553ee4')
    def test_preparation_unknown_no_later_send(self):
        p=plan_rogue_special_execution(decision(),observations(**{'preparation.3c_dword':None}))
        self.assertEqual(p.status,'needs_observation');self.assertNotIn('004dfd7c',[x[0] for x in p.trace])
    def test_unknown_clock_preserves_source_duration_write(self):
        p=plan_rogue_special_execution(decision(),observations(**{'clock.lock':None}))
        self.assertEqual(p.status,'needs_observation');self.assertEqual(p.local_writes,(('00561f80',1600),))
    def test_unknown_after_send_preserves_source_lock(self):
        p=plan_rogue_special_execution(decision(),observations(**{'clock.after_send':None}))
        self.assertEqual(p.status,'needs_observation');self.assertEqual(len(p.local_writes),3);self.assertEqual(p.trace[-1][0],'004dfd7c')
    def test_wrap_future_timestamp(self):
        p=plan_rogue_special_execution(decision(),observations(**{'clock.after_send':0xffffff00}))
        self.assertEqual(p.local_writes[-1],('object:+60',1344))
    def test_rawprefix_arithmetic_wrap(self):
        p=plan_rogue_special_execution(decision(alt=True),observations(True,**{'alternate.prefix_46256c':0xffffffff}))
        self.assertIn(('00464990',((0xffffffff*1000+0x276)&0xffffffff,123)),p.trace)
    def test_invalid_observation_and_mode(self):
        with self.assertRaises(ValueError):observations(**{'clock.lock':True})
        with self.assertRaises(ValueError):plan_rogue_special_execution(decision(),observations(True))
        with self.assertRaises(ValueError):plan_rogue_special_execution(decision(),observations(**{'normal.caller_20_dword':1,'normal.helper_20_byte':256}))
    def test_not_selected(self):
        self.assertEqual(plan_rogue_special_execution(RogueDecision('locked'),observations()).status,'not_selected')

if __name__=='__main__':unittest.main()
