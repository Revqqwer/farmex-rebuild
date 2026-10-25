"""Captured0040fc1c normal paths; plans only, never reads or acts on a game.

Every reached source field/global/helper return is an independent capture.
Configuration does not silently supply later reads. A frame freezes consumed
values/normal receipts while leaving future observations fresh.
"""
from dataclasses import dataclass,field,replace
from types import MappingProxyType

FOOD_IDS=(0x17385dd0,0x173884e0,0x1738abf0)

@dataclass(frozen=True)
class PetObservation:
    values:object=field(default_factory=dict)
    normal_returns:object=field(default_factory=dict)
    def __post_init__(self):
        values=dict(self.values);normals=dict(self.normal_returns)
        if any(type(v) is not int or not 0<=v<=0xffffffff for v in values.values()):
            raise ValueError('Raw Pet DWORD captures required')
        if any(type(v) is not bool for v in normals.values()):
            raise ValueError('Separate Pet helper normal-return receipts required')
        object.__setattr__(self,'values',MappingProxyType(values))
        object.__setattr__(self,'normal_returns',MappingProxyType(normals))

@dataclass(frozen=True)
class PetPlan:
    complete:bool
    status:str
    calls:tuple=()
    reads:tuple=()
    stores:tuple=()
    missing:str=''
    needed:object=None
    native_execution_verified:bool=False
    live_compatibility_verified:bool=False

class _Wait(Exception):
    def __init__(self,kind,key):self.needed=(kind,key);super().__init__(kind+': '+key)

def plan_pet(o,*,context=0x561f34):
    if not isinstance(o,PetObservation):raise ValueError('Typed Pet captures required')
    if type(context) is not int or not 0<=context<=0xffffffff:raise ValueError('Raw Pet context required')
    calls=[];reads=[];stores=[]
    def result(status,error=None):
        return PetPlan(error is None,status,tuple(calls),tuple(reads),tuple(stores),
                       '' if error is None else str(error),None if error is None else error.needed)
    def value(key,address=None,width=4):
        reads.append((key,address,width))
        if key not in o.values:raise _Wait('values',key)
        v=o.values[key]
        if v>=1<<(8*width):raise ValueError('Pet capture exceeds reached width: '+key)
        return v
    def call(key,target,args=(),returns_value=True):
        calls.append((key,target,args))
        if o.normal_returns.get(key) is not True:raise _Wait('normal_returns',key)
        return value(key+'_eax') if returns_value else None
    def field(key,offset,width=4):return value(key,(context+offset)&0xffffffff,width)
    def guarded(key,offset_slot,byte=False,fp=False):
        slot=value(key+'_root_slot',0x553e7c)
        root=call(key+'_root','0045dc44',(slot,))
        offset=value(key+'_offset',offset_slot)
        return call(key,'0045ddb8' if fp else '0045dbdc' if byte else '0045dc44',
                    ((root+offset)&0xffffffff,),not fp)
    def store(address,width,v):stores.append((address&0xffffffff,width,v))
    def signed(v):return v if v<0x80000000 else v-0x100000000
    try:
        if field('auto_initial',0x1a8,1)==0 and field('food_initial',0x1b0,1)==0:
            return result('disabled')
        if call('busy_vip','004fe3a0',(0x5690b8,))&255:return result('vip_busy')
        if call('busy_supply','0046fe90',(0x5690e0,))&255:return result('supply_busy')
        if guarded('state',0x55402c,byte=True)&255:return result('character_state_gate')
        guarded('float_gate',0x554030,fp=True)
        if (value('float_compare_status',width=2)>>8)&0x45==0:return result('character_float_gate')
        if call('pet_exists','00463274')&255==0:
            if field('auto_absent',0x1a8,1)==0:return result('absent_auto_disabled')
            if guarded('class',0x554034)==6:return result('class_six')
            if call('summon_item','00463924',(0x17329558,))&255==0:return result('summon_item_missing')
            if guarded('actor',0x554020)!=0:call('cancel_actor','00464714',returns_value=False)
            call('target_initial','00462630')
            # TEST EAX,EAX clears CF; the following JC cannot branch normally.
            if guarded('target_flag',0x55403c)!=0:
                target=call('target_fresh','00462630')
                call('clear_target','00465ef8',(target,0),False)
            if call('summon_ready','00464504',(0x7a195,))&255:return result('summon_blocked')
            store(context+0x4c,4,0x2904)
            now=call('summon_clock','005074f6');store(context+0x50,4,now)
            store(context+0x4a,1,1)
            actor_id=call('self_id','00462650')
            call('summon','00465640',(0x7a195,actor_id),False)
            return result('summon_returned')
        if field('auto_present',0x1a8,1)!=0:
            mode=call('pet_mode','00463284')
            if mode!=field('mode_compare',0x1ac):
                now=call('mode_clock','005074f6')
                if (now-value('mode_last',0x553c54))&0xffffffff>=1000:
                    desired=field('mode_send',0x1ac)
                    call('set_mode','004c7fe4',(0x561ef8,desired),False)
                    post=call('mode_post_clock','005074f6');store(0x553c54,4,post)
                    return result('mode_returned')
        if field('food_present',0x1b0,1)==0:return result('food_disabled')
        now=call('food_clock','005074f6')
        if (now-value('food_last',0x553c58))&0xffffffff<5000:return result('food_timer')
        hunger=call('hunger','00463228')&0xffff
        threshold=field('food_threshold',0x1b4)
        fed=False
        if hunger<=signed(threshold):
            for slot in range(14,42):
                item=call('food_item_%d'%slot,'004634a4',(slot,))
                if item in FOOD_IDS:
                    call('feed','00464ff8',(slot,),False);fed=True;break
        # Timestamp is written even if hunger is high or no matching item exists.
        post=call('food_post_clock','005074f6');store(0x553c58,4,post)
        return result('feed_returned' if fed else 'food_checked')
    except _Wait as error:return result('needs_observation',error)

class PetFrame:
    def __init__(self,*,context=0x561f34):
        self.context=context;self.observation=PetObservation();self.final=None
    def advance(self,incoming=None):
        if self.final is not None:return self.final
        incoming=PetObservation() if incoming is None else incoming
        if not isinstance(incoming,PetObservation):raise ValueError('Typed Pet capture required')
        for _ in range(512):
            p=plan_pet(self.observation,context=self.context)
            if p.complete:self.final=p;return p
            kind,key=p.needed;available=getattr(incoming,kind)
            if key not in available or kind=='normal_returns' and available[key] is not True:return p
            self.observation=replace(self.observation,**{kind:{**getattr(self.observation,kind),key:available[key]}})
        raise AssertionError('Pet capture budget exhausted')
