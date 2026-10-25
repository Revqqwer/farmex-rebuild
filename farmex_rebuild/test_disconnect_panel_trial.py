import json,unittest
from disconnect_panel_trial import *


class OwnUTF8Codec:
    def __init__(self,codepage):self.codepage=codepage
    def encode(self,text):return text.encode('utf-8'),False


PATHS=dict(DC_SETTING_FIELDS)


def fixture():
    values={};routes={}
    for slot,path in DC_SETTING_FIELDS:
        kind=KINDS[slot]
        values[path]=False if kind=='flag' else 2 if kind=='index' else '30' if kind=='number' else 'yerel metin'
    values[PATHS[ROUTE_SLOT]]=1;routes[PATHS[ROUTE_SLOT]]='Örnek.R'
    trial=DisconnectSettingsTrial(lambda:(values,{}),lambda:(routes,1254))
    data=json.loads(example_disconnect_sample(trial.current_snapshot(),OwnUTF8Codec))
    return values,routes,trial,data


class DisconnectPanelTrialTests(unittest.TestCase):
    def test_empty_sample_does_not_create_shadow(self):
        _,_,t,_=fixture();p=t.step('{}')
        self.assertEqual(p.needed,('entry','00457d02'));self.assertFalse(t.scalar_state)

    def test_fourteen_fields_actual_route_text_and_context_projection(self):
        values,_,t,_=fixture();values[PATHS[0x828]]=True
        p=t.step(example_disconnect_sample(t.current_snapshot(),OwnUTF8Codec))
        self.assertTrue(p.complete);self.assertEqual(t.scalar_state[0x56221e],(1,1))
        self.assertEqual(t.scalar_state[0x562224],(4,2));self.assertEqual(t.scalar_state[0x562228],(4,30))
        self.assertEqual(t.string_state[0x562230],'Örnek.R'.encode())
        self.assertEqual(len(DC_SETTING_INPUTS),14)

    def test_unread_controls_do_not_change_snapshot_or_forced_flag(self):
        values,_,t,data=fixture();old=t.current_snapshot()
        values['frmMain/MainTab/SheetKontrol/GroupBox32/chDCControlWaitSecond']=False
        values['frmMain/MainTab/SheetKontrol/GroupBox32/chRelogAfterUseManuelRoute']=False
        self.assertEqual(t.current_snapshot(),old)
        t.step(json.dumps(data));self.assertEqual(t.scalar_state[0x56222e],(1,1))

    def test_signed_combo_minus_one_is_raw_dword_not_default(self):
        values,_,t,_=fixture();values[PATHS[0x83c]]=-1
        p=t.step(example_disconnect_sample(t.current_snapshot(),OwnUTF8Codec))
        self.assertTrue(p.complete);self.assertEqual(t.scalar_state[0x562224],(4,0xffffffff))

    def test_conflicting_panel_getter_rejected(self):
        _,_,t,data=fixture();data['values']={'checked_828':1}
        with self.assertRaises(ValueError):t.step(json.dumps(data))
        self.assertFalse(t.scalar_state)

    def test_stale_panel_value_does_not_apply_old_sample(self):
        values,_,t,data=fixture();t.step(json.dumps(data));old=dict(t.scalar_state)
        values[PATHS[0x834]]='31'
        with self.assertRaises(ValueError):t.step(json.dumps(data))
        self.assertEqual(t.scalar_state,old);self.assertIsNone(t.last)

    def test_route_text_change_with_same_index_is_stale(self):
        values,routes,t,data=fixture();index=values[PATHS[ROUTE_SLOT]]
        routes[PATHS[ROUTE_SLOT]]='Başka.R'
        self.assertEqual(values[PATHS[ROUTE_SLOT]],index)
        with self.assertRaises(ValueError):t.step(json.dumps(data))

    def test_source_numeric_catch_receipt_is_not_guessed_from_text(self):
        values,_,t,_=fixture();values[PATHS[0x834]]='invalid native text'
        with self.assertRaises(ValueError):example_disconnect_sample(t.current_snapshot(),OwnUTF8Codec)
        data={'entry_reached':True,'normal_returns':{},'integer_children':{},'ansi_hex':{}}
        # Use an explicit fallback capture while leaving the actual panel text invalid.
        values[PATHS[0x834]]='30';data=json.loads(example_disconnect_sample(t.current_snapshot(),OwnUTF8Codec))
        values[PATHS[0x834]]='invalid native text';data['panel_snapshot_sha256']=protection_snapshot_digest(t.current_snapshot())
        data['integer_children']['834']={'text_copy_returned':True,'route':'catch_landing','catch_landing_returned':True,'cleanup_returned':True}
        p=t.step(json.dumps(data));self.assertTrue(p.complete);self.assertEqual(t.scalar_state[0x562228],(4,30))

    def test_partial_shadow_and_same_frame_resume(self):
        _,_,t,data=fixture();data['normal_returns']['assign_854']=False
        p=t.step(json.dumps(data));self.assertEqual(p.needed,('normal','assign_854'))
        self.assertEqual(len(t.string_state),1);frame=t.frame
        data['normal_returns']['assign_854']=True;p=t.step(json.dumps(data))
        self.assertTrue(p.complete);self.assertIs(t.frame,frame);self.assertEqual(len(t.string_state),4)

    def test_late_invalid_ansi_preserves_accepted_scalar_prefix(self):
        values,_,t,data=fixture();values[PATHS[0x828]]=True
        data=json.loads(example_disconnect_sample(t.current_snapshot(),OwnUTF8Codec));data['ansi_hex']['84c']='xx'
        with self.assertRaises(ValueError):t.step(json.dumps(data))
        self.assertEqual(t.scalar_state[0x56221e],(1,1));self.assertFalse(t.string_state)

    def test_same_frame_idempotence_and_explicit_reset(self):
        _,_,t,data=fixture();t.step(json.dumps(data));old=dict(t.scalar_state);frame=t.frame
        t.step(json.dumps(data));self.assertEqual(t.scalar_state,old);self.assertIs(t.frame,frame)
        t.reset();self.assertFalse(t.scalar_state);self.assertFalse(t.string_state)

    def test_required_snapshot_types_and_no_native_claim(self):
        values,routes,t,data=fixture();values[PATHS[0x83c]]=True
        with self.assertRaises(ValueError):t.current_snapshot()
        values[PATHS[0x83c]]=2;t.step(json.dumps(data))
        self.assertFalse(describe_disconnect_trial(t)['oyunda_uygulama_doğrulandı'])
