import unittest
from dataclasses import replace
from motion_genie_helpers import (GuardedReadReceipt as R,MotionGenieObservation as O,
    MotionGenieFrame,plan_movement_helper,plan_genie_helper)
from chat_commands import (SPECS,CommandSetting,ChatCommandsConfiguration as C,
    ChatCommandsObservation as CO,ChatCommandsFrame,plan_chat_commands)
from chat_party_invite import ChatPartyMessage

# All addresses and outcomes below are synthetic fixtures, not live observations.
def motion(state=2,root=0x1000):
    return O(((0x553e7c,0x2000),(0x554014,0x10),(0x554018,0x14),
              (0x55401c,0x18),(0x554020,0x20),(0x553e80,0x3000),(0x553f50,0x9000)),
             (R(0x2000,4,root,True),R((root+0x20)&0xffffffff,1,state,True)),
             ((0x3000,0x4000),),
             dict(write_moving=True,write_x=True,write_y=True,indirect_target=True))

def genie():
    return O(((0x553e80,0x2000),(0x554178,0x10),(0x55417c,0x14),
              (0x554180,0x18),(0x553e80,0x3000),(0x554178,0x20),(0x554200,0x30)),
             (R(0x2000,4,0x4000,True),R(0x4010,4,0x5000,True),
              R(0x5014,4,0xaaaa,True),R(0x5018,4,0xbbbb,True)),
             ((0x3000,0x6000),(0x6020,0x7000),(0x7000,0x8000),(0x8030,0x9000)),
             {'indirect_target':True})

def config(key):
    return C(tuple(CommandSetting(s[0],int(s[0]==key),b'go' if s[0]==key else b'other') for s in SPECS))

def command_obs(key,child,**fields):
    return CO({**{'compare:'+s[0]:True for s in SPECS},'action:'+key:True,
               'genie_start_state':True,'genie_remaining':True,'genie_stop_state':True},
              action_executions={key:child},**fields)

