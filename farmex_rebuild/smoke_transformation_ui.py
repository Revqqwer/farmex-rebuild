"""Hidden owned Tk widgets -> TS source producer/helper model; no game action."""
import json,tempfile
from pathlib import Path
from transformation import TRANSFORMATION_INPUTS,SKILLS

def check_transformation_ui(app):
 e=app.engine_page;p=app.panel;old_values=dict(app.values);old_case=e.case.get();old_form=p.form.get()
 old_sample=e.transformation_sample.get();old_hp=e.inputs['hp'].get()
 enabled,wait,route,combo=TRANSFORMATION_INPUTS
 try:
  for path,value in zip(TRANSFORMATION_INPUTS,(False,'10',False,0)):app.profiles.update(app.values,path,value)
  p.form.set('frmMain');p.render();p.widgets[enabled].invoke()
  p.widgets[combo].current(17);p.widgets[combo].event_generate('<<ComboboxSelected>>')
  app.root.update_idletasks()
  assert app.values[enabled] is True and app.values[combo]==17
  e.case.set('Transformation');e.reset();e.inputs['hp'].set('unrelated invalid HP')
  e.transformation_sample.set('{}');e.tick(1)
  assert e.transformation_trial.last.settings.needed==('entry','0040929a')
  assert e.transformation_trial.queue.records==()
  e.transformation_example();data=json.loads(e.transformation_sample.get());del data['use']['queue_tick']
  e.transformation_sample.set(json.dumps(data));e.tick(1)
  assert e.transformation_trial.last.settings.selected_skill==SKILLS[17]
  assert not e.transformation_trial.last.use.complete and e.transformation_trial.queue.records==()
  data['use']['queue_tick']=333;data['use']['queue_gate']=0;data['use']['cast_returned']=False
  e.transformation_sample.set(json.dumps(data));e.tick(1)
  assert len(e.transformation_trial.queue.records)==1 and not e.transformation_trial.last.use.complete
  payload=e.transformation_trial.queue.records[0].payload
  assert payload[2:6]==SKILLS[17].to_bytes(4,'little') and payload[6:14]==bytes.fromhex('7856341278563412')
  data['use']['cast_returned']=True;e.transformation_sample.set(json.dumps(data));e.tick(1)
  assert e.transformation_trial.last.use.complete
  frame=e.transformation_trial.use;e.tick(1)
  assert e.transformation_trial.use is frame and len(e.transformation_trial.queue.records)==1
  p.widgets[route].invoke();e.tick(1)
  assert e.transformation_trial.last is None and len(e.transformation_trial.queue.records)==1
  e.transformation_example();e.tick(1);assert len(e.transformation_trial.queue.records)==2
  with tempfile.TemporaryDirectory() as directory:
   path=Path(directory)/'ts.json';app.profiles.save(path,app.values,app.lists)
   restored,_=app.profiles.load_document(path)
   assert all(restored[k]==app.values[k] for k in TRANSFORMATION_INPUTS)
  e.reset();e.transformation_example();data=json.loads(e.transformation_sample.get())
  data['settings']['parser_route']='exception_unresolved';e.transformation_sample.set(json.dumps(data));e.tick(1)
  assert len(e.transformation_trial.last.settings.stores)==2 and e.transformation_trial.last.use is None
  e.transformation_sample.set('{bad');e.tick(1);assert e.transformation_trial.last is None
  assert 'Periyodik kullanım doğrulandı: False' in e.output.get('1.0','end')
 finally:
  app.values.clear();app.values.update(old_values);e.transformation_sample.set(old_sample);e.inputs['hp'].set(old_hp)
  e.case.set(old_case);e.reset();p.form.set(old_form);p.render()
 print('Transformation UI passed: four real panel controls ->bounded source producer ->explicit helper ->38byte own queue; parser exception prefix, gate/clock gap, full actor DWORD, no duplicate, stale snapshot rejection, queue seed preservation and profile roundtrip; periodic/native/live remain unverified')

if __name__=='__main__':
 import tkinter as tk
 from app import Application
 root=tk.Tk();root.withdraw()
 try:check_transformation_ui(Application(root))
 finally:root.destroy()
