import unittest
from dataclasses import replace
from bot_switch import (BASE_RESETS,STOP_CONTEXT_RESETS,STOP_GLOBAL_RESETS,
    BotSwitchObservation as O,BotSwitchFrame,plan_bot_switch)
from chat_commands import (SPECS,CommandSetting,ChatCommandsConfiguration as C,
    ChatCommandsObservation as CO,ChatCommandsFrame,plan_chat_commands)
from chat_party_invite import ChatPartyMessage

CTX=0x561f34
LABELS=('switch_frame_setup','base_frame_setup','form_active','form_activate',
        'start_caption_span','start_notification_span','stop_caption_span','stop_notification_span',
        'activation_helper','use_current_xy','current_y','current_x','coordinate_helper',
        'current_coordinates_label_span','entered_y_text','entered_x_text','entered_coordinate_cleanup',
        'mode_two_start','mode_two_stop','stop_genie_state','stop_genie','stop_movement')
def fixture(mode=0,**values):
    v=dict(base_started_byte=0,form_active_eax=0,use_current_xy_eax=1,
           mode_for_zero=mode,mode_for_two=mode,mode_for_four=mode,mode_for_five=mode,
           current_y_eax=22,current_x_eax=11,entered_y_eax=0xffffffff,entered_x_eax=0xfffffffe,
           mode_two_start_eax=1,stop_mode_for_two=mode,stop_genie_state_eax=0)
    v.update(values);return O(v,{k:True for k in LABELS})
def writes(p,source=None):
    return [(s.address,s.width,s.value) for s in p.stores if source is None or s.source==source]
def called(p):return [s[1] for s in p.steps if s[0]=='opaque_call']
def config(key):return C(tuple(CommandSetting(s[0],int(s[0]==key),b'go' if s[0]==key else b'other') for s in SPECS))
def chat_obs(key,child):
    return CO({**{'compare:'+s[0]:True for s in SPECS},'action:'+key:True},action_executions={key:child})

