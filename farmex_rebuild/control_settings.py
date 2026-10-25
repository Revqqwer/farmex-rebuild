"""4581b9..4584af control settings producer and own captured consumer bridge."""
from dataclasses import dataclass
from protection_settings import ProtectionSettingsFrame,ProtectionSettingsObservation,plan_protection_settings,ProtectionSettingsPlan
from control_guards import ControlGuardConfiguration,ControlGuardObservation
from control_continuation import ControlContinuationObservation,replay_control_chain

OPS=(('flag',0x8a4,0xbd),('flag',0x8a8,0xbe),('flag',0x8a0,0xbf),
 ('flag',0x8ac,0xc0),('number64',0x8b0,0xc8,0),('flag',0x8c4,0xd0),
 ('number',0x8c8,0xd4,54),('flag',0x8b4,0xd8),('number',0x8b8,0xdc,0),
 ('number',0x8bc,0xe0,0),('number',0x8c0,0xe4,5),
 ('flag',0xbf0,0xe8),('flag',0xbf4,0xe9),('flag',0xbfc,0xea),('flag',0xc00,0xeb))
NAMES=('chZoneChangeBotStop','chTownRequestBotStop','chNPControl','chCoinControl',
 'txtCoinControlValue','chLevelKontrol','txtLevelKontrol','chGameCloseClock',
 'txtGameCloseHour','txtGameCloseMinute','txtPartyControlCount','chPartyCountBotStop',
 'chPartyCountAlarm','chPartyNotPriestBotStop','chPartyNotPriestAlarm')
CONTROL_SETTING_FIELDS=tuple((op[1],'frmMain/MainTab/SheetKontrol/GroupBox43/'+name) for op,name in zip(OPS,NAMES))
ControlSettingsObservation=ProtectionSettingsObservation

def plan_control_settings(o,*,context=0x562194,_child=None):
 return plan_protection_settings(o,context=context,_child=_child,_ops=OPS,
                                 _entry='004581b9',_exit=0x4584af,_prologue=False)

class ControlSettingsFrame(ProtectionSettingsFrame):
 _planner=staticmethod(plan_control_settings)
 def __init__(self,*,context=0x562194):super().__init__(context=context)

def control_configuration_from_settings(plan,*,context=0x562194):
 """Own completed settings projection, never a native fresh-read certificate."""
 if not isinstance(plan,ProtectionSettingsPlan) or not plan.complete or plan.next_address!=0x4584af:
  raise ValueError('Completed bounded control settings plan required')
 if type(context) is not int or not 0<=context<=0xffffffff:raise ValueError('Raw producer context required')
 expected=[((context+op[2]+delta)&0xffffffff,width) for op in OPS
           for delta,width in ([(0,1)] if op[0]=='flag' else [(0,4),(4,4)] if op[0]=='number64' else [(0,4)])]
 if [(a,w) for a,w,_ in plan.stores]!=expected:raise ValueError('Exact source settings store span required')
 fields={}
 for (address,width),(_,_,value) in zip(expected,plan.stores):
  if type(value) is not int or not 0<=value<1<<(width*8):raise ValueError('Raw settings store required')
  fields[(address-context)&0xffffffff]=value
 return ControlGuardConfiguration(fields,parser_scope='captured_source_integer_normal_or_catch_landing')

@dataclass(frozen=True)
class ControlSettingsConsumerPlan:
 complete:bool
 settings:object
 configuration:object=None
 consumer:object=None
 native_execution_verified:bool=False
 live_compatibility_verified:bool=False

def replay_control_settings_consumer(settings,entry,continuation,*,context=0x562194):
 """Explicit own snapshot bridge into existing NP/coin/level/clock/party plans."""
 if not isinstance(settings,ProtectionSettingsPlan):raise ValueError('Typed settings plan required')
 if not isinstance(entry,ControlGuardObservation) or not isinstance(continuation,ControlContinuationObservation):
  raise ValueError('Separate typed consumer observations required')
 if not settings.complete:return ControlSettingsConsumerPlan(False,settings)
 config=control_configuration_from_settings(settings,context=context)
 consumer=replay_control_chain(config,entry,config,continuation)
 return ControlSettingsConsumerPlan(consumer.complete,settings,config,consumer)
