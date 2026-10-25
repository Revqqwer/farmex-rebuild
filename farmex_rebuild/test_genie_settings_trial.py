import json,unittest
from dataclasses import replace
from genie_settings import OPS,GENIE_SETTING_FIELDS,GenieSettingsFrame,GenieSettingsObservation
from genie_settings_trial import GenieSettingsTrial,example_genie_settings_sample,describe_genie_settings_trial

PATHS=dict(GENIE_SETTING_FIELDS)


def fixture():
    values={path:False for _,path in GENIE_SETTING_FIELDS}
    t=GenieSettingsTrial(lambda:(values,{}));data=json.loads(example_genie_settings_sample(t.current_snapshot()))
    return values,t,data


class GenieSettingsTests(unittest.TestCase):
    def test_explicit_middle_span_and_end_before_coupon_sync(self):
        p=GenieSettingsFrame().advance(GenieSettingsObservation())
        self.assertEqual(p.needed,('entry','004580ac'))
        o=GenieSettingsObservation(True,{'checked_%03x'%slot:0 for _,slot,_ in OPS},
                                  {'checked_%03x'%slot:True for _,slot,_ in OPS})
        p=GenieSettingsFrame().advance(o)
        self.assertTrue(p.complete);self.assertEqual(p.next_address,0x458143)
        self.assertEqual(len(p.stores),5)
        self.assertFalse(any('prologue'==label for _,_,label in p.calls))

    def test_raw_source_al_and_context_wrap(self):
        o=GenieSettingsObservation(True,{'checked_%03x'%slot:0x102 for _,slot,_ in OPS},
                                  {'checked_%03x'%slot:True for _,slot,_ in OPS})
        p=GenieSettingsFrame(context=0xffffff80).advance(o)
        self.assertEqual(p.stores[0],(0x38,1,2))

    def test_empty_capture_does_not_initialize_shadow(self):
        _,t,_=fixture();p=t.step('{}')
        self.assertEqual(p.needed,('entry','004580ac'));self.assertFalse(t.scalar_state)

    def test_actual_panel_flags_map_in_source_order(self):
        values,t,_=fixture();values[PATHS[0xbd0]]=True;values[PATHS[0xbd4]]=True
        p=t.step(example_genie_settings_sample(t.current_snapshot()))
        self.assertTrue(p.complete);self.assertEqual(t.scalar_state[0x56224c],(1,1))
        self.assertEqual(t.scalar_state[0x56224e],(1,1))
        self.assertEqual([a-0x562194 for a,_,_ in p.stores],[0xb8,0xb9,0xba,0xbb,0xbc])

    def test_no_mob_and_free_genie_controls_not_used(self):
        values,t,data=fixture();snapshot=t.current_snapshot()
        for name,value in (('chGenieStartStopNoMob',True),('txtGenieStartStopNoMob','777')):
            values['frmMain/MainTab/SheetKontrol/grpGenie/'+name]=value
        values['frmMain/MainTab/SheetGenel/GroupBox48/chFreeGenie']=True
        self.assertEqual(t.current_snapshot(),snapshot)
        t.step(json.dumps(data));self.assertEqual(len(t.scalar_state),5)

    def test_panel_override_and_stale_snapshot_rejected(self):
        values,t,data=fixture();data['values']={'checked_bd0':1}
        with self.assertRaises(ValueError):t.step(json.dumps(data))
        data=json.loads(example_genie_settings_sample(t.current_snapshot()));values[PATHS[0xbd0]]=True
        with self.assertRaises(ValueError):t.step(json.dumps(data))
        self.assertFalse(t.scalar_state)

    def test_prefix_wait_resume_and_idempotence(self):
        _,t,data=fixture();data['normal_returns']['checked_bd4']=False
        p=t.step(json.dumps(data));self.assertEqual(len(t.scalar_state),2)
        frame=t.frame;self.assertEqual(p.needed,('normal','checked_bd4'))
        data['normal_returns']['checked_bd4']=True;p=t.step(json.dumps(data))
        self.assertTrue(p.complete);self.assertEqual(len(t.scalar_state),5);self.assertIs(t.frame,frame)
        before=dict(t.scalar_state);t.step(json.dumps(data));self.assertEqual(t.scalar_state,before)

    def test_late_bad_capture_preserves_accepted_prefix(self):
        values,t,data=fixture();values[PATHS[0xbd0]]=True
        data=json.loads(example_genie_settings_sample(t.current_snapshot()));data['values']={'checked_be8':'invalid'}
        with self.assertRaises(ValueError):t.step(json.dumps(data))
        self.assertEqual(t.scalar_state[0x56224c],(1,1));self.assertEqual(len(t.scalar_state),4)

    def test_explicit_reset_and_invalid_panel_type(self):
        values,t,data=fixture();t.step(json.dumps(data));t.reset();self.assertFalse(t.scalar_state)
        values[PATHS[0xbd0]]=1
        with self.assertRaises(ValueError):t.current_snapshot()

    def test_local_only_claim(self):
        _,t,data=fixture();p=t.step(json.dumps(data))
        self.assertFalse(p.whole_producer_verified or p.native_execution_verified or p.live_compatibility_verified)
        self.assertFalse(describe_genie_settings_trial(t)['oyunda_uygulama_doğrulandı'])
