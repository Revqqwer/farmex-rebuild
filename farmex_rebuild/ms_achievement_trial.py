"""Reached-only JSON adapter for own achievement event queue replay."""
import json
from dataclasses import replace
from ms_achievement import MSAchievementFrame,MSAchievementObservation,AchievementRequestObservation
from direct_chat_packets import QueueAttempt

def example_achievement_sample():
 return json.dumps({'requests':{str(i):{'normal_returns':{'frame_setup':True,'copy':True,'return':True},
  'attempt':{'gate':1,'tick':100+i,'normal_returned':True}} for i in range(11)},
  'caller_returns':{str(i):True for i in range(11)},'event_returned':True})

def advance_achievement_sample(frame,text):
 try:data=json.loads(text)
 except (ValueError,TypeError) as error:raise ValueError('Achievement observations must be a JSON object') from error
 if type(data) is not dict:raise ValueError('Achievement observations must be a JSON object')
 o=MSAchievementObservation();seen=set()
 for _ in range(160):
  p=frame.advance(o)
  if p.complete:return p
  kind,index=p.needed;key=(kind,index,p.missing)
  if key in seen:return p
  seen.add(key)
  if kind=='event_return':
   if 'event_returned' not in data:return p
   o=replace(o,event_returned=data['event_returned'])
  elif kind=='caller_return':
   returns=data.get('caller_returns',{})
   if type(returns) is not dict:raise ValueError('Achievement caller_returns must be an object')
   if str(index) not in returns:return p
   o=replace(o,caller_returns={**o.caller_returns,index:returns[str(index)]})
  elif kind=='request':
   requests=data.get('requests',{})
   if type(requests) is not dict:raise ValueError('Achievement requests must be an object')
   if str(index) not in requests:return p
   raw=requests[str(index)]
   if type(raw) is not dict:raise ValueError('Reached achievement request must be an object')
   current=o.requests.get(index,AchievementRequestObservation())
   normal={'frame_setup normal return':'frame_setup','copy normal return':'copy','helper return span':'return'}.get(p.missing)
   if normal is not None:
    returns=raw.get('normal_returns',{})
    if type(returns) is not dict:raise ValueError('Reached achievement normal_returns must be an object')
    if normal not in returns:return p
    current=replace(current,normal_returns={**current.normal_returns,normal:returns[normal]})
   else:
    field={'enqueue connection gate':'gate','enqueue GetTickCount':'tick','enqueue normal return':'normal_returned'}.get(p.missing)
    if field is None:return p
    attempt=raw.get('attempt',{})
    if type(attempt) is not dict:raise ValueError('Reached achievement attempt must be an object')
    if field not in attempt:return p
    current=replace(current,attempt=replace(current.attempt,**{field:attempt[field]}))
   o=replace(o,requests={**o.requests,index:current})
  else:return p
 raise ValueError('Achievement sample reached-field budget exceeded')

def describe_achievement_trial(plan):
 waiting=''
 if plan.needed:
  kind,index=plan.needed
  waiting='Olay tamamlanma dönüşü' if kind=='event_return' else '%d. istek %s'%(index+1,'alt modeli' if kind=='request' else 'dış dönüşü')
 return {'Yerel istek denemesi':len(plan.calls),'Dış dönüşü tamamlanan':len(plan.completed_invocations),
  'Yerel kuyruk kaydı':len(plan.queue.records),'Beklenen gözlem':waiting,
  'Sunucudan ödül kazanımı doğrulandı':False}

class AchievementTrial:
 def __init__(self):self.reset()
 def reset(self,queue=None):self.frame=MSAchievementFrame(queue);self.last=None
 def step(self,text):
  self.last=None;self.last=advance_achievement_sample(self.frame,text);return self.last
