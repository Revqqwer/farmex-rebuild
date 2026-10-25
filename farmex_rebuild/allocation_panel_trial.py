"""Stable own panel snapshot -> captured allocation producer; no native conversion."""
import json,re,hashlib
from dataclasses import dataclass,replace
from auto_allocation import AUTO_ALLOCATION_FLAGS,AutoAllocationFrame
from allocation_consumer_trial import advance_allocation_consumer_sample,describe_allocation_consumer
from allocation_producer import ALLOCATION_LISTS,AllocationProducerObservation,AllocationProducerFrame
from source_integer import SourceIntegerObservation

ALLOCATION_PANEL_INPUTS=AUTO_ALLOCATION_FLAGS+tuple(ALLOCATION_LISTS.values())

@dataclass(frozen=True)
class AllocationPanelRow:
 caption:str
 subitems:tuple

@dataclass(frozen=True)
class AllocationPanelSnapshot:
 flags:tuple
 stat_rows:tuple
 skill_rows:tuple
 def rows(self,domain):return self.stat_rows if domain=='stat' else self.skill_rows

def compile_allocation_panel(values,lists):
 flags=tuple(values.get(path) for path in AUTO_ALLOCATION_FLAGS)
 if any(type(v) is not bool for v in flags):raise ValueError('Stat/skill checkbox booleans required')
 groups=[]
 for path in ALLOCATION_LISTS.values():
  rows=lists.get(path)
  if type(rows) not in (tuple,list):raise ValueError('Stat/skill panel list required')
  group=[]
  for row in rows:
   if type(row) is not dict or type(row.get('caption')) is not str or type(row.get('subitems')) not in (tuple,list) or any(type(v) is not str for v in row['subitems']):raise ValueError('Known panel caption/subitems required')
   group.append(AllocationPanelRow(row['caption'],tuple(row['subitems'])))
  groups.append(tuple(group))
 return AllocationPanelSnapshot(flags,*groups)

def _object(data,key):
 value=data.get(key,{})
 if type(value) is not dict:raise ValueError('Allocation '+key+' must be an object')
 return value

def snapshot_digest(snapshot):
 data={'flags':snapshot.flags,'stat':[(r.caption,r.subitems) for r in snapshot.stat_rows],
  'skill':[(r.caption,r.subitems) for r in snapshot.skill_rows]}
 return hashlib.sha256(json.dumps(data,ensure_ascii=True,separators=(',',':')).encode('ascii')).hexdigest()

def advance_allocation_panel_sample(frame,snapshot,text):
 try:data=json.loads(text)
 except (ValueError,TypeError) as error:raise ValueError('Allocation observations must be a JSON object') from error
 if type(data) is not dict:raise ValueError('Allocation observations must be a JSON object')
 if 'panel_snapshot_sha256' in data and data['panel_snapshot_sha256']!=snapshot_digest(snapshot):
  raise ValueError('Panel değişti; sentetik örneği yeniden doldurun')
 o=AllocationProducerObservation();seen=set()
 for _ in range(32768):
  p=frame.advance(o)
  if p.complete:return p
  kind,label=p.needed;marker=(kind,label)
  if marker in seen:return p
  seen.add(marker)
  if kind=='entry':
   #Own trial enters this bounded producer explicitly; not a source event/scheduler proof.
   o=replace(o,entry_reached=True)
  elif kind=='normal':
   if label in ('stat_enabled','skill_enabled') or label.endswith(('.count','.name_get','.caption_get','.threshold_get')):
    o=replace(o,normal_returns={**o.normal_returns,label:True}) #Own stable getter adapter.
   else:
    returns=_object(data,'normal_returns')
    if label not in returns:return p
    v=returns[label]
    if type(v) is not bool:raise ValueError('Allocation normal return must be boolean: '+label)
    if v is not True:return p
    o=replace(o,normal_returns={**o.normal_returns,label:True})
  elif kind=='value':
   if label in ('stat_enabled_eax','skill_enabled_eax'):v=int(snapshot.flags[0 if label.startswith('stat') else 1])
   elif label.endswith('.count_eax'):v=len(snapshot.rows('stat' if label.startswith('stat') else 'skill'))
   else:
    values=_object(data,'values')
    if label not in values:return p
    v=values[label]
   o=replace(o,values={**o.values,label:v})
  elif kind=='text':
   m=re.fullmatch(r'(stat|skill)([0-9]+)\.(name|caption|threshold)',label)
   if m is None:raise ValueError('Unknown allocation panel text')
   domain,index,field=m.groups();row=snapshot.rows(domain)[int(index)]
   if field=='caption':v=row.caption
   else:
    column=0 if field=='name' else 1
    if len(row.subitems)<=column:raise ValueError('Reached allocation row lacks subitem '+str(column))
    v=row.subitems[column]
   o=replace(o,texts={**o.texts,label:v})
  elif kind=='name':
   names=_object(data,'name_bytes_hex')
   if label not in names:return p
   if type(names[label]) is not str:raise ValueError('Captured allocation ANSI hex required')
   try:v=bytes.fromhex(names[label])
   except ValueError as error:raise ValueError('Invalid allocation ANSI hex') from error
   o=replace(o,names={**o.names,label:v})
  elif kind=='integer':
   captures=_object(data,'integer_inputs')
   if label not in captures:return p
   if type(captures[label]) is not dict:raise ValueError('Typed allocation integer receipt object required')
   try:v=SourceIntegerObservation(**captures[label])
   except TypeError as error:raise ValueError('Unknown allocation integer field') from error
   o=replace(o,integer_inputs={**o.integer_inputs,label:v})
  else:return p
 raise ValueError('Allocation panel reached-field budget exceeded')

