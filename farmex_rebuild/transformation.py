"""Transformation config/004c8498 selector/004c8388 local frame; no game IO."""
import re
from dataclasses import dataclass,field
from types import MappingProxyType
from action_queue import QueueState,enqueue

ROOT='frmMain/MainTab/SheetGenel/GroupBox39/'
TRANSFORMATION_INPUTS=tuple(ROOT+n for n in ('chTransformation','txttsbekle','chototsnoslot','cmbTransformationSkill'))
SKILLS=(0x72d26,0x72c04,0x72c18,0x72c22,0x72c36,0x72c40,0x72c4a,0x72c86,0x72c72,
        0x72c74,0x73460,0x72cb8,0x72cba,0x72cea,0x72cf4,0x72d12,0x72d04,0x72d08)
TEMPLATE=bytes.fromhex('3106'+'00'*36)

def raw(v,optional=False):
    if optional and v is None:return
    if type(v) is not int or not 0<=v<1<<32:raise ValueError('Raw transformation DWORD required')
def normal_type(v):
    if v is not None and type(v) is not bool:raise ValueError('Separate transformation normal return required')

@dataclass(frozen=True)
class TransformationConfiguration:
    fields:object
    combo_index:int
    parser_scope:str='strict_signed_decimal32_subset'
    def __post_init__(self):object.__setattr__(self,'fields',MappingProxyType(dict(self.fields)))

def compile_transformation(values):
    enabled=values.get(TRANSFORMATION_INPUTS[0]);wait=values.get(TRANSFORMATION_INPUTS[1])
    no_route=values.get(TRANSFORMATION_INPUTS[2]);index=values.get(TRANSFORMATION_INPUTS[3])
    if type(enabled) is not bool or type(no_route) is not bool:raise ValueError('Known transformation checkboxes required')
    if type(index) is not int or not -(1<<31)<=index<1<<31:raise ValueError('Signed source combo index required')
    if type(wait) is not str or not re.fullmatch(r'[+-]?[0-9]+',wait.strip()):raise ValueError('Strict signed decimal wait required')
    seconds=int(wait.strip())
    if not -(1<<31)<=seconds<1<<31:raise ValueError('Signed DWORD wait required')
    skill=SKILLS[index] if 0<=index<18 else SKILLS[0]
    return TransformationConfiguration({0x20:int(enabled),0x21:1,0x28:(seconds*1000)&0xffffffff,
                                         0x22:int(no_route),0x24:skill},index)

@dataclass(frozen=True)
class TransformationSelectionSamples:
    test_returns:tuple=()
    test_eax:tuple=()
    def __post_init__(self):
        if type(self.test_returns) is not tuple or type(self.test_eax) is not tuple or max(len(self.test_returns),len(self.test_eax))>2:raise ValueError('Two ordered transformation checks required')
        for v in self.test_returns:normal_type(v)
        for v in self.test_eax:raw(v,True)

@dataclass(frozen=True)
class TransformationSelectionPlan:
    complete:bool
    selected_skill:object=None
    checks:tuple=()
    missing:str=''
    native_execution_verified:bool=False

def select_transformation(skill,o):
    raw(skill)
    if not isinstance(o,TransformationSelectionSamples):raise ValueError('Typed transformation checks required')
    checks=[]
    for i,candidate in enumerate((skill,(skill+2000)&0xffffffff)):
        checks.append(('00464268',candidate))
        if i>=len(o.test_returns) or o.test_returns[i] is not True:
            return TransformationSelectionPlan(False,checks=tuple(checks),missing='skill check%d normal return'%i)
        eax=o.test_eax[i] if i<len(o.test_eax) else None
        if eax is None:return TransformationSelectionPlan(False,checks=tuple(checks),missing='skill check%d EAX'%i)
        if eax&255:return TransformationSelectionPlan(True,candidate,tuple(checks))
    return TransformationSelectionPlan(True,checks=tuple(checks))