class BotSwitchTests(unittest.TestCase):
    def test_base_reset_order_before_start_branch(self):
        o=fixture();p=plan_bot_switch(CTX,1,replace(o,values={}))
        self.assertFalse(p.complete);self.assertEqual(p.missing,'base_started_byte value')
        self.assertEqual(writes(p),[(CTX+x,w,v) for x,w,v in BASE_RESETS])

    def test_base_start_skips_ui_when_already_started(self):
        o=fixture(5,base_started_byte=255)
        p=plan_bot_switch(CTX,1,replace(o,normal_returns={'switch_frame_setup':True,'base_frame_setup':True,'activation_helper':True}))
        self.assertTrue(p.complete);self.assertEqual(called(p),[])
        self.assertEqual(writes(p)[-1],(CTX+0x38,1,1))

    def test_base_start_uses_low_al_and_writes_after_caption(self):
        o=fixture(5,form_active_eax=0x100)
        p=plan_bot_switch(CTX,1,o);self.assertTrue(p.complete)
        self.assertIn('form_vtable_94',called(p))
        p=plan_bot_switch(CTX,1,replace(o,normal_returns={**o.normal_returns,'start_caption_span':False}))
        self.assertFalse(p.complete);self.assertNotIn((CTX+0x2c,1,1),writes(p))
        p=plan_bot_switch(CTX,1,fixture(5,form_active_eax=0x101))
        self.assertNotIn('form_vtable_94',called(p))

    def test_mode_zero_current_coordinates_and_label_boundary(self):
        p=plan_bot_switch(CTX,1,fixture());self.assertTrue(p.complete)
        self.assertEqual(writes(p,'coordinate_helper_normal'),[(CTX+0xcc,4,11),(CTX+0xd0,4,22)])
        call=next(s for s in p.steps if s[:2]==('opaque_call','0040a2dc'))
        self.assertEqual(call[2],(22,11,CTX))
        o=fixture();p=plan_bot_switch(CTX,1,replace(o,normal_returns={**o.normal_returns,'current_coordinates_label_span':False}))
        self.assertFalse(p.complete);self.assertNotIn((CTX+0x38,1,1),writes(p))
        self.assertEqual(len(writes(p,'coordinate_helper_normal')),2)

    def test_mode_zero_entered_coordinates_preserve_raw_signed_bits(self):
        p=plan_bot_switch(CTX,1,fixture(use_current_xy_eax=0x100));self.assertTrue(p.complete)
        self.assertEqual(writes(p,'coordinate_helper_normal'),[(CTX+0xcc,4,0xfffffffe),(CTX+0xd0,4,0xffffffff)])
        self.assertNotIn('004625d8',called(p));self.assertNotIn('004625ac',called(p))

    def test_each_mode_comparison_is_fresh_not_stable_assumption(self):
        p=plan_bot_switch(CTX,1,fixture(9,mode_for_four=4))
        self.assertTrue(p.complete)
        self.assertEqual(writes(p,'mode_four_reset'),[(0x5697e4,4,0),(0x569838,1,0),(0x569870,1,0)])
        o=fixture(9);v=dict(o.values);del v['mode_for_two']
        self.assertEqual(plan_bot_switch(CTX,1,replace(o,values=v)).missing,'mode_for_two value')

    def test_mode_two_start_al_gate_never_falls_through_to_mode_four(self):
        for eax,expected in ((0,False),(0x100,False),(1,True),(0xff,True)):
            p=plan_bot_switch(CTX,1,fixture(2,mode_two_start_eax=eax,mode_for_four=4))
            self.assertTrue(p.complete);self.assertEqual(bool(writes(p,'mode_two_start')),expected)
            self.assertEqual(writes(p,'mode_four_reset'),[])

    def test_mode_five_and_unsupported_mode(self):
        self.assertEqual(writes(plan_bot_switch(CTX,1,fixture(5)),'mode_five_start'),[(CTX+0x38,1,1)])
        p=plan_bot_switch(CTX,1,fixture(6));self.assertTrue(p.complete)
        self.assertFalse(any(s.address==CTX+0x38 for s in p.stores))

    def test_stop_resets_all_fields_with_nonzero_sentinels(self):
        p=plan_bot_switch(CTX,0,fixture(2));self.assertTrue(p.complete)
        self.assertEqual(writes(p,'stop_context_reset'),[(CTX+x,w,v) for x,w,v in STOP_CONTEXT_RESETS])
        self.assertEqual(writes(p,'stop_global_reset'),list(STOP_GLOBAL_RESETS))
        self.assertEqual(len(p.stores),49)
        self.assertEqual(dict((a,v) for a,w,v in writes(p,'stop_global_reset'))[0x568dc0],14)
        self.assertEqual(called(p)[-1],'00464714')
        self.assertFalse(p.native_execution_verified);self.assertFalse(p.whole_helper_effects_verified)

    def test_stop_genie_requires_exact_low_byte_one_and_distinct_helper(self):
        for eax,yes in ((0,False),(1,True),(2,False),(0x101,True),(0x100,False)):
            p=plan_bot_switch(CTX,0,fixture(stop_genie_state_eax=eax))
            self.assertTrue(p.complete);self.assertEqual('004ca4c4' in called(p),yes)
            self.assertNotIn('00466cc4',called(p))

    def test_argument_is_low_byte_and_context_addition_wraps(self):
        p=plan_bot_switch(0xfffffff0,0x100,fixture());self.assertTrue(p.complete)
        self.assertEqual(p.key,'bot_stop');self.assertEqual(p.push_order,(0x100,0xfffffff0))
        self.assertEqual(p.stores[0].address,0x64)
        with self.assertRaises(ValueError):plan_bot_switch(CTX,True,fixture())

    def test_each_reached_value_and_normal_span_is_required(self):
        cases=((1,fixture()),(1,fixture(use_current_xy_eax=0)),(1,fixture(2)),(1,fixture(4)),(0,fixture(2,stop_genie_state_eax=1)))
        for flag,o in cases:
            full=plan_bot_switch(CTX,flag,o);self.assertTrue(full.complete)
            labels=[s[1] for s in full.steps if s[0]=='normal_return']
            for label in labels:
                p=plan_bot_switch(CTX,flag,replace(o,normal_returns={**o.normal_returns,label:False}))
                self.assertFalse(p.complete,(flag,label));self.assertEqual(p.missing,label+' normal return')
            fields=[s[1] for s in full.steps if s[0]=='observed_value']
            for name in fields:
                v=dict(o.values);del v[name]
                self.assertFalse(plan_bot_switch(CTX,flag,replace(o,values=v)).complete,(flag,name))

    def test_frame_keeps_consumed_values_and_projects_no_duplicate_stores(self):
        o=fixture(0);f=BotSwitchFrame(CTX,1)
        p=f.advance(replace(o,normal_returns={**o.normal_returns,'current_coordinates_label_span':False}))
        self.assertFalse(p.complete)
        changed=fixture(4,current_x_eax=999,current_y_eax=888)
        p=f.advance(O(changed.values,{'current_coordinates_label_span':True}))
        self.assertTrue(p.complete);self.assertEqual(writes(p,'coordinate_helper_normal'),[(CTX+0xcc,4,11),(CTX+0xd0,4,22)])
        self.assertIs(f.advance(O()),p)

    def test_stop_frame_retains_resets_while_final_helper_is_missing(self):
        o=fixture();f=BotSwitchFrame(CTX,0)
        p=f.advance(replace(o,normal_returns={**o.normal_returns,'stop_movement':False}))
        self.assertFalse(p.complete);self.assertEqual(len(p.stores),49)
        final=f.advance(O(normal_returns={'stop_movement':True}));self.assertTrue(final.complete)
        self.assertEqual(final.stores,p.stores)

    def test_chat_binding_waits_for_child_and_separate_parent_return(self):
        msg=ChatPartyMessage(1,7,b'Alice',b'go')
        for flag,key in ((1,'bot_start'),(0,'bot_stop')):
            gap=plan_bot_switch(CTX,flag,O());o=chat_obs(key,gap)
            self.assertFalse(plan_chat_commands(config(key),msg,o).complete)
            f=ChatCommandsFrame(config(key),msg);self.assertFalse(f.advance(o).complete)
            done=plan_bot_switch(CTX,flag,fixture())
            p=f.advance(chat_obs(key,done));self.assertTrue(p.complete)
            self.assertIs(p.actions[0].helper_execution,done)
            o=chat_obs(key,done)
            p=plan_chat_commands(config(key),msg,replace(o,helper_returns={**o.helper_returns,'action:'+key:False}))
            self.assertFalse(p.complete);self.assertEqual(p.missing,'action:'+key+' normal return')

    def test_chat_rejects_different_context_or_same_low_byte_different_argument(self):
        msg=ChatPartyMessage(1,7,b'Alice',b'go');key='bot_start'
        for ctx,flag in ((CTX+4,1),(CTX,0x101)):
            child=plan_bot_switch(ctx,flag,fixture())
            with self.assertRaises(ValueError):plan_chat_commands(config(key),msg,chat_obs(key,child))

if __name__=='__main__':unittest.main()
