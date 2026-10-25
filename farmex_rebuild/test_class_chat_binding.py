import unittest
from dataclasses import replace
from job_dispatcher import JobSnapshot,JobState,HelperReply as H,dispatch_job
from alternate_dispatcher import AlternateSnapshot,dispatch_alternate
from class_family import FamilySelection,LEGAL_HEADS,dispatch_class_family
from chat_skill_consumers import ChatConsumerObservation as O,plan_chat_consumer
from test_chat_skill_consumers import sample as mr_sample
from test_priest_chat_consumer import sample as priest_sample

HELPERS={'mage':'004994bc','rogue':'004da568','priest':'004cee18'}
def consumer(job,complete=True,context=0x5000):
    o=priest_sample() if job=='priest' else mr_sample()
    return plan_chat_consumer(job.title(),context,o if complete else O())
def snapshot(job,legal=False,context=0x5000):
    cls=AlternateSnapshot if legal else JobSnapshot
    values=dict(locked_561f7e=False,raw_byte_55402c=0,raw_float_554030=0,
                rogue_flag_0=False,attack_enabled_561f6c=True,guard_fe384=False,guard_46fe90=False,
                target_id_562040=0,class_context_dword=context)
    if legal:values['actor_state_554034']=0
    return cls(1000,**values)
def replies(job,child,legal=False,normal=True,post_lock=None,raw=None):
    if job=='mage':d={a:H(False,False) for a in ('00499b88','00499620')}
    elif job=='rogue':d={'004da2d4':H(False,False)}
    else:d={a:H(False,False) for a in ('004cf8b8','004d0c18','004cfc74','004d0eb0')}
    d[HELPERS[job]]=H(raw,post_lock,child,normal)
    return d
def run(job,legal,child,**kwargs):
    rs=replies(job,child,legal,**kwargs)
    return dispatch_alternate(job,snapshot(job,True),replies=rs) if legal else dispatch_job(job,snapshot(job),replies=rs)

class ClassChatBindingTests(unittest.TestCase):
    def test_mage_both_heads_consume_low_al_and_set650_interval(self):
        for legal in (False,True):
            c=consumer('mage');p=run('mage',legal,c)
            self.assertEqual(p.status,'complete');self.assertIs(p.chat_consumers[0][1],c)
            self.assertEqual(p.calls[-1],HELPERS['mage'])
            self.assertEqual(p.state.interval_ms if legal else p.state.mage_interval_ms,650)

    def test_legal_priest_and_rogue_use_boolean_result(self):
        for job,interval in (('priest',650),('rogue',500)):
            c=consumer(job);p=run(job,True,c)
            self.assertEqual(p.status,'complete');self.assertEqual(p.reason,'support_consumed')
            self.assertEqual(p.state.interval_ms,interval);self.assertIs(p.chat_consumers[0][1],c)

    def test_normal_priest_ignores_low_al_and_calls_next_helper(self):
        p=run('priest',False,consumer('priest'),raw=False,post_lock=True)
        self.assertEqual(p.status,'complete');self.assertEqual(p.reason,'target_or_route_gate')
        self.assertEqual(p.calls[p.calls.index(HELPERS['priest'])+1],'004d0eb0')

    def test_normal_rogue_uses_fresh_post_lock_not_boolean(self):
        p=run('rogue',False,consumer('rogue'),raw=False,post_lock=True)
        self.assertEqual(p.status,'complete');self.assertEqual(p.reason,'locked_after_004da568')
        p=run('rogue',False,consumer('rogue'))
        self.assertEqual(p.status,'needs_observation');self.assertEqual(p.reason,'DAT_00561f7e')

    def test_incomplete_child_cannot_be_bypassed_by_raw_positive_reply(self):
        for job in HELPERS:
            for legal in (False,True):
                c=consumer(job,False);p=run(job,legal,c,raw=True,post_lock=True)
                self.assertEqual(p.status,'needs_observation');self.assertTrue(p.reason.startswith('bound chat consumer:'))
                self.assertEqual(p.calls[-1],HELPERS[job]);self.assertIs(p.chat_consumers[0][1],c)

    def test_separate_source_helper_normal_return_required(self):
        for job in HELPERS:
            for legal in (False,True):
                p=run(job,legal,consumer(job),normal=False,raw=True)
                self.assertEqual(p.status,'needs_observation');self.assertEqual(p.reason,'normal:'+HELPERS[job])

    def test_context_missing_is_gap_and_different_context_rejected(self):
        c=consumer('mage');rs=replies('mage',c)
        p=dispatch_job('mage',snapshot('mage',context=None),replies=rs)
        self.assertEqual(p.status,'needs_observation');self.assertIn('actor context',p.reason)
        for legal in (False,True):
            fn=dispatch_alternate if legal else dispatch_job
            with self.assertRaises(ValueError):fn('mage',snapshot('mage',legal,0x6000),replies=rs)

    def test_wrong_consumer_family_rejected_when_reached(self):
        rs=replies('mage',consumer('rogue'))
        with self.assertRaises(ValueError):dispatch_job('mage',snapshot('mage'),replies=rs)
        s=replace(snapshot('mage'),locked_561f7e=True)
        p=dispatch_job('mage',s,replies=rs);self.assertEqual(p.status,'complete');self.assertEqual(p.chat_consumers,())

    def test_conflicting_low_al_rejected_only_if_caller_uses_return(self):
        for job,legal in (('mage',False),('mage',True),('rogue',True),('priest',True)):
            with self.assertRaises(ValueError):run(job,legal,consumer(job),raw=False)
        self.assertEqual(run('priest',False,consumer('priest'),raw=False).status,'complete')

    def test_legal_family_router_preserves_bound_child_result(self):
        c=consumer('mage');selection=FamilySelection('selected','legal',LEGAL_HEADS['mage'],'fixture')
        p=dispatch_class_family('mage',selection,snapshot('mage',True),replies=replies('mage',c,True))
        self.assertIs(p.chat_consumers[0][1],c)

    def test_legacy_unbound_helper_reply_remains_available(self):
        rs=replies('mage',None,raw=True)
        p=dispatch_job('mage',snapshot('mage',context=None),replies=rs)
        self.assertEqual(p.status,'complete');self.assertEqual(p.chat_consumers,())

    def test_actor_context_and_normal_receipt_types_not_coerced(self):
        with self.assertRaises(ValueError):replace(snapshot('mage'),class_context_dword=True)
        with self.assertRaises(ValueError):H(chat_consumer=consumer('mage'),normal_returned=1)

if __name__=='__main__':unittest.main()