@dataclass(frozen=True)
class TransformationUseSamples:
    selection:TransformationSelectionSamples=field(default_factory=TransformationSelectionSamples)
    actor_returned:object=None
    actor_dword:object=None
    copy_returns:tuple=()
    queue_gate:object=None
    queue_tick:object=None
    cast_returned:object=None
    def __post_init__(self):
        if not isinstance(self.selection,TransformationSelectionSamples):raise ValueError('Typed transformation selection required')
        normal_type(self.actor_returned);normal_type(self.cast_returned)
        for v in (self.actor_dword,self.queue_gate,self.queue_tick):raw(v,True)
        if type(self.copy_returns) is not tuple or len(self.copy_returns)>3:raise ValueError('Three ordered memcpy returns required')
        for v in self.copy_returns:normal_type(v)

@dataclass(frozen=True)
class TransformationUsePlan:
    complete:bool
    status:str
    selection:object=None
    payload:object=None
    queue_decision:object=None
    missing:str=''
    native_execution_verified:bool=False

class TransformationFrame:
    """One explicit helper invocation, cached local prefix across observation gaps."""
    def __init__(self,skill,queue=None):
        raw(skill);self.skill=skill;self.queue=QueueState() if queue is None else queue
        if not isinstance(self.queue,QueueState):raise ValueError('Own local queue required')
        self.selection=None;self.actor=None;self.copies=0;self.payload=None;self.queue_decision=None;self.finished=False
        self.queue_gate=None
        self.check_returned=[None,None];self.check_eax=[None,None]
    def advance(self,o):
        if not isinstance(o,TransformationUseSamples):raise ValueError('Typed transformation use observations required')
        def result(ok,status,missing=''):
            return TransformationUsePlan(ok,status,self.selection,self.payload,self.queue_decision,missing)
        if self.finished:return result(True,'already_finished')
        if self.selection is None or not self.selection.complete:
            for i in range(2):
                if self.check_returned[i] is not True and i<len(o.selection.test_returns) and o.selection.test_returns[i] is True:self.check_returned[i]=True
                if self.check_returned[i] is True and self.check_eax[i] is None and i<len(o.selection.test_eax):self.check_eax[i]=o.selection.test_eax[i]
                self.selection=select_transformation(self.skill,TransformationSelectionSamples(tuple(self.check_returned),tuple(self.check_eax)))
                if self.selection.complete:break
                if self.check_returned[i] is not True or self.check_eax[i] is None:return result(False,'needs_observation',self.selection.missing)
        chosen=self.selection.selected_skill
        if chosen is None:self.finished=True;return result(True,'no_skill_selected')
        if self.actor is None:
            if o.actor_returned is not True:return result(False,'needs_observation','00462650 actor normal return')
            if o.actor_dword is None:return result(False,'needs_observation','fresh actor DWORD')
            self.actor=o.actor_dword
        while self.copies<3:
            if self.copies>=len(o.copy_returns) or o.copy_returns[self.copies] is not True:
                return result(False,'needs_observation','memcpy%d normal return'%self.copies)
            self.copies+=1
        if self.payload is None:
            data=bytearray(TEMPLATE);data[2:6]=chosen.to_bytes(4,'little')
            actor=self.actor.to_bytes(4,'little');data[6:10]=actor;data[10:14]=actor;self.payload=bytes(data)
        if self.queue_decision is None:
            # 004c771c tests the full EAX once, before the GetTickCount call.
            # A later observation cannot change this already-consumed branch.
            if self.queue_gate is None:self.queue_gate=o.queue_gate
            decision=enqueue(self.queue,self.payload,38,0,self.queue_gate,o.queue_tick)
            if decision.state is None:return result(False,'needs_observation',decision.missing)
            self.queue_decision=decision;self.queue=decision.state
        if o.cast_returned is not True:return result(False,'needs_observation','004c8388 cast normal return')
        self.finished=True;return result(True,'cast_span_returned')

class DirectSkillFrame(TransformationFrame):
    """004c8388 entry directly: no004c8498 checker or+2000 fallback."""
    def __init__(self,skill,queue=None):
        super().__init__(skill,queue)
        self.selection=TransformationSelectionPlan(True,skill,())
