"""Panel -> bounded TS producer -> explicitly reached helper -> owned queue."""
import hashlib,json
from dataclasses import dataclass,replace
from action_queue import QueueState
from transformation import (TRANSFORMATION_INPUTS,compile_transformation,
 TransformationFrame,TransformationSelectionSamples,TransformationUseSamples)
from transformation_settings import TransformationSettingsFrame,TransformationSettingsObservation

def transformation_snapshot(values):
 result=tuple(values.get(k) for k in TRANSFORMATION_INPUTS)
 enabled,wait,route,index=result
 if type(enabled) is not bool or type(route) is not bool or type(wait) is not str:
  raise ValueError('Transformation panel flags/text required')
 if type(index) is not int or not -(1<<31)<=index<1<<31:raise ValueError('Signed combo index required')
 return result

def snapshot_digest(snapshot):return hashlib.sha256(json.dumps(snapshot,ensure_ascii=True,separators=(',',':')).encode('ascii')).hexdigest()
def obj(data,key):
 value=data.get(key,{})
 if type(value) is not dict:raise ValueError('Transformation '+key+' must be an object')
 return value

def advance_settings(frame,snapshot,data):
 enabled,wait,route,index=snapshot;o=TransformationSettingsObservation();capture=obj(data,'settings')
 for _ in range(32):
  p=frame.advance(o)
  if p.complete or p.needed[0]=='unmodeled':return p
  kind,label=p.needed
  if kind=='entry':
   entry=capture.get('entry_reached',False)
   if type(entry) is not bool:raise ValueError('Explicit settings entry flag required')
   if not entry:return p
   o=replace(o,entry_reached=True)
  elif kind=='normal':
   fields=obj(capture,'normal_returns')
   if label in fields and type(fields[label]) is not bool:raise ValueError('Separate helper normal receipt must be boolean')
   if fields.get(label) is not True:return p
   o=replace(o,normal_returns={**o.normal_returns,label:True})
  elif kind=='value':
   derived={'enabled_eax':int(enabled),'route_eax':int(route),'combo_eax':index&0xffffffff}
   fields=obj(capture,'values')
   if label in derived:
    value=derived[label]
    if label in fields and (type(fields[label]) is not int or fields[label]!=value):
     raise ValueError('Panel-derived Transformation getter cannot be overridden')
   else:
    if label not in fields:return p
    value=fields[label]
   o=replace(o,values={**o.values,label:value})
  elif kind=='text':
   if 'wait_text' in capture and capture['wait_text']!=wait:raise ValueError('Parser text must match panel')
   o=replace(o,wait_text=wait)
  elif kind=='route':
   if 'parser_route' not in capture:return p
   o=replace(o,parser_route=capture['parser_route'])
  else:return p
 raise ValueError('Transformation settings reached-field budget exceeded')

@dataclass(frozen=True)
class TransformationTrialPlan:
 settings:object
 use:object=None
 queue:object=None
 explicit_helper_entry:bool=False
 periodic_consumer_verified:bool=False
 native_execution_verified:bool=False
 live_compatibility_verified:bool=False

class TransformationTrial:
 def __init__(self,reader):self.reader=reader;self.reset()
 def reset(self):
  self.snapshot=None;self.settings=None;self.use=None;self.queue=QueueState();self.last=None
 def step(self,text):
  self.last=None
  if self.reader is None:raise ValueError('Transformation panel reader required')
  values,_=self.reader();snapshot=transformation_snapshot(values)
  if snapshot!=self.snapshot:
   if self.use is not None:self.queue=self.use.queue
   self.snapshot=snapshot;self.settings=TransformationSettingsFrame();self.use=None
  try:data=json.loads(text)
  except (TypeError,ValueError) as error:raise ValueError('Transformation observations must be a JSON object') from error
  if type(data) is not dict:raise ValueError('Transformation observations must be a JSON object')
  if 'panel_snapshot_sha256' in data and data['panel_snapshot_sha256']!=snapshot_digest(snapshot):
   raise ValueError('Panel değişti; Transformation örneğini yeniden doldurun')
  settings=advance_settings(self.settings,snapshot,data)
  if not settings.complete:
   self.last=TransformationTrialPlan(settings,queue=self.queue);return self.last
  reached=data.get('helper_entry_reached',False)
  if type(reached) is not bool:raise ValueError('Explicit helper entry flag required')
  if self.use is None and not reached:
   self.last=TransformationTrialPlan(settings,queue=self.queue);return self.last
  if self.use is None:self.use=TransformationFrame(settings.selected_skill,self.queue)
  capture=obj(data,'use');selection=obj(capture,'selection')
  def sequence(data,key):
   value=data.get(key,[])
   if type(value) not in (list,tuple):raise ValueError('Transformation '+key+' must be an array')
   return tuple(value)
  o=TransformationUseSamples(TransformationSelectionSamples(sequence(selection,'test_returns'),sequence(selection,'test_eax')),
   capture.get('actor_returned'),capture.get('actor_dword'),sequence(capture,'copy_returns'),
   capture.get('queue_gate'),capture.get('queue_tick'),capture.get('cast_returned'))
  use=self.use.advance(o);self.queue=self.use.queue
  self.last=TransformationTrialPlan(settings,use,self.queue,True);return self.last

def example_transformation_sample(snapshot):
 compile_transformation(dict(zip(TRANSFORMATION_INPUTS,snapshot)))
 # This lexical subset is an own synthetic example policy, not native StrToInt.
 # Obtain the parser capture from the original seconds, not the wrapped product.
 parser=int(snapshot[1].strip())&0xffffffff
 return json.dumps(dict(panel_snapshot_sha256=snapshot_digest(snapshot),synthetic_example=True,
  settings=dict(entry_reached=True,parser_route='normal',values=dict(parser_eax=parser),
   normal_returns={k:True for k in ('enabled','text_init','wait_text','parser','wait_cleanup','route','combo')}),
  helper_entry_reached=True,use=dict(selection=dict(test_returns=[True],test_eax=[1]),
   actor_returned=True,actor_dword=0x12345678,copy_returns=[True]*3,queue_gate=1,queue_tick=100,cast_returned=True)),ensure_ascii=False)

def describe_transformation_trial(trial):
 p=trial.last
 if p is None:return 'Geçerli Transformation sonucu yok'
 return {'ayar_öneki_tamam':p.settings.complete,'ayar_eksiği':p.settings.missing,
  'beceri_id':p.settings.selected_skill,'bekleme_ms':p.settings.milliseconds_dword,
  'açık_yardımcı_çağrısı':p.explicit_helper_entry,'çağrı_tamam':None if p.use is None else p.use.complete,
  'çağrı_eksiği':None if p.use is None else p.use.missing,'yerel_kayıt':len(p.queue.records),
  'Periyodik kullanım doğrulandı':False,'Oyunda kullanım doğrulandı':False}