class MotionGenieTests(unittest.TestCase):
    def test_motion_exact_bit_copies_and_state_two_skips_indirect(self):
        p=plan_movement_helper(0xdeadbeef,0x7fc00001,motion(0xffff0002))
        self.assertTrue(p.complete);self.assertEqual(p.push_order,(0x7fc00001,0xdeadbeef))
        self.assertEqual([(w.address,w.width,w.value) for w in p.writes],
                         [(0x1010,1,1),(0x1014,4,0xdeadbeef),(0x1018,4,0x7fc00001)])
        self.assertTrue(all(w.normal_return_observed for w in p.writes));self.assertIsNone(p.call)
        self.assertFalse(p.native_execution_verified);self.assertFalse(p.protection_side_effects_emulated)

    def test_motion_every_other_low_byte_calls_with_fresh_root(self):
        for state in (0,1,3,255,0x102):
            p=plan_movement_helper(11,22,motion(state))
            self.assertTrue(p.complete)
            if state&255==2:self.assertIsNone(p.call)
            else:
                self.assertEqual((p.call.target,p.call.ecx,p.call.push_order),(0x9000,0x4000,(1,1)))
                self.assertFalse(p.call.abi_verified)

    def test_motion_write_order_and_separate_normal_receipts(self):
        o=motion(0)
        for label,n in (('write_moving',1),('write_x',2),('write_y',3)):
            p=plan_movement_helper(11,22,replace(o,normal_returns={**o.normal_returns,label:False}))
            self.assertFalse(p.complete);self.assertEqual(p.missing,label+' normal return')
            self.assertEqual(len(p.writes),n);self.assertFalse(p.writes[-1].normal_return_observed)
        p=plan_movement_helper(11,22,replace(o,normal_returns={**o.normal_returns,'indirect_target':False}))
        self.assertFalse(p.complete);self.assertEqual(p.call.ecx,0x4000)

    def test_failed_or_null_guarded_root_is_not_safe_no_op(self):
        o=motion(root=0);p=plan_movement_helper(11,22,replace(o,normal_returns={}))
        self.assertFalse(p.complete);self.assertEqual(p.writes[0].address,0x10)
        self.assertEqual(p.missing,'write_moving normal return')
        with self.assertRaises(ValueError):R(0,4,1,True)

    def test_motion_dword_addition_wraps(self):
        p=plan_movement_helper(1,2,motion(root=0xfffffff8))
        self.assertTrue(p.complete);self.assertEqual([w.address for w in p.writes],[8,12,16])

    def test_genie_low_byte_choice_and_fresh_direct_call_chain(self):
        for flag,selected in ((0,0xbbbb),(0x100,0xbbbb),(1,0xaaaa),(255,0xaaaa),(0x101,0xaaaa)):
            p=plan_genie_helper(flag,genie());self.assertTrue(p.complete)
            self.assertEqual((p.call.ecx,p.call.target,p.call.push_order),(0x7000,0x9000,(1,selected)))
            self.assertEqual(len([s for s in p.steps if s[0]=='guarded']),4)
            self.assertEqual(len([s for s in p.steps if s[0]=='direct']),4)
            self.assertEqual(p.writes,())

    def test_genie_reads_unselected_option_before_branch(self):
        for flag in (0,1):
            o=genie();p=plan_genie_helper(flag,replace(o,guarded_reads=o.guarded_reads[:3]))
            self.assertFalse(p.complete);self.assertEqual(p.request.address,0x5018)
            self.assertIsNone(p.call)

    def test_every_ordered_observation_gap(self):
        for planner,o in ((lambda v:plan_movement_helper(11,22,v),motion(0)),(lambda v:plan_genie_helper(1,v),genie())):
            for name in ('global_samples','guarded_reads','direct_samples'):
                for count in range(len(getattr(o,name))):
                    p=planner(replace(o,**{name:getattr(o,name)[:count]}))
                    self.assertFalse(p.complete,(name,count))
            for count in range(len(o.guarded_reads)):
                rows=list(o.guarded_reads);rows[count]=replace(rows[count],normal_returned=False)
                self.assertFalse(planner(replace(o,guarded_reads=tuple(rows))).complete)

    def test_order_and_width_mismatches_rejected_only_when_reached(self):
        o=genie();rows=list(o.guarded_reads);rows[2]=replace(rows[2],width=1)
        with self.assertRaises(ValueError):plan_genie_helper(1,replace(o,guarded_reads=tuple(rows)))
        rows=list(o.direct_samples);rows[0]=(0x2000,0x6000)
        with self.assertRaises(ValueError):plan_genie_helper(1,replace(o,direct_samples=tuple(rows)))
        o=motion();rows=list(o.direct_samples);rows[0]=(0,123)
        self.assertTrue(plan_movement_helper(1,2,replace(o,direct_samples=tuple(rows))).complete)

    def test_genie_frame_preserves_both_option_reads_across_call_gap(self):
        o=genie();f=MotionGenieFrame('00466cc4',(1,))
        p=f.advance(replace(o,direct_samples=(),normal_returns={}))
        self.assertFalse(p.complete);self.assertEqual(p.request.address,0x3000)
        altered=replace(o,global_samples=((0x553e80,0xdead),)+o.global_samples[1:],
                        guarded_reads=(R(0xdead,4,0xbad,True),)+o.guarded_reads[1:])
        p=f.advance(altered);self.assertTrue(p.complete);self.assertEqual(p.call.push_order,(1,0xaaaa))
        self.assertIs(f.advance(O()),p)

    def test_motion_frame_preserves_completed_write_prefix(self):
        o=motion(0);f=MotionGenieFrame('004646b4',(22,11))
        p=f.advance(replace(o,normal_returns={'write_moving':True}))
        self.assertEqual(p.missing,'write_x normal return')
        self.assertTrue(p.writes[0].normal_return_observed)
        p=f.advance(replace(o,normal_returns={'write_x':True,'write_y':True,'indirect_target':True}))
        self.assertTrue(p.complete);self.assertEqual(p.writes[0].address,0x1010)

    def test_chat_binding_checks_exact_motion_arguments_and_resumes(self):
        msg=ChatPartyMessage(1,7,b'Alice',b'go');key='return_center'
        fields=dict(center_y_dword=22,center_y_f32_bits=22,center_x_dword=11,center_x_f32_bits=11)
        child=plan_movement_helper(11,22,O());o=command_obs(key,child,**fields)
        p=plan_chat_commands(config(key),msg,o);self.assertFalse(p.complete)
        self.assertIn('bound action:return_center',p.missing)
        f=ChatCommandsFrame(config(key),msg);self.assertFalse(f.advance(o).complete)
        done=plan_movement_helper(11,22,motion())
        p=f.advance(CO({'action:'+key:True,**{'compare:'+s[0]:True for s in SPECS}},action_executions={key:done}))
        self.assertTrue(p.complete);self.assertIs(p.actions[0].helper_execution,done)
        with self.assertRaises(ValueError):
            plan_chat_commands(config(key),msg,command_obs(key,plan_movement_helper(22,11,motion()),**fields))

    def test_chat_genie_binding_cannot_bypass_gap_or_upper_return(self):
        msg=ChatPartyMessage(1,7,b'Alice',b'go');key='genie_start'
        fields=dict(genie_blocked_byte=0,genie_start_state_eax=0,genie_remaining_eax=1)
        p=plan_chat_commands(config(key),msg,command_obs(key,plan_genie_helper(1,O()),**fields))
        self.assertFalse(p.complete);self.assertIn('bound action:genie_start',p.missing)
        done=plan_genie_helper(1,genie());o=command_obs(key,done,**fields)
        p=plan_chat_commands(config(key),msg,replace(o,helper_returns={**o.helper_returns,'action:'+key:False}))
        self.assertFalse(p.complete);self.assertEqual(p.missing,'action:genie_start normal return')
        self.assertTrue(plan_chat_commands(config(key),msg,o).complete)
        with self.assertRaises(ValueError):
            plan_chat_commands(config(key),msg,command_obs(key,plan_genie_helper(0x101,genie()),**fields))

if __name__=='__main__':unittest.main()
