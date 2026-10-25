"""Hidden own UI: real15-field widgets, 64bit threshold, prefix and profiles."""
import json,tempfile
from pathlib import Path
from control_settings import OPS,CONTROL_SETTING_FIELDS
from control_settings_trial import describe_control_settings_trial

def check_control_settings_ui(app):
 e=app.engine_page;p=app.panel;paths=dict(CONTROL_SETTING_FIELDS)
 old_values=dict(app.values);old_case=e.case.get();old_form=p.form.get()
 old_sample=e.control_settings_sample.get();old_hp=e.inputs['hp'].get()
 try:
  for op,(_,path) in zip(OPS,CONTROL_SETTING_FIELDS):app.profiles.update(app.values,path,False if op[0]=='flag' else '5')
  p.form.set('frmMain');p.render()
  p.widgets[paths[0x8a4]].invoke();p.widgets[paths[0x8a8]].invoke()
  assert app.values[paths[0x8a4]] is True and app.values[paths[0x8a8]] is True
  coin=p.widgets[paths[0x8b0]];coin.delete(0,'end');coin.insert(0,'4294967297')
  assert app.values[paths[0x8b0]]=='4294967297'
  e.case.set('Kontrol Ayarları');e.reset();e.inputs['hp'].set('unrelated invalid HP')
  assert e.control_settings_controls.grid_info() and not e.genie_settings_controls.grid_info()
  e.control_settings_sample.set('{}');e.tick(1)
  assert e.control_settings_trial.last.needed==('entry','004581b9') and not e.control_settings_trial.scalar_state
  e.control_settings_example();data=json.loads(e.control_settings_sample.get())
  data['normal_returns']['parser_outer_8b0']=False
  e.control_settings_sample.set(json.dumps(data));e.tick(1)
  assert e.control_settings_trial.last.needed==('normal','parser_outer_8b0')
  assert len(e.control_settings_trial.scalar_state)==4
  assert e.control_settings_trial.scalar_state[0x562194+0xbd]==(1,1)
  data['normal_returns']['parser_outer_8b0']=True;data['normal_returns']['text_cleanup_8b0']=False
  e.control_settings_sample.set(json.dumps(data));e.tick(1)
  assert e.control_settings_trial.last.needed==('normal','text_cleanup_8b0')
  assert e.control_settings_trial.scalar_state[0x562194+0xc8]==(4,1) and e.control_settings_trial.scalar_state[0x562194+0xcc]==(4,1)
  data['normal_returns']['text_cleanup_8b0']=True;e.control_settings_sample.set(json.dumps(data));e.tick(1)
  assert e.control_settings_trial.last.complete and len(e.control_settings_trial.scalar_state)==16
  assert describe_control_settings_trial(e.control_settings_trial)['coin_eşiği']==4294967297
  frame=e.control_settings_trial.frame;before=dict(e.control_settings_trial.scalar_state);e.tick(1)
  assert e.control_settings_trial.frame is frame and e.control_settings_trial.scalar_state==before
  coin.delete(0,'end');coin.insert(0,'-1');e.tick(1)
  assert e.control_settings_trial.last is None
  e.control_settings_example();e.tick(1);assert e.control_settings_trial.last.complete
  assert describe_control_settings_trial(e.control_settings_trial)['coin_eşiği']==-1
  with tempfile.TemporaryDirectory() as directory:
   target=Path(directory)/'control.json';app.profiles.save(target,app.values,app.lists)
   restored,_=app.profiles.load_document(target)
   assert all(restored[path]==app.values[path] for _,path in CONTROL_SETTING_FIELDS)
  e.control_settings_sample.set('{bad');e.tick(1);assert e.control_settings_trial.last is None
 finally:
  app.values.clear();app.values.update(old_values)
  e.control_settings_sample.set(old_sample);e.inputs['hp'].set(old_hp);e.case.set(old_case);e.reset()
  p.form.set(old_form);p.render()
 print('Control settings UI passed:15 actual fields, 64bit signed coin threshold, independent HP, prefix/outer/cleanup waits, stale capture rejection, idempotence and profile roundtrip; local only')

if __name__=='__main__':
 import tkinter as tk
 from app import Application
 root=tk.Tk();root.withdraw()
 try:check_control_settings_ui(Application(root))
 finally:root.destroy()
