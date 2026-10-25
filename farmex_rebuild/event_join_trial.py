"""Own stable panel ->bounded settings ->captured event worker and own queue."""
import hashlib,json,re
from dataclasses import replace
from action_queue import QueueState
from direct_chat_packets import QueueAttempt
from event_join import EVENT_FIELDS,EVENT_JOIN_INPUTS,compile_event_join,EventSettingsFrame,EventSettingsObservation,EventJoinFrame,EventJoinObservation
from event_packets import EventPacketObservation,EventPacketPlan
from event_target_fallback import EventFallbackObservation,EventFallbackPlan

def event_snapshot(values):return tuple(compile_event_join(values).items())
def event_snapshot_digest(snapshot):return hashlib.sha256(json.dumps(snapshot,separators=(',',':')).encode('ascii')).hexdigest()
def obj(data,key):
 v=data.get(key,{})
 if type(v) is not dict:raise ValueError('Event '+key+' must be an object')
 return v

def advance_event_sample(frame,snapshot,data):
 o=EventJoinObservation();seen=set();settings=dict(snapshot);offsets={key:offset for key,name,offset,slot in EVENT_FIELDS}
 packet_labels=('chaos_join','bdw_join','royale_join','target_prepare');enqueue_labels=('ft_enqueue','utc_enqueue','jr_enqueue0','jr_enqueue200')
 for _ in range(4096):
  p=frame.advance(o)
  if p.complete:return p
  kind,label=p.needed
  if kind=='normal' and label not in frame.frames:
   if label=='target_fallback' and 'fallback_child' in data:
    o=replace(o,fallback_child=EventFallbackObservation());continue
   if label in packet_labels and label in obj(data,'packet_children'):
    o=replace(o,packet_children={**o.packet_children,label:EventPacketObservation()});continue
   if label in enqueue_labels and label in obj(data,'enqueue_children'):
    o=replace(o,enqueue_children={**o.enqueue_children,label:QueueAttempt()});continue
  if kind=='child':
   child=dict(p.children)[label];inner_kind,inner_label=child.needed
   marker=(kind,label,inner_kind,inner_label)
   if marker in seen:return p
   seen.add(marker)
   if isinstance(child,EventFallbackPlan):
    capture=obj(data,'fallback_child');key='normal_returns' if inner_kind=='normal' else 'values';fields=obj(capture,key)
    if inner_label not in fields:return p
    previous=o.fallback_child or EventFallbackObservation()
    o=replace(o,fallback_child=replace(previous,**{key:{**getattr(previous,key),inner_label:fields[inner_label]}}));continue
   packet=isinstance(child,EventPacketPlan);group='packet_children' if packet else 'enqueue_children'
   captures=obj(data,group)
   if label not in captures:return p
   capture=captures[label]
   if type(capture) is not dict:raise ValueError('Event child must be an object')
   if packet:
    previous=o.packet_children.get(label,EventPacketObservation())
    if inner_kind in ('normal','value'):
     key='normal_returns' if inner_kind=='normal' else 'values';fields=obj(capture,key)
     if inner_label not in fields:return p
     updated=replace(previous,**{key:{**getattr(previous,key),inner_label:fields[inner_label]}})
    else:
     fields=obj(capture,'attempt');field={'connection gate':'gate','GetTickCount':'tick','enqueue normal return':'normal_returned'}[inner_label]
     if field not in fields:return p
     updated=replace(previous,attempt=replace(previous.attempt,**{field:fields[field]}))
    o=replace(o,packet_children={**o.packet_children,label:updated})
   else:
    field={'gate':'gate','tick':'tick','normal':'normal_returned'}[inner_kind]
    if field not in capture:return p
    previous=o.enqueue_children.get(label,QueueAttempt())
    o=replace(o,enqueue_children={**o.enqueue_children,label:replace(previous,**{field:capture[field]})})
   continue
  marker=(kind,label)
  if marker in seen:return p
  seen.add(marker)
  key='normal_returns' if kind=='normal' else 'values'
  flag=re.fullmatch(r'(?:first|second|priority)_(chaos|bdw|royale|ft|utc|jr)_byte',label) if kind=='value' else None
  if flag:v=settings[offsets[flag[1]]]
  else:
   fields=obj(data,key)
   if label not in fields:return p
   v=fields[label]
  o=replace(o,**{key:{**getattr(o,key),label:v}})
 raise ValueError('Own event reached-field budget exceeded')

def example_event_sample(snapshot):
 settings=dict(snapshot);first=any(settings[offset] for offset in (0x68,0x6d,0x6b))
 values=dict(first_tick_eax=100,first_low=0,first_high=0,first_post_tick_eax=101,
 second_tick_eax=101 if first else 201,second_low=101 if first else 0,second_high=0,
 target_first_eax=3001,target_second_eax=3001,target_third_eax=3001,nation_eax=1,second_post_tick_eax=202)
 normals={key:True for key in ('entry_setup','first_tick','first_post_tick','second_tick','second_post_tick','chaos_join','bdw_join','royale_join',
 'target_first','target_second','target_third','target_prepare','target_fallback','nation','ft_copy','utc_copy','jr_copy','ft_enqueue','utc_enqueue','jr_enqueue0','jr_enqueue200','return')}
 packet={'values':{'nation_eax':2},'normal_returns':{k:True for k in ('frame_setup','nation','copy','return')},'attempt':{'gate':1,'tick':110,'normal_returned':True}}
 packets={label:packet for label in ('chaos_join','bdw_join','royale_join')}
 packets['target_prepare']={'normal_returns':{k:True for k in ('frame_setup','template_copy','target_copy','return')},'attempt':{'gate':1,'tick':209,'normal_returned':True}}
 return json.dumps(dict(panel_snapshot_sha256=event_snapshot_digest(snapshot),values=values,normal_returns=normals,
 packet_children=packets,
 enqueue_children={label:dict(gate=1,tick=tick,normal_returned=True) for label,tick in (('ft_enqueue',210),('utc_enqueue',210),('jr_enqueue0',210),('jr_enqueue200',211))}))

def describe_event_trial(trial):
 p=trial.last
 return {'Yerel etkinlik akışı':'Tamamlandı' if p.complete else 'Gözlem bekliyor','Beklenen gözlem':p.missing,
  'Ayrıntılı alt model':len(p.children),'Yerel kuyruk kaydı':len(p.queue.records),'Oyunda katılım doğrulandı':False}

class EventJoinTrial:
 def __init__(self,configuration_reader):self.reader=configuration_reader;self.reset()
 def reset(self):self.snapshot=None;self.frame=None;self.settings=None;self.last=None
 def step(self,text):
  self.last=None
  if self.reader is None:raise ValueError('Event trial needs a panel reader')
  values,_=self.reader();snapshot=event_snapshot(values)
  if snapshot!=self.snapshot:
   queue=QueueState() if self.frame is None else self.frame.queue
   self.snapshot=snapshot;self.frame=EventJoinFrame(queue=queue)
   self.settings=EventSettingsFrame().advance(EventSettingsObservation(True,(True,)*6,tuple(v for offset,v in snapshot)))
  try:data=json.loads(text)
  except (TypeError,ValueError) as error:raise ValueError('Event observations must be a JSON object') from error
  if type(data) is not dict:raise ValueError('Event observations must be a JSON object')
  if 'panel_snapshot_sha256' in data and data['panel_snapshot_sha256']!=event_snapshot_digest(snapshot):raise ValueError('Panel değişti; etkinlik örneğini yeniden doldurun')
  self.last=advance_event_sample(self.frame,snapshot,data)
  return self.last
