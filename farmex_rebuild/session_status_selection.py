"""004f9fda..004fa097 normal selector and owned ratio/wire composition."""
from dataclasses import dataclass,field
from types import MappingProxyType
from source_math64 import session_ratio
from session_status_wire import FIELDS,SessionStatusPrepared,build_session_status_wire

LABELS={'exclusive_byte','mode0','mode1','mode2','mode3','special_initial_byte',
        'connection_eax','bot_byte','secondary_byte','special_fresh_byte'}

@dataclass(frozen=True)
class SessionSelectionObservation:
    values:object=field(default_factory=dict)
    normal_returns:object=field(default_factory=dict)
    entry_observed:bool=False
    def __post_init__(self):
        values=dict(self.values);normals=dict(self.normal_returns)
        if type(self.entry_observed) is not bool:raise ValueError('Explicit source entry flag required')
        if set(values)-LABELS:raise ValueError('Unknown selector observation')
        for key,value in values.items():
            if type(value) is not int or not 0<=value<(256 if key.endswith('_byte') else 1<<32):
                raise ValueError('Raw source BYTE/DWORD required')
        if set(normals)-{'connection'} or any(type(v) is not bool for v in normals.values()):
            raise ValueError('Separate connection-helper normal receipt required')
        object.__setattr__(self,'values',MappingProxyType(values))
        object.__setattr__(self,'normal_returns',MappingProxyType(normals))

@dataclass(frozen=True)
class SessionSelectionPlan:
    complete:bool
    fields:object
    reads:tuple=()
    calls:tuple=()
    missing:str=''
    needed:object=None
    helper_effects_verified:bool=False
    native_execution_verified:bool=False

class _Wait(Exception):
    def __init__(self,kind,label):self.needed=(kind,label);super().__init__(label+' '+kind)

def select_session_fields(o):
    if not isinstance(o,SessionSelectionObservation):raise ValueError('Typed source selector observations required')
    fields={};reads=[];calls=[]
    def result(error=None):
        return SessionSelectionPlan(error is None,MappingProxyType(dict(fields)),tuple(reads),tuple(calls),
            '' if error is None else str(error),None if error is None else error.needed)
    def value(label):
        if label not in o.values:raise _Wait('value',label)
        return o.values[label]
    def read(label,address):
        reads.append((address,1 if label.endswith('_byte') else 4,label));return value(label)
    try:
        if not o.entry_observed:raise _Wait('entry','004f9fda')
        fields['exclusive_byte']=int(read('exclusive_byte',0x561f6f)!=0)
        fields['mode_byte']=255
        for i in range(4):
            if read('mode%d'%i,0x561f58)==i:
                fields['mode_byte']=i+1;break
        # This initial source read is required even though each later branch
        # overwrites the tentative status. It must not be removed as dead input.
        status=0x35 if read('special_initial_byte',0x56209c)!=0 else 255
        calls.append(('00462738',(),'connection'))
        if o.normal_returns.get('connection') is not True:raise _Wait('normal','connection')
        connection=value('connection_eax')
        if connection!=1:
            status=0x33 if read('special_fresh_byte',0x56209c)!=0 else 10
        elif read('bot_byte',0x561f60)==0:
            status=0x35 if read('special_fresh_byte',0x56209c)!=0 else 9
        elif read('secondary_byte',0x561f6c)!=0:
            status=1
        else:
            status=0x34 if read('special_fresh_byte',0x56209c)!=0 else 2
        fields['status_byte']=status
        return result()
    except _Wait as error:return result(error)

class SessionSelectionFrame:
    def __init__(self):self.observation=SessionSelectionObservation();self.final=None
    def advance(self,incoming):
        if not isinstance(incoming,SessionSelectionObservation):raise ValueError('Typed source selector observations required')
        if self.final is not None:return self.final
        for _ in range(20):
            p=select_session_fields(self.observation)
            if p.complete:self.final=p;return p
            kind,label=p.needed;values=dict(self.observation.values);normals=dict(self.observation.normal_returns)
            entry=self.observation.entry_observed
            if kind=='entry' and incoming.entry_observed:entry=True
            elif kind=='value' and label in incoming.values:values[label]=incoming.values[label]
            elif kind=='normal' and incoming.normal_returns.get(label) is True:normals[label]=True
            else:return p
            self.observation=SessionSelectionObservation(values,normals,entry)
        raise AssertionError('Selector exceeds known source read/receipt count')

@dataclass(frozen=True)
class SessionSourceWirePlan:
    complete:bool
    ratio:object
    selection:object=None
    wire:object=None
    missing:str=''
    full_builder_verified:bool=False
    native_execution_verified:bool=False
    live_compatibility_verified:bool=False

class SessionSourceWireFrame:
    """One invocation's stable getter/name captures plus fresh selector receipts.

    Ratio math precedes selection. Selector entry is explicit because earlier
    getters remain opaque. Every normal selector branch reaches serialization;
    this entry is derived rather than requesting a redundant observation.
    """
    def __init__(self,values_without_derived,serialized_name,*,numerator,denominator):
        values=dict(values_without_derived)
        derived={'ratio_division_eax','exclusive_byte','mode_byte','status_byte'}
        if set(values)!=set(FIELDS)-derived:raise ValueError('Exactly the remaining prepared getter/name fields required')
        # Validate the immutable capture shapes without claiming source entry.
        SessionStatusPrepared(dict(values,**dict.fromkeys(derived,0)),serialized_name)
        self.values=MappingProxyType(values);self.name=serialized_name
        self.ratio=session_ratio(numerator,denominator);self.selector=SessionSelectionFrame()
        self.final=None
    def advance(self,observation,*,transform_length_word=None):
        if not isinstance(observation,SessionSelectionObservation):
            raise ValueError('Typed selector observations required')
        if self.final is not None:return self.final
        if not self.ratio.complete:
            return SessionSourceWirePlan(False,self.ratio,missing='Source ratio divide fault; selector not reached')
        selection=self.selector.advance(observation)
        if not selection.complete:return SessionSourceWirePlan(False,self.ratio,selection,missing=selection.missing)
        values=dict(self.values);values.update(selection.fields)
        values['ratio_division_eax']=self.ratio.division.eax
        wire=build_session_status_wire(SessionStatusPrepared(values,self.name),
            entry_observed=True,transform_length_word=transform_length_word)
        plan=SessionSourceWirePlan(wire.complete,self.ratio,selection,wire,wire.missing)
        if plan.complete:self.final=plan
        return plan
