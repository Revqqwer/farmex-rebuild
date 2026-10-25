"""Hidden real-panel chat-skill checks; no game/native actions."""
import json
from chat_skill_requests import SPECS,ROOTS
from chat_skills_trial import example_chat_skills_sample

def check_chat_skills_ui(app):
 e=app.engine_page;p=app.panel;old_values=dict(app.values);old_form=p.form.get();old_case=e.case.get();old_hp=e.inputs['hp'].get()
 old=(e.chat_skills_packet.get(),e.chat_skills_sample.get(),e.chat_skills_codepage.get(),e.chat_skills_example_family.get())
 try:
  for spec in SPECS:
   app.profiles.update(app.values,ROOTS[spec[1]]+spec[2],False);app.profiles.update(app.values,ROOTS[spec[1]]+spec[3],'go')
  p.form.set('frmMain');p.render();e.case.set('Chat Yetenek İsteği');e.reset()
  e.inputs['hp'].set('unused bad HP');assert e.chat_skills_controls.winfo_manager()=='grid'
  e.chat_skills_codepage.set('1254');e.chat_skills_packet.set('10');e.chat_skills_sample.set('{}');e.tick(1)
  assert not e.chat_skills_trial.last.complete and e.chat_skills_trial.frame is None
  for spec in SPECS:
   key,family,check,text,*_=spec;path=ROOTS[family]+check
   p.widgets[path].invoke();e.chat_skills_example_family.set(family);before=dict(app.values);e.chat_skills_example()
   assert app.values==before #Example must not change real panel settings.
   e.tick(1);assert e.chat_skills_trial.last.complete and e.chat_skills_trial.last.queued_request.key==key
   assert 'İstek: '+key in e.output.get('1.0','end');frame=e.chat_skills_trial.frame;e.tick(1);assert e.chat_skills_trial.frame is frame
   p.variables[ROOTS[family]+text].set('GO');e.tick(1);assert e.chat_skills_trial.last.queued_request is None
   p.variables[ROOTS[family]+text].set('go');p.widgets[path].invoke()
  p.widgets[ROOTS['Mage']+'chChatTP'].invoke();e.chat_skills_example_family.set('Mage');e.chat_skills_example()
  raw=json.loads(example_chat_skills_sample());del raw['normal_returns']['compare:mage_tp']
  e.chat_skills_sample.set(json.dumps(raw));e.tick(1);assert not e.chat_skills_trial.last.complete
  e.chat_skills_sample.set('{"values":"consumed","normal_returns":{"compare:mage_tp":true}}');e.tick(1)
  assert e.chat_skills_trial.last.complete and e.chat_skills_trial.last.queued_request.key=='mage_tp'
  e.chat_skills_sample.set('{bad');e.tick(1);assert e.chat_skills_trial.last is None and e.chat_skills_trial.frame is None
  e.case.set('Chat Komutları');e.reset();assert e.chat_skills_controls.winfo_manager()==''
 finally:
  app.values.clear();app.values.update(old_values)
  for var,value in zip((e.chat_skills_packet,e.chat_skills_sample,e.chat_skills_codepage,e.chat_skills_example_family),old):var.set(value)
  e.inputs['hp'].set(old_hp);e.case.set(old_case);e.reset();p.form.set(old_form);p.render()
 print('Chat skill UI passed: 18 real widgets, all9 requests, fresh flags/exact text, cached prefix, example preserves panel, malformed reset and hidden controls; no skill execution')
