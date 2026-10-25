"""Own panel settings/activation trial. No main worker or game IO is executed."""
import json
from dataclasses import dataclass,replace
from monster_stone import MS_SETTING_INPUTS,MS_ENABLE_INPUT,MSFrame,MSObservation,compile_ms_settings
from bot_switch import BotSwitchObservation

MS_PANEL_INPUTS=MS_SETTING_INPUTS+(MS_ENABLE_INPUT,)

@dataclass(frozen=True)
class MSPanelTrialResult:
 settings:object
 activation:object
 applied_ui_updates:tuple=()
 native_execution_verified:bool=False
 live_compatibility_verified:bool=False
 main_worker_executed:bool=False

def advance_ms_activation_sample(frame,text,enabled):
 try:data=json.loads(text)
 except (ValueError,TypeError) as error:raise ValueError('MS observations must be a JSON object') from error
 if type(data) is not dict:raise ValueError('MS observations must be a JSON object')
 if type(enabled) is not bool:raise ValueError('MS panel boolean required')
 o=MSObservation({'enabled_eax':int(enabled)},{'enabled':True})
 seen=set()
 for _ in range(20):
  p=frame.advance(o)
  if p.complete:return p
  kind,label=p.needed
  if (kind,label) in seen:return p
  seen.add((kind,label))
  if (kind=='child' or label=='bot_start') and 'bot_start' in data and o.bot_start_inputs is None:
   child=data['bot_start']
   if type(child) is not dict or set(child)-{'values','normal_returns'}:raise ValueError('Known bot_start values/normal_returns required')
   o=replace(o,bot_start_inputs=BotSwitchObservation(child.get('values',{}),child.get('normal_returns',{})))
   seen.discard((kind,label));continue
  if kind!='normal':return p
  returns=data.get('normal_returns',{})
  if type(returns) is not dict:raise ValueError('MS normal_returns must be an object')
  if label not in returns:return p
  v=returns[label]
  if type(v) is not bool:raise ValueError('MS normal return must be boolean: '+label)
  if v is not True:return p
  o=replace(o,normal_returns={**o.normal_returns,label:True})
 raise ValueError('MS activation sample budget exceeded')

def example_ms_activation():
 return json.dumps({'normal_returns':{'wallhack_setter':True,'bot_start':True,'activation_return':True}})

def describe_ms_trial(result):
 mode=result.settings.mode_after
 label={0:'Boss',1:'Tüm moblar (kaynakta kapalı seçenek)'}.get(mode,'Önceki seçim belirsiz')
 names={'wallhack_setter':'WallHack işaretleme dönüşü','bot_start':'Başlatma dönüşü',
  'activation_return':'Etkinleştirme tamamlanma dönüşü'}
 waiting=''
 if result.activation.needed:
  kind,step=result.activation.needed
  waiting='Başlatma alt modeli' if kind=='child' else names.get(step,step)
 return {'Seçim':label,'Taş bitince alarm':bool(result.settings.stores[-1][2]),
  'Yerel etkinleştirme adımları': 'Tamamlandı' if result.activation.complete else 'Gözlem bekliyor',
  'Beklenen gözlem':waiting,'Oyun işleyicisi çalıştırıldı':False}

class MonsterStoneTrial:
 def __init__(self,configuration_reader,configuration_writer=None):
  self.reader=configuration_reader;self.writer=configuration_writer;self.reset()
 def reset(self):
  self.mode=0 #Source startup mode0, used only as own initial state.
  self.key=None;self.frame=None;self.settings=None;self.last=None;self.applied=set()
 def step(self,text):
  self.last=None
  if self.reader is None:raise ValueError('MS trial needs panel configuration reader')
  values,_=self.reader();enabled=values.get(MS_ENABLE_INPUT)
  if type(enabled) is not bool:raise ValueError('MS enable checkbox boolean required')
  settings=compile_ms_settings(values,previous_mode=self.mode)
  key=(settings.mode_after,settings.stores,enabled)
  if self.frame is None or key!=self.key:
   self.frame=MSFrame(activation=True);self.key=key;self.applied=set();self.settings=settings
  self.settings=settings
  self.mode=settings.mode_after
  plan=advance_ms_activation_sample(self.frame,text,enabled)
  pending=dict(update for update in plan.ui_updates if update not in self.applied)
  if pending and self.writer is not None:
   self.writer(pending);self.applied.update(pending.items())
  self.last=MSPanelTrialResult(self.settings,plan,tuple(sorted(self.applied)))
  return self.last
