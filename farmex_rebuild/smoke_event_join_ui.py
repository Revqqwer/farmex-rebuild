"""Own hidden event panel/trial smoke, no native game actions."""
import json,tempfile
from pathlib import Path
from event_join import EVENT_FIELDS,EVENT_JOIN_INPUTS

def check_event_join_ui(app):
 e=app.engine_page;p=app.panel;old_values=dict(app.values);old_case=e.case.get();old_form=p.form.get()
 old_sample=e.event_sample.get();old_hp=e.inputs['hp'].get()
 paths={key:path for path,(key,name,offset,slot) in zip(EVENT_JOIN_INPUTS,EVENT_FIELDS)}
 try:
  for path in EVENT_JOIN_INPUTS:app.profiles.update(app.values,path,False)
  p.form.set('frmMain');p.render();p.widgets[paths['bdw']].invoke()
  e.case.set('Etkinlik Katılımı');e.reset();e.inputs['hp'].set('unrelated invalid HP')
  e.event_sample.set('{}');e.tick(1)
  assert e.event_trial.last.needed==('normal','entry_setup')
  assert e.event_trial.settings.stores[-1]==(0x562201,1,1)
  e.event_example();data=json.loads(e.event_sample.get());del data['packet_children']['bdw_join']['attempt']['tick']
  e.event_sample.set(json.dumps(data));e.tick(1);assert e.event_trial.last.needed==('child','bdw_join')
  assert e.event_trial.last.queue.records==()
  data['packet_children']['bdw_join']['attempt'].update(gate=0,tick=333)
  data['packet_children']['bdw_join']['normal_returns']['return']=False
  e.event_sample.set(json.dumps(data));e.tick(1);assert len(e.event_trial.last.queue.records)==1
  assert not e.event_trial.last.complete
  data['packet_children']['bdw_join']['normal_returns']['return']=True
  e.event_sample.set(json.dumps(data));e.tick(1);assert e.event_trial.last.complete
  assert e.event_trial.last.queue.records[0].payload.hex()=='5f080200'
  frame=e.event_trial.frame;e.tick(1);assert e.event_trial.frame is frame and len(e.event_trial.last.queue.records)==1
  p.widgets[paths['chaos']].invoke();e.tick(1);assert e.event_trial.last is None
  assert e.event_trial.frame is not frame and len(e.event_trial.frame.queue.records)==1
  e.event_example();e.tick(1);assert e.event_trial.last.complete and len(e.event_trial.last.queue.records)==2
  assert e.event_trial.last.queue.records[-1].payload.hex()=='5f081800'
  for path in EVENT_JOIN_INPUTS:app.profiles.update(app.values,path,path==paths['ft'])
  p.render();e.reset();e.event_example();data=json.loads(e.event_sample.get())
  data['packet_children']['target_prepare']['normal_returns']['target_copy']=False
  e.event_sample.set(json.dumps(data));e.tick(1)
  assert e.event_trial.last.needed==('child','target_prepare') and e.event_trial.last.queue.records==()
  data['packet_children']['target_prepare']['normal_returns']['target_copy']=True
  e.event_sample.set(json.dumps(data));e.tick(1)
  assert e.event_trial.last.complete and [len(r.payload) for r in e.event_trial.last.queue.records]==[10,17]
  assert e.event_trial.last.queue.records[0].payload[2:6]==(3001).to_bytes(4,'little')
  e.reset();e.event_example();data=json.loads(e.event_sample.get());data['values']['target_first_eax']=3000
  data['fallback_child']={'values':{'first_profile_byte':1,'profile1_root_slot':0x1000,'profile1_ecx':0x2000,'profile1_target':0x3000},
   'normal_returns':{'profile1_callback':False,'return':True}}
  e.event_sample.set(json.dumps(data));e.tick(1)
  assert e.event_trial.last.needed==('child','target_fallback') and e.event_trial.last.stores==()
  data['fallback_child']['normal_returns']['profile1_callback']=True
  e.event_sample.set(json.dumps(data));e.tick(1)
  assert e.event_trial.last.complete and e.event_trial.last.queue.records==()
  assert dict(e.event_trial.last.children)['target_fallback'].callbacks==( ('profile1_callback',0x3000,0x2000,()), )
  with tempfile.TemporaryDirectory() as directory:
   path=Path(directory)/'events.json';app.profiles.save(path,app.values,app.lists)
   restored,_=app.profiles.load_document(path)
   assert all(restored[k]==app.values[k] for k in EVENT_JOIN_INPUTS)
  e.event_sample.set('{bad');e.tick(1);assert e.event_trial.last is None
  assert 'Oyunda katılım doğrulandı: False' in e.output.get('1.0','end')
 finally:
  app.values.clear();app.values.update(old_values);e.event_sample.set(old_sample);e.inputs['hp'].set(old_hp)
  e.case.set(old_case);e.reset();p.form.set(old_form);p.render()
 print('Event join UI passed: six real flags, bounded settings ->worker ->packet ->own queue, clock/helper gaps, target10 before FT17, typed fallback callback gap/resume, no duplicate, changed snapshot rejection/seed preservation, fresh priority, profile roundtrip and stale-result clearing; no native game action')

if __name__=='__main__':
 import tkinter as tk
 from app import Application
 root=tk.Tk();root.withdraw()
 try:
  app=Application(root);check_event_join_ui(app)
 finally:
  if 'app' in globals():app.connection_page.close()
  root.destroy()
