"""Own flags/treeviews -> captured producer trial, never point allocation."""
import copy,json,tempfile
from pathlib import Path
from allocation_panel_trial import AUTO_ALLOCATION_FLAGS,ALLOCATION_LISTS

def check_allocation_panel_ui(app):
 e=app.engine_page;p=app.panel;old_values=dict(app.values);old_lists=copy.deepcopy(app.lists)
 old_case=e.case.get();old_form=p.form.get();old_sample=e.allocation_sample.get();old_hp=e.inputs['hp'].get()
 try:
  for path in AUTO_ALLOCATION_FLAGS:app.profiles.update(app.values,path,False)
  app.lists[ALLOCATION_LISTS['stat']]=[dict(caption='3',subitems=['STR','100'],checked=False)]
  app.lists[ALLOCATION_LISTS['skill']]=[dict(caption='1',subitems=['Attack','50'],checked=False)]
  p.form.set('frmMain');p.render();p.widgets[AUTO_ALLOCATION_FLAGS[0]].invoke();p.widgets[AUTO_ALLOCATION_FLAGS[1]].invoke()
  tree=p.widgets[ALLOCATION_LISTS['stat']];assert tree.item(tree.get_children()[0],'values')[1:] == ('STR','100')
  e.case.set('Stat/Skill Ayarları');e.reset();e.inputs['hp'].set('unrelated invalid HP');e.allocation_sample.set('{}');e.tick(1)
  assert not e.allocation_trial.last.complete and e.allocation_trial.last.stores[:2]==((0x5621b4,1,1),(0x5621b5,1,1))
  e.allocation_example();e.tick(1);assert e.allocation_trial.last.complete
  assert e.allocation_trial.last.stat_rows[0].action_dword==3 and e.allocation_trial.last.skill_rows[0].threshold_dword==50
  frame=e.allocation_trial.frame;e.tick(1);assert e.allocation_trial.frame is frame
  app.lists[ALLOCATION_LISTS['stat']][0]['subitems'][1]='120';p.render();e.tick(1)
  assert e.allocation_trial.last is None
  e.allocation_example();e.tick(1);assert e.allocation_trial.last.stat_rows[0].threshold_dword==120
  with tempfile.TemporaryDirectory() as directory:
   path=Path(directory)/'allocation.json';app.profiles.save(path,app.values,app.lists)
   restored_values,restored_lists=app.profiles.load_document(path)
   assert all(restored_values[k] for k in AUTO_ALLOCATION_FLAGS)
   assert restored_lists[ALLOCATION_LISTS['stat']][0]['caption']=='3' and restored_lists[ALLOCATION_LISTS['stat']][0]['subitems'][1]=='120'
  e.allocation_sample.set('{bad');e.tick(1);assert e.allocation_trial.last is None
  assert 'Oyunda puan dağıtıldı: False' in e.output.get('1.0','end')
  from test_allocation_consumer_trial import trial_data
  values,lists,data=trial_data()
  for path,value in values.items():app.profiles.update(app.values,path,value)
  app.lists.update(copy.deepcopy(lists));p.render();e.reset()
  child=data['consumer']['action_children']['stat0.action'];child['normal_returns']['callback']=False
  from test_allocation_queries import stat_sample
  from test_allocation_consumer_trial import observation_json
  query=observation_json(stat_sample());query['normal_returns']['argument_cleanup']=False
  data['consumer']['query_children']={'stat0.query':query}
  e.allocation_sample.set(json.dumps(data));e.tick(1)
  assert e.allocation_trial.last.complete and e.allocation_trial.consumer_last.needed==('child','stat0.query')
  assert e.allocation_trial.consumer_last.actions==()
  query['normal_returns']['argument_cleanup']=True
  e.allocation_sample.set(json.dumps(data));e.tick(1)
  assert e.allocation_trial.last.complete and e.allocation_trial.consumer_last.needed==('child','stat0.action')
  assert e.allocation_trial.consumer_last.stores==()
  child['normal_returns']['callback']=True;e.allocation_sample.set(json.dumps(data));e.tick(1)
  consumer=e.allocation_trial.consumer_last
  assert consumer.complete and consumer.actions==( ('stat',0,3), )
  assert dict(consumer.children)['stat0.action'].invocation==(0xabcdef12,0x8000,(1,0x76543210))
  assert dict(consumer.children)['stat0.query'].selected_field==b'STR'
  assert 'Dağıtım çağrı modeli: Tamamlandı' in e.output.get('1.0','end')
  e.allocation_sample.set('{bad');e.tick(1);assert e.allocation_trial.consumer_last is None
  print('Allocation consumer UI passed: actual panel snapshot ->producer ->captured consumer ->typed stat query/action, separate query cleanup and callback gaps, resume, argument identity and stale-result clearing; no game action')
 finally:
  app.values.clear();app.values.update(old_values);app.lists.clear();app.lists.update(old_lists)
  e.inputs['hp'].set(old_hp);e.allocation_sample.set(old_sample);e.case.set(old_case);e.reset();p.form.set(old_form);p.render()
 print('Allocation panel UI passed: two real flags/treeview rows, hidden caption/name/threshold mapping, default capture gaps, explicit example, cached invocation, stale-example rejection, fresh rows, profile roundtrip and bad-result clearing; no point/native/game effects')

if __name__=='__main__':
 import tkinter as tk
 from app import Application
 root=tk.Tk();root.withdraw()
 try:
  app=Application(root);check_allocation_panel_ui(app)
 finally:
  if 'app' in globals():app.connection_page.close()
  root.destroy()