def example_allocation_sample(snapshot):
 data={'panel_snapshot_sha256':snapshot_digest(snapshot),'normal_returns':{'stat_clear':True,'skill_clear':True},'values':{},'name_bytes_hex':{},'integer_inputs':{}}
 for domain in ('stat','skill'):
  for index,row in enumerate(snapshot.rows(domain)):
   if len(row.subitems)<2:raise ValueError('Example needs name and threshold columns')
   pre='%s%d.'%(domain,index)
   try:name=row.subitems[0].encode('ascii')
   except UnicodeEncodeError as error:raise ValueError('Synthetic example supports ASCII names; supply captured ANSI bytes for other text') from error
   data['name_bytes_hex'][pre+'name']=name.hex()
   for suffix,source in (('action_integer',row.caption),('threshold_integer',row.subitems[1])):
    if not re.fullmatch(r'[+-]?[0-9]+',source.strip()):raise ValueError('Synthetic example requires strict decimal row integers')
    value=int(source.strip())
    if not -(1<<63)<=value<1<<63:raise ValueError('Synthetic example integer must fit signed64')
    data['integer_inputs'][pre+suffix]=dict(text_copy_returned=True,route='normal',parser_returned=True,parser_qword=value&0xffffffffffffffff,cleanup_returned=True)
   data['values'].update({pre+'size_eax':index,pre+'capacity_eax':0}) #Explicit synthetic reallocation span, no native pointers.
   for suffix in ('row_init','name_conversion_cleanup','action_integer','caption_cleanup','threshold_integer','threshold_cleanup','size','capacity','reallocate','row_cleanup'):
    data['normal_returns'][pre+suffix]=True
 return json.dumps(data,ensure_ascii=False)

def describe_allocation_panel(plan,consumer=None):
 return {'Üretilen stat satırı':len(plan.stat_rows),'Üretilen skill satırı':len(plan.skill_rows),
  'Yerel ayar üretimi':'Tamamlandı' if plan.complete else 'Gözlem bekliyor',
  'Beklenen gözlem':plan.missing,'Oyunda puan dağıtıldı':False,**describe_allocation_consumer(consumer)}

class AllocationPanelTrial:
 def __init__(self,configuration_reader):self.reader=configuration_reader;self.reset()
 def reset(self):self.snapshot=None;self.frame=None;self.last=None;self.consumer_frame=None;self.consumer_last=None
 def step(self,text):
  self.last=None;self.consumer_last=None
  if self.reader is None:raise ValueError('Allocation trial needs a panel reader')
  values,lists=self.reader();snapshot=compile_allocation_panel(values,lists)
  if snapshot!=self.snapshot:
   self.snapshot=snapshot;self.frame=AllocationProducerFrame();self.consumer_frame=AutoAllocationFrame()
  self.last=advance_allocation_panel_sample(self.frame,snapshot,text)
  if self.last.complete:
   data=json.loads(text)
   if 'consumer' in data:
    self.consumer_last=advance_allocation_consumer_sample(self.consumer_frame,self.last,data['consumer'])
  return self.last
