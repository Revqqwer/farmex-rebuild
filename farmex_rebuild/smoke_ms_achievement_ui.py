"""Invoke actual own source button; no network, native or reward execution."""
import json
from ms_achievement import BUTTON_PATH
from ms_achievement_trial import example_achievement_sample

def check_ms_achievement_ui(app):
 e=app.engine_page;p=app.panel;old_case=e.case.get();old_form=p.form.get();old_sample=e.achievement_sample.get();old_hp=e.inputs['hp'].get()
 try:
  p.form.set('frmMain');p.render();e.case.set('Achieve MS');e.reset();e.inputs['hp'].set('unrelated invalid HP')
  button=p.widgets[BUTTON_PATH];assert 'disabled' not in button.state()
  button.invoke();assert e.case.get()=='Achieve MS';assert not e.achievement_trial.last.complete
  assert e.achievement_trial.last.queue.records==()
  r=json.loads(example_achievement_sample());r['requests']['0']['attempt']['normal_returned']=False
  e.achievement_sample.set(json.dumps(r));e.tick(1)
  assert len(e.achievement_trial.last.queue.records)==1
  frame=e.achievement_trial.frame;button.invoke()
  assert e.achievement_trial.frame is frame and len(e.achievement_trial.last.queue.records)==1
  e.achievement_sample.set(example_achievement_sample());e.tick(1)
  assert e.achievement_trial.last.complete and len(e.achievement_trial.last.queue.records)==11
  e.tick(1);assert len(e.achievement_trial.last.queue.records)==11
  p.render();p.widgets[BUTTON_PATH].invoke()
  assert e.achievement_trial.frame is not frame and e.achievement_sample.get()=='{}'
  assert len(e.achievement_trial.last.queue.records)==11
  e.achievement_sample.set(example_achievement_sample());e.tick(1)
  assert len(e.achievement_trial.last.queue.records)==22 and not e.achievement_trial.last.reward_verified
  e.achievement_sample.set('{bad');e.tick(1);assert e.achievement_trial.last is None
  assert 'Yerel kuyruk kaydı' in e.output.get('1.0','end')
  e.reset();assert e.achievement_trial.frame.queue.records==()
 finally:
  e.inputs['hp'].set(old_hp);e.achievement_sample.set(old_sample);e.case.set(old_case);e.reset();p.form.set(old_form);p.render()
 print('Achieve MS UI passed: actual source button adapter survives rerender, default missing receipts, pending-click continuation,11 ordered own records without duplicates, completed-click new event preserves queue, reset clears and invalid sample clears stale result; no reward/network/native effects')

if __name__=='__main__':
 import tkinter as tk
 from app import Application
 root=tk.Tk();root.withdraw()
 try:
  app=Application(root);check_ms_achievement_ui(app)
 finally:
  if 'app' in globals():app.connection_page.close()
  root.destroy()
