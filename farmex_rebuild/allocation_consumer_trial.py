"""Reached-only JSON adapter for explicit allocation consumer observations."""
import re
from dataclasses import replace
from auto_allocation import AutoAllocationObservation
from allocation_actions import AllocationActionObservation
from allocation_queries import AllocationQueryObservation

def object_field(data,key):
 v=data.get(key,{})
 if type(v) is not dict:raise ValueError('Allocation consumer '+key+' must be an object')
 return v

def advance_allocation_consumer_sample(frame,producer,data):
 if not producer.complete:raise ValueError('Complete bounded producer required before consumer trial')
 if type(data) is not dict:raise ValueError('Allocation consumer must be an object')
 o=AutoAllocationObservation();seen=set()
 for _ in range(32768):
  p=frame.advance(o)
  if p.complete:return p
  kind,label=p.needed
  if kind=='budget':return p
  match=re.fullmatch(r'(stat|skill)[0-9]+\.(action|query)',label)
  if kind in ('normal','child') and match:
   category=match[2];group=category+'_children'
   frames=frame.action_frames if category=='action' else frame.query_frames
   observation_type=AllocationActionObservation if category=='action' else AllocationQueryObservation
   if kind=='normal' and label not in frames:
    captures=object_field(data,group)
    if label in captures:
     o=replace(o,**{group:{**getattr(o,group),label:observation_type()}})
     continue
  if kind=='child':
   child=dict(p.children)[label];child_kind,child_label=child.needed
   marker=(kind,label,child_kind,child_label)
   if marker in seen:return p
   seen.add(marker)
   captures=object_field(data,group)
   if label not in captures:return p
   capture=captures[label]
   if type(capture) is not dict:raise ValueError('Allocation '+category+' child must be an object')
   key='values' if child_kind=='value' else 'normal_returns'
   fields=object_field(capture,key)
   if child_label not in fields:return p
   previous=getattr(o,group).get(label,observation_type())
   updated={**getattr(previous,key),child_label:fields[child_label]}
   child_o=replace(previous,**{key:updated})
   o=replace(o,**{group:{**getattr(o,group),label:child_o}})
   continue
  marker=(kind,label)
  if marker in seen:return p
  seen.add(marker)
  key='values' if kind=='value' else 'normal_returns'
  fields=object_field(data,key)
  if label not in fields:return p
  v=fields[label]
  if kind=='value':
   if label in ('stat_enabled_byte','skill_enabled_byte'):
    offset=0x5621b4 if label.startswith('stat') else 0x5621b5
    expected=next(value for at,width,value in producer.stores if at==offset and width==1)
    if type(v) is not int or v!=expected:raise ValueError('Consumer flag differs from produced panel flag: '+label)
   match=re.fullmatch(r'(stat|skill)([0-9]+)\.(threshold|action_argument|query_argument)',label)
   if match:
    domain,index,field=match.groups();rows=getattr(producer,domain+'_rows');index=int(index)
    if index>=len(rows):raise ValueError('Reached consumer row is outside produced panel rows')
    expected=getattr(rows[index],'threshold_dword' if field=='threshold' else 'action_dword')
    if type(v) is not int or v!=expected:raise ValueError('Consumer row differs from produced panel row: '+label)
  o=replace(o,**{key:{**getattr(o,key),label:v}})
 raise ValueError('Allocation consumer reached-field budget exceeded')

def describe_allocation_consumer(plan):
 if plan is None:return {'Dağıtım çağrı modeli':'Gözlem verilmedi'}
 return {'Dağıtım çağrı modeli':'Tamamlandı' if plan.complete else 'Gözlem bekliyor',
  'Dağıtım beklenen gözlem':plan.missing,'Hazırlanan eylem sayısı':len(plan.actions),
  'Ayrıntılı eylem modeli sayısı':sum(label.endswith('.action') for label,child in plan.children),
  'Ayrıntılı sorgu modeli sayısı':sum(label.endswith('.query') for label,child in plan.children),'Oyunda puan dağıtıldı':False}
