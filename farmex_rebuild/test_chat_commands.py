import unittest
from dataclasses import replace
from chat_commands import *

def config(overrides=None):
    overrides={} if overrides is None else overrides
    return ChatCommandsConfiguration(tuple(CommandSetting(key,*overrides.get(key,(1,key.encode()))) for key,*_ in SPECS))

def observations(**changes):
    returns={prefix+key:True for key,*_ in SPECS for prefix in ('compare:','action:')}
    returns.update(genie_start_state=True,genie_remaining=True,genie_stop_state=True)
    return replace(ChatCommandsObservation(returns,20,0x41a00000,10,0x41200000,0,0,1,1),**changes)

def message(text=b'disconnect',channel=1):return ChatPartyMessage(channel,7,b'Alice',text)

class ChatCommandTests(unittest.TestCase):
    def test_each_command_maps_to_distinct_source_call_and_push_order(self):
        expected={'disconnect':('004c7e0c',(0x561ef8,)),'return_center':('004646b4',(0x41a00000,0x41200000)),
                  'bot_start':('0040ae0c',(1,0x561f34)),'bot_stop':('0040ae0c',(0,0x561f34)),
                  'genie_start':('00466cc4',(1,)),'genie_stop':('00466cc4',(0,)),
                  'stand':('004c8d48',(0x561ef8,)),'town':('00465678',())}
        for key,(helper,pushes) in expected.items():
            p=plan_chat_commands(config(),message(key.encode()),observations())
            self.assertTrue(p.complete);self.assertEqual(len(p.actions),1)
            self.assertEqual((p.actions[0].helper,p.actions[0].push_order),(helper,pushes))
            self.assertFalse(p.native_execution_verified or p.actions[0].native_execution_verified)

    def test_same_keyword_runs_all_enabled_commands_in_runtime_order(self):
        c=config({key:(1,b'go') for key,*_ in SPECS})
        p=plan_chat_commands(c,message(b'go'),observations())
        self.assertTrue(p.complete);self.assertEqual([a.key for a in p.actions],[s[0] for s in SPECS])
        self.assertEqual(len(p.actions),8)

    def test_disabled_commands_still_require_comparison_normal_return(self):
        c=config({key:(0,b'go') for key,*_ in SPECS})
        p=plan_chat_commands(c,message(b'go'),ChatCommandsObservation())
        self.assertFalse(p.complete);self.assertEqual(p.missing,'compare:disconnect normal return')
        p=plan_chat_commands(c,message(b'go'),observations(helper_returns={'compare:'+key:True for key,*_ in SPECS}))
        self.assertTrue(p.complete);self.assertEqual(p.actions,())

    def test_exact_bytes_no_casefold_trim_or_channel_gate_in_reached_span(self):
        for text in (b'DISCONNECT',b' disconnect',b'disconnect ',b'disconnect\0'):
            p=plan_chat_commands(config(),message(text),observations())
            self.assertTrue(p.complete);self.assertEqual(p.actions,())
        p=plan_chat_commands(config(),message(channel=3),observations())
        self.assertEqual(p.actions[0].key,'disconnect')
        p=plan_chat_commands(config({'disconnect':(255,b'')}),message(b''),observations())
        self.assertEqual(p.actions[0].key,'disconnect')

    def test_genie_start_blocker_skips_state_and_remaining_helpers(self):
        o=ChatCommandsObservation({'compare:'+key:True for key,*_ in SPECS},genie_blocked_byte=2)
        p=plan_chat_commands(config(),message(b'genie_start'),o)
        self.assertTrue(p.complete);self.assertEqual(p.actions,())
        self.assertFalse(any(s[0]=='helper' for s in p.steps))

    def test_genie_start_requires_low_al_zero_state_and_nonzero_remaining(self):
        for state,remaining,expected in ((1,1,False),(0x100,0x100,False),(0x100,0xff,True),(0,1,True)):
            p=plan_chat_commands(config(),message(b'genie_start'),observations(genie_start_state_eax=state,genie_remaining_eax=remaining))
            self.assertTrue(p.complete);self.assertEqual(bool(p.actions),expected)
        p=plan_chat_commands(config(),message(b'genie_start'),observations(genie_remaining_eax=None))
        self.assertFalse(p.complete);self.assertEqual(p.actions,())

    def test_genie_stop_requires_exact_low_byte_one_and_fresh_state(self):
        for eax,expected in ((0,False),(0x100,False),(1,True),(0x101,True),(2,False),(255,False)):
            p=plan_chat_commands(config(),message(b'genie_stop'),observations(genie_stop_state_eax=eax))
            self.assertTrue(p.complete);self.assertEqual(bool(p.actions),expected)
        c=config({'genie_start':(1,b'go'),'genie_stop':(1,b'go')})
        p=plan_chat_commands(c,message(b'go'),observations(genie_stop_state_eax=None))
        self.assertFalse(p.complete);self.assertEqual([a.key for a in p.actions],['genie_start'])
        self.assertIn('fresh Genie-stop',p.missing)

    def test_center_reads_y_and_post_round_before_x_with_signed_fild(self):
        p=plan_chat_commands(config(),message(b'return_center'),observations(center_y_dword=0xffffffff,center_y_f32_bits=0xbf800000,center_x_dword=None))
        self.assertFalse(p.complete);self.assertIn('center X DWORD',p.missing)
        self.assertIn(('FILD_signed32',0x562004,0xffffffff,-1),p.steps)
        self.assertIn(('FSTP_f32',0xbf800000),p.steps)
        self.assertEqual(p.actions,())
        p=plan_chat_commands(config(),message(b'return_center'),observations(center_y_f32_bits=None))
        self.assertFalse(p.complete);self.assertIn('Y post-FSTP',p.missing)

    def test_missing_action_return_keeps_intent_but_stops_next_comparison(self):
        o=observations(helper_returns={**observations().helper_returns,'action:disconnect':False})
        p=plan_chat_commands(config(),message(),o)
        self.assertFalse(p.complete);self.assertEqual([a.key for a in p.actions],['disconnect'])
        self.assertEqual(p.missing,'action:disconnect normal return')
        self.assertFalse(any(s[0]=='00457388' and s[1]=='return_center' for s in p.steps))

    def test_frame_resumes_consumed_prefix_without_new_action_intents(self):
        c=config({key:(1,b'go') for key,*_ in SPECS});f=ChatCommandsFrame(c,message(b'go'))
        o=observations(center_y_f32_bits=None)
        p=f.advance(o);self.assertFalse(p.complete);self.assertEqual([a.key for a in p.actions],['disconnect'])
        # Earlier Y and first action receipts are not supplied a second time.
        follow=replace(observations(),center_y_dword=999,helper_returns={k:v for k,v in observations().helper_returns.items() if k not in ('compare:disconnect','action:disconnect','compare:return_center')})
        p=f.advance(follow);self.assertTrue(p.complete);self.assertEqual(len(p.actions),8)
        self.assertIn(('FILD_signed32',0x562004,20,20),p.steps)
        self.assertIs(f.advance(ChatCommandsObservation()),p)

    def test_panel_lossless_codepage_and_c_string_truncation(self):
        values={}
        for _,check,text,*_ in SPECS:values[ROOT+check]=True;values[ROOT+text]='çağrı\0tail'
        c=compile_chat_commands(values,WindowsNameCodec(1254))
        self.assertEqual(c.settings[0].command,'çağrı'.encode('cp1254'));self.assertEqual(c.codepage,1254)
        values[ROOT+SPECS[0][2]]='😀'
        with self.assertRaises(ValueError):compile_chat_commands(values,WindowsNameCodec(1254))

    def test_unknown_inputs_and_wrong_configuration_order_are_rejected(self):
        with self.assertRaises(ValueError):ChatCommandsObservation(genie_blocked_byte=256)
        with self.assertRaises(ValueError):ChatCommandsObservation(center_x_f32_bits=True)
        with self.assertRaises(ValueError):ChatCommandsConfiguration(tuple(reversed(config().settings)))
        with self.assertRaises(ValueError):plan_chat_commands(config(),b'go',observations())

if __name__=='__main__':unittest.main()
