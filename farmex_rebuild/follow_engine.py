"""Reached0040e550 follow tail and own panel projection; no game actions."""
from dataclasses import dataclass,field,replace
from types import MappingProxyType
from source_unicode import UnicodeEqualityObservation,plan_unicode_equality,utf16_key

ROOT='frmMain/MainTab/SheetGenel/GroupBox12/'
FOLLOW_PANEL_INPUTS=tuple(ROOT+n for n in ('chFollow','rdFollowPartyLeader','txtFollowNick'))
DISTANCE_THRESHOLD_BITS=0x40a00000 # binary32 5.0, literal0040e7a4
MANUAL_Y_ADD_BITS=0x40800000 # binary32 4.0, literal0040e7a8

def raw(v,bits=32,optional=False):
    if optional and v is None:return
    if type(v) is not int or not 0<=v<1<<bits:raise ValueError('Raw follow source value required')

@dataclass(frozen=True)
class FollowConfiguration:
    enabled_byte:int
    mode_dword:int
    nickname:str
    def __post_init__(self):
        raw(self.enabled_byte,8);raw(self.mode_dword);utf16_key(self.nickname)

def compile_follow_panel(values):
    enabled=values.get(FOLLOW_PANEL_INPUTS[0]);leader=values.get(FOLLOW_PANEL_INPUTS[1]);name=values.get(FOLLOW_PANEL_INPUTS[2])
    if type(enabled) is not bool or type(leader) is not bool:raise ValueError('Known follow checkboxes required')
    utf16_key(name)
    # Source does not read the manual radio; leader false writes mode2.
    return FollowConfiguration(int(enabled),1 if leader else 2,name)

@dataclass(frozen=True)
class FollowState:
    initialized_byte:int=0
    previous_name:object=None
    cached_id_dword:int=0
    def __post_init__(self):
        raw(self.initialized_byte,8);raw(self.cached_id_dword)
        if self.previous_name is not None:utf16_key(self.previous_name)

@dataclass(frozen=True)
class FollowObservation:
    entry_reached:object=None
    second_mode_dword:object=None
    party_count_dword:object=None
    leader_id_word:object=None
    pointer_dword:object=None
    name_id_dword:object=None
    initialized_previous_name:object=None
    empty_equal:object=None
    previous_equal:object=None
    coordinate_offsets:tuple=()
    coordinate_bits:tuple=()
    distance_status_word:object=None
    manual_y_after_add_bits:object=None
    helper_returns:object=field(default_factory=dict)
    def __post_init__(self):
        if self.entry_reached is not None and type(self.entry_reached) is not bool:raise ValueError('Explicit reached-follow entry required')
        for v in (self.second_mode_dword,self.party_count_dword,self.pointer_dword,self.name_id_dword,self.manual_y_after_add_bits):raw(v,optional=True)
        raw(self.leader_id_word,16,True);raw(self.distance_status_word,16,True)
        if self.initialized_previous_name is not None:utf16_key(self.initialized_previous_name)
        for e in (self.empty_equal,self.previous_equal):
            if e is not None and not isinstance(e,UnicodeEqualityObservation):raise ValueError('Typed Unicode comparison required')
        for seq in (self.coordinate_offsets,self.coordinate_bits):
            if type(seq) is not tuple or len(seq)>2:raise ValueError('Two ordered coordinate observations required')
            for v in seq:raw(v,optional=True)
        if any(type(v) is not bool for v in self.helper_returns.values()):raise ValueError('Separate follow helper returns required')
        object.__setattr__(self,'helper_returns',MappingProxyType(dict(self.helper_returns)))

@dataclass(frozen=True)
class FollowPlan:
    complete:bool
    status:str
    state:FollowState
    steps:tuple=()
    equality_plans:tuple=()
    movement:object=None
    missing:str=''
    native_execution_verified:bool=False

