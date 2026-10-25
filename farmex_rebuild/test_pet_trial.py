import json,unittest
from pet_settings import PET_SETTING_FIELDS
from pet_trial import (PetTrial,example_pet_settings_sample,example_pet_runtime_sample,
                       describe_pet_trial)
PATHS=dict(PET_SETTING_FIELDS)

def fixture():
    values={path:('10' if slot==0xf1c else False) for slot,path in PET_SETTING_FIELDS}
    values[PATHS[0xf20]]=True
    trial=PetTrial(lambda:(values,{}))
    return values,trial

def examples(trial):
    snapshot=trial.settings.current_snapshot()
    return example_pet_settings_sample(snapshot),json.loads(example_pet_runtime_sample(snapshot,trial))

class PetTrialTests(unittest.TestCase):
    def test_empty_settings_does_not_start_worker(self):
        _,t=fixture();self.assertIsNone(t.step('{}','{}'));self.assertIsNone(t.frame)
        self.assertEqual(t.settings.scalar_state,{})
    def test_real_control_projection_reaches_feed_and_owns_timer(self):
        values,t=fixture();values[PATHS[0xf14]]=True;s,r=examples(t)
        p=t.step(s,json.dumps(r));self.assertEqual(p.status,'feed_returned')
        self.assertEqual(t.settings.scalar_state[0x5620e0],(4,3))
        self.assertEqual(t.scalar_state[0x553c58],(4,10002))
        self.assertFalse(describe_pet_trial(t)['oyun_eylemi_doğrulandı'])
    def test_mode_none_preserves_old_mode_across_settings_change(self):
        values,t=fixture();s,r=examples(t);t.step(s,json.dumps(r))
        values[PATHS[0xf20]]=False;values[PATHS[0xf18]]=True;s,r=examples(t)
        p=t.step(s,json.dumps(r));self.assertEqual(p.status,'mode_returned')
        self.assertEqual(t.settings.scalar_state[0x5620e0],(4,3))
        self.assertIn(('set_mode','004c7fe4',(0x561ef8,3)),p.calls)
    def test_unknown_previous_mode_is_not_fabricated(self):
        values,t=fixture();values[PATHS[0xf20]]=False;values[PATHS[0xf18]]=True
        s,r=examples(t);p=t.step(s,json.dumps(r))
        self.assertFalse(p.complete);self.assertEqual(p.needed,('values','mode_compare'))
        self.assertNotIn(0x5620e0,t.settings.scalar_state)
    def test_settings_cleanup_wait_holds_worker_but_keeps_prefix(self):
        values,t=fixture();values[PATHS[0xf14]]=True;s,r=examples(t)
        d=json.loads(s);d['normal_returns']['text_cleanup_f1c']=False
        self.assertIsNone(t.step(json.dumps(d),json.dumps(r)))
        self.assertEqual(len(t.settings.scalar_state),4);self.assertIsNone(t.frame)
        d['normal_returns']['text_cleanup_f1c']=True
        self.assertEqual(t.step(json.dumps(d),json.dumps(r)).status,'feed_returned')
    def test_runtime_prefix_wait_resume_and_completed_idempotence(self):
        values,t=fixture();values[PATHS[0xf18]]=True;s,r=examples(t)
        r['values']['pet_exists_eax']=0;r['normal_returns']['summon']=False
        p=t.step(s,json.dumps(r));self.assertFalse(p.complete);self.assertEqual(len(t.scalar_state),3)
        r['values']['summon_clock_eax']=99;r['normal_returns']['summon']=True
        p=t.step(s,json.dumps(r));self.assertEqual(p.status,'summon_returned')
        self.assertEqual(t.scalar_state[0x561f84],(4,10000))
        before=dict(t.scalar_state);frame=t.frame;t.step(s,json.dumps(r))
        self.assertIs(frame,t.frame);self.assertEqual(t.scalar_state,before)
    def test_new_ticket_reuses_owned_timer_and_old_ticket_rejected(self):
        values,t=fixture();values[PATHS[0xf14]]=True;s,r=examples(t);old=json.dumps(r)
        t.step(s,old);s,r=examples(t);self.assertNotIn('food_last',r['values'])
        r['values']['food_clock_eax']=11000
        self.assertEqual(t.step(s,json.dumps(r)).status,'food_timer')
        with self.assertRaises(ValueError):t.step(s,old)
    def test_stale_panel_and_own_override_rejected(self):
        values,t=fixture();s,r=examples(t);values[PATHS[0xf14]]=True
        with self.assertRaises(ValueError):t.step(s,json.dumps(r))
        s,r=examples(t);r['values']['food_present']=0
        with self.assertRaises(ValueError):t.step(s,json.dumps(r))
        self.assertIsNone(t.last)
    def test_invalid_late_sample_keeps_prefix_and_can_resume(self):
        values,t=fixture();values[PATHS[0xf18]]=True;s,r=examples(t)
        r['values']['pet_exists_eax']=0;r['normal_returns']['summon']='invalid'
        with self.assertRaises(ValueError):t.step(s,json.dumps(r))
        self.assertEqual(len(t.scalar_state),3)
        r['normal_returns']['summon']=True
        self.assertEqual(t.step(s,json.dumps(r)).status,'summon_returned')
    def test_reset_clears_settings_worker_timers_and_tickets(self):
        values,t=fixture();values[PATHS[0xf14]]=True;s,r=examples(t);t.step(s,json.dumps(r))
        t.reset();self.assertFalse(t.scalar_state);self.assertFalse(t.settings.scalar_state)
        self.assertIsNone(t.frame);self.assertEqual(t.last_token,0)
    def test_identical_profile_document_invalidates_previous_ticket(self):
        values,_=fixture();holder=[values];t=PetTrial(lambda:(holder[0],{}))
        values[PATHS[0xf14]]=True;s,r=examples(t);t.step(s,json.dumps(r))
        holder[0]=dict(values)
        with self.assertRaises(ValueError):t.step(s,json.dumps(r))
        self.assertEqual(t.scalar_state,{});self.assertIsNone(t.frame)
        s,r=examples(t);self.assertIn('food_last',r['values'])
        self.assertEqual(t.step(s,json.dumps(r)).status,'feed_returned')
    def test_owned_timer_store_cannot_be_overridden(self):
        values,t=fixture();values[PATHS[0xf14]]=True;s,r=examples(t);t.step(s,json.dumps(r))
        s,r=examples(t);r['values']['food_last']=0
        with self.assertRaises(ValueError):t.step(s,json.dumps(r))
        self.assertEqual(t.scalar_state[0x553c58],(4,10002))
    def test_invalid_word_capture_is_not_frozen_into_frame(self):
        values,t=fixture();values[PATHS[0xf14]]=True;s,r=examples(t)
        r['values']['float_compare_status']=65536
        with self.assertRaises(ValueError):t.step(s,json.dumps(r))
        r['values']['float_compare_status']=0x4000
        self.assertEqual(t.step(s,json.dumps(r)).status,'feed_returned')

if __name__=='__main__':unittest.main()
