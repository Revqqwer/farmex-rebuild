"""Own real widgets feed MS settings/activation trial; no game actions."""
import json,tempfile
from pathlib import Path
from monster_stone import MS_SETTING_INPUTS,MS_ENABLE_INPUT,WALLHACK_INPUT
from monster_stone_trial import example_ms_activation

def check_monster_stone_ui(app):
 e=app.engine_page;p=app.panel;old_values=dict(app.values);old_case=e.case.get();old_form=p.form.get()
 old_sample=e.ms_sample.get();old_hp=e.inputs['hp'].get()
 try:
  for path,val in zip(MS_SETTING_INPUTS+(MS_ENABLE_INPUT,WALLHACK_INPUT),(True,False,False,False,False)):
   app.profiles.update(app.values,path,val)
  p.form.set('frmMain');p.render();e.case.set('Monster Stone');e.reset();e.inputs['hp'].set('unrelated bad HP')
  assert 'disabled' in p.widgets[MS_SETTING_INPUTS[1]].state()
  p.widgets[MS_ENABLE_INPUT].invoke();p.widgets[MS_SETTING_INPUTS[2]].invoke()
  e.ms_sample.set('{}');e.tick(1)
  assert e.ms_trial.last.settings.mode_after==0 and not e.ms_trial.last.activation.complete
  assert app.values[WALLHACK_INPUT] is False
  e.ms_sample.set(json.dumps({'normal_returns':{'wallhack_setter':True}}));e.tick(1)
  assert app.values[WALLHACK_INPUT] is True
  assert p.variables[WALLHACK_INPUT].get() is True
  assert not e.ms_trial.last.activation.complete
  e.ms_sample.set(json.dumps({'normal_returns':{'bot_start':True,'activation_return':True}}));e.tick(1)
  assert e.ms_trial.last.activation.complete and not e.ms_trial.last.main_worker_executed
  with tempfile.TemporaryDirectory() as directory:
   path=Path(directory)/'own_ms.json';app.profiles.save(path,app.values,app.lists)
   restored=app.profiles.load(path)
   assert restored[MS_ENABLE_INPUT] and restored[MS_SETTING_INPUTS[2]] and restored[WALLHACK_INPUT]
  p.widgets[MS_ENABLE_INPUT].invoke();e.ms_sample.set(example_ms_activation());e.tick(1)
  assert e.ms_trial.last.activation.stores==((0x561f5c,4,0),)
  assert app.values[WALLHACK_INPUT] is True
  e.ms_sample.set('{bad');e.tick(1);assert e.ms_trial.last is None
 finally:
  app.values.clear();app.values.update(old_values);e.ms_sample.set(old_sample);e.inputs['hp'].set(old_hp)
  e.case.set(old_case);e.reset();p.form.set(old_form);p.render()
 print('Monster Stone UI passed: real enable/alarm/boss widgets, source-disabled all-mob preserved, missing setter gate, own derived WallHack prefix, separate bot-start/return, disable-only MS flag and profile roundtrip; no main-worker/game effects')

if __name__=='__main__':
 import tkinter as tk
 from app import Application
 root=tk.Tk();root.withdraw()
 try:
  app=Application(root);check_monster_stone_ui(app)
 finally:
  if 'app' in globals():app.connection_page.close()
  root.destroy()