def plan_follow_tail(c,state,o):
    if not isinstance(c,FollowConfiguration) or not isinstance(state,FollowState) or not isinstance(o,FollowObservation):raise ValueError('Typed follow configuration/state/observations required')
    steps=[];equalities=[];movement=None
    class Missing(Exception):pass
    def result(ok,status,missing=''):
        return FollowPlan(ok,status,state,tuple(steps),tuple(equalities),movement,missing)
    def need(v,label):
        if v is None:raise Missing(label)
        return v
    def normal(name):
        steps.append(('normal_return',name))
        if o.helper_returns.get(name) is not True:raise Missing(name+' normal return')
    def eq(sample,left,right,label):
        if sample is None:raise Missing(label+' comparison')
        if sample.use_owned_text_model:
            if sample.left_text is not None and utf16_key(sample.left_text)!=utf16_key(left):raise ValueError('Follow comparison left text mismatch')
            if sample.right_text is not None and utf16_key(sample.right_text)!=utf16_key(right):raise ValueError('Follow comparison right text mismatch')
        p=plan_unicode_equality(sample);equalities.append(p)
        if not p.complete:raise Missing(label+': '+p.missing)
        return p.al!=0
    try:
        if o.entry_reached is not True:raise Missing('earlier caller reached0040e550')
        steps.append(('read_field',0x1e8,c.enabled_byte))
        if c.enabled_byte==0:return result(True,'disabled')
        steps.append(('read_field',0x1ec,c.mode_dword))
        manual=c.mode_dword!=1
        if not manual:
            steps.append(('004645e4',));normal('party_count')
            count=need(o.party_count_dword,'party count DWORD')
            if count==0 or count&0x80000000:return result(True,'no_positive_party_count')
            target=need(o.leader_id_word,'leader ID WORD');steps.append(('MOVZX_leader_id',target))
        else:
            mode=need(o.second_mode_dword,'second mode DWORD');steps.append(('read_field',0x1ec,mode))
            if mode!=2:return result(True,'other_mode')
            if state.initialized_byte==0:
                normal('initialize_previous_name')
                previous=need(o.initialized_previous_name,'initialized previous Unicode name')
                state=replace(state,initialized_byte=1,previous_name=previous)
                steps.append(('global_write_plan',0x50888a,1))
            empty=eq(o.empty_equal,c.nickname,'','empty name')
            normal('empty_temporary_cleanup')
            if empty:return result(True,'empty_name')
            previous=need(state.previous_name,'previous Unicode name')
            same=eq(o.previous_equal,c.nickname,previous,'previous name')
            if not same:
                normal('copy_previous_name')
                state=replace(state,previous_name=c.nickname,cached_id_dword=0)
                steps.append(('global_write_plan',0x553c30,0))
            if state.cached_id_dword==0:
                steps.append(('004656cc',c.nickname));normal('name_lookup')
                target=need(o.name_id_dword,'name lookup ID DWORD')
                state=replace(state,cached_id_dword=target);steps.append(('global_write_plan',0x553c30,target))
            if state.cached_id_dword==0:return result(True,'name_not_found')
            target=state.cached_id_dword
        steps.append(('00464a10',target));normal('entity_lookup')
        pointer=need(o.pointer_dword,'entity pointer DWORD')
        if pointer==0:
            if manual:
                state=replace(state,cached_id_dword=0);steps.append(('global_write_plan',0x553c30,0))
            return result(True,'entity_not_found')
        coordinates=[]
        for index,label in enumerate(('coord_x','coord_y')):
            offset=need(o.coordinate_offsets[index] if index<len(o.coordinate_offsets) else None,label+' offset DWORD')
            steps.append(('0045ddb8',(pointer+offset)&0xffffffff));normal(label)
            coordinates.append(need(o.coordinate_bits[index] if index<len(o.coordinate_bits) else None,label+' post-FSTP float bits'))
        steps.append(('00460548',coordinates[0],coordinates[1]));normal('distance')
        status=need(o.distance_status_word,'post-FUCOMPP status WORD');steps.append(('TEST_AH_45',status,DISTANCE_THRESHOLD_BITS))
        if status&0x4500:return result(True,'distance_gate_skipped')
        x,y=coordinates
        if manual:
            adjusted=need(o.manual_y_after_add_bits,'manual Y post-FADD/FSTP float bits')
            steps.append(('manual_y_add_observed',y,MANUAL_Y_ADD_BITS,adjusted));y=adjusted
        movement=(x,y);steps.append(('004646b4',x,y));normal('movement')
        return result(True,'movement_span_returned')
    except Missing as e:return result(False,'needs_observation',str(e))
