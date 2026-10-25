"""Reached-only004d6668 candidate filters, ending before NPC/name construction.

No game lookup/read, display row insertion, native helper or refresh UI action.
Repeated reads of one address have different labels and remain independent.
"""
from dataclasses import dataclass,field
from collections.abc import Mapping

ZONE_MATCHES=(('Moradon',21),('Luferson',1),('EMC',2),('Karus Eslant',11),('Human Eslant',12))


@dataclass(frozen=True)
class QuestZonePlan:
    complete:bool
    code:object=None
    needed:object=None
    compared:tuple=()


def resolve_quest_zone(matches):
    if not isinstance(matches,Mapping):raise ValueError('Explicit source equality outcomes required')
    compared=[]
    for name,code in ZONE_MATCHES:
        compared.append(name);value=matches.get(name)
        if value is None:return QuestZonePlan(False,needed=name,compared=tuple(compared))
        if type(value) is not bool:raise ValueError('Normalized source equality boolean required')
        if value:return QuestZonePlan(True,code,compared=tuple(compared))
    return QuestZonePlan(True,0,compared=tuple(compared))


@dataclass(frozen=True)
class QuestCandidateObservation:
    values:object=field(default_factory=dict)
    normal_returns:object=field(default_factory=dict)


@dataclass(frozen=True)
class QuestCandidatePlan:
    complete:bool
    status:str
    eligible:bool=False
    needed:object=None
    source_index:int=0
    pointer:object=None
    reads:tuple=()
    calls:tuple=()
    native_execution_verified:bool=False
    live_compatibility_verified:bool=False


class QuestCandidateFrame:
    def __init__(self,source_index,zone_code):
        if type(source_index) is not int or not 0<=source_index<=30000:raise ValueError('Source candidate index0..30000 required')
        if type(zone_code) is not int or not 1<=zone_code<=255:raise ValueError('Known nonzero mapped zone BYTE required')
        self.index=source_index;self.zone=zone_code;self.phase=0;self.cache={};self.normal=set();self.called=set()
        self.pointer=None;self.reads=[];self.calls=[];self.final=None
    def out(self,status,complete=False,eligible=False,needed=None):
        p=QuestCandidatePlan(complete,status,eligible,needed,self.index,self.pointer,tuple(self.reads),tuple(self.calls))
        if complete:self.final=p
        return p
    def advance(self,o=None):
        if self.final is not None:return self.final
        o=QuestCandidateObservation() if o is None else o
        if not isinstance(o,QuestCandidateObservation) or not isinstance(o.values,Mapping) or not isinstance(o.normal_returns,Mapping):
            raise ValueError('Typed sparse candidate observations required')
        class Missing(Exception):pass
        def take(label,helper,args,width=32,read_address=None):
            if label in self.cache:return self.cache[label]
            if label not in self.called:self.calls.append((helper,args,label));self.called.add(label)
            if label not in self.normal:
                value=o.normal_returns.get(label)
                if value is not None and type(value) is not bool:raise ValueError('Explicit helper normal return required')
                if value is not True:raise Missing(('normal',label))
                self.normal.add(label)
            if label not in o.values:raise Missing(('value',label))
            value=o.values[label]
            if type(value) is not int or not 0<=value<1<<width:raise ValueError('Raw reached%d-bit value required'%width)
            self.cache[label]=value
            if read_address is not None:self.reads.append((read_address,width,label,value))
            return value
        def byte(label,offset):
            address=(self.pointer+offset)&0xffffffff
            return take(label,'0045dbdc',(address,),8,address)
        def signed(value):return value if value<0x80000000 else value-0x100000000
        try:
            while self.phase<18:
                p=self.phase
                if p==0:
                    self.pointer=take('lookup_eax','004d51c4',('owned_quest_context',self.index))
                    if self.pointer==0:return self.out('null_candidate',True)
                elif p==1:
                    if byte('zone',0x1b)!=self.zone:return self.out('zone_mismatch',True)
                elif p==2:
                    if byte('kind_not3',0x1a)==3:return self.out('kind3',True)
                elif p==3:
                    if byte('kind_not4',0x1a)==4:return self.out('kind4',True)
                elif p==4:
                    if byte('nation_gate',0x19)==3:self.phase=7;continue
                elif p==5:byte('nation_value',0x19)
                elif p==6:
                    if self.cache['nation_value']!=take('nation_eax','00462690',()):return self.out('nation_mismatch',True)
                elif p==7:
                    if byte('class_gate',0x18)==5:self.phase=10;continue
                elif p==8:byte('class_value',0x18)
                elif p==9:
                    if self.cache['class_value']!=(take('class_eax','004d4f60',('owned_quest_context',))&255):
                        return self.out('class_mismatch',True)
                elif p==10:
                    if byte('field24',0x24)!=4:return self.out('field24_not4',True)
                elif p==11:
                    if byte('field30',0x30)==0:return self.out('field30_zero',True)
                elif p==12:
                    if byte('minimum_nonzero',5)==0:return self.out('minimum_zero',True)
                elif p==13:
                    if byte('minimum_not100',5)==100:return self.out('minimum100',True)
                elif p==14:byte('minimum_value',5)
                elif p==15:
                    if self.cache['minimum_value']>signed(take('level_eax','00462670',())):return self.out('level_too_low',True)
                elif p==16:
                    address=(self.pointer+0x20)&0xffffffff
                    take('status_key','0045dc44',(address,),32,address)
                elif p==17:
                    if take('status_eax','004d5244',('owned_quest_context',self.cache['status_key']))&255==2:
                        return self.out('status2',True)
                self.phase+=1
            return self.out('eligible_for_name_stage',True,True)
        except Missing as error:return self.out('needs_observation',needed=error.args[0])
