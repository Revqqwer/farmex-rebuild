"""0045dca8 captured read-string helper; owned byte effects, no memory IO.

Guard, memcpy prefix/return, constructor value, assignment prefix/return and
cleanup are separate observations. A destination prefix survives later gaps.
"""
from dataclasses import dataclass,field
from collections.abc import Mapping


def dword(value):
    if type(value) is not int or not 0<=value<=0xffffffff:raise ValueError('Raw DWORD required')
    return value


@dataclass(frozen=True)
class QuestReadStringObservation:
    bad_read_eax:object=None
    copied_bytes:object=None
    constructor_ansi:object=None
    normal_returns:object=field(default_factory=dict)


@dataclass(frozen=True)
class QuestReadStringPlan:
    complete:bool
    status:str
    address_dword:int
    count_dword:int
    destination_ansi:bytes
    destination_assigned:bool
    temporary_ansi:object=None
    local_buffer:object=None
    needed:object=None
    calls:tuple=()
    branch:object=None
    return_target:object=None
    native_execution_verified:bool=False
    live_compatibility_verified:bool=False


class QuestReadStringFrame:
    def __init__(self,address,count,initial_ansi=b'',*,use_owned_cstring_model=False):
        self.address=dword(address);self.count=dword(count)
        if type(initial_ansi) is not bytes:raise ValueError('Immutable own destination snapshot required')
        if type(use_owned_cstring_model) is not bool:raise ValueError('Explicit own C-string policy required')
        self.destination=initial_ansi;self.assigned=False;self.owned=use_owned_cstring_model
        self.phase='entry';self.cache={};self.normal=set();self.called=set();self.calls=[]
        self.buffer=None;self.temporary=None;self.branch=None;self.final=None

    def out(self,status,needed=None,complete=False):
        p=QuestReadStringPlan(complete,status,self.address,self.count,self.destination,self.assigned,
            self.temporary,self.buffer,needed,tuple(self.calls),self.branch,
            'owned_destination' if complete else None)
        if complete:self.final=p
        return p

    def advance(self,observation=None):
        if self.final is not None:return self.final
        o=QuestReadStringObservation() if observation is None else observation
        if not isinstance(o,QuestReadStringObservation) or not isinstance(o.normal_returns,Mapping):
            raise ValueError('Typed sparse string-read observations required')
        class Missing(Exception):pass
        def request(label,helper,args=()):
            if label not in self.called:self.called.add(label);self.calls.append((label,helper,args))
        def receipt(label):
            if label not in self.normal:
                v=o.normal_returns.get(label)
                if v is not None and type(v) is not bool:raise ValueError('Explicit normal span receipt required')
                if v is not True:raise Missing(('normal',label))
                self.normal.add(label)
        def normal(label,helper,args=()):request(label,helper,args);receipt(label)
        try:
            while True:
                if self.phase=='entry':
                    normal('entry','source prologue/SEH setup span');self.phase='guard'
                elif self.phase=='guard':
                    normal('guard','KERNEL32!IsBadReadPtr',(self.address,self.count))
                    if 'bad' not in self.cache:
                        if o.bad_read_eax is None:raise Missing(('value','bad_read_eax'))
                        self.cache['bad']=dword(o.bad_read_eax)
                    self.branch='bad_read' if self.cache['bad'] else 'readable'
                    if self.cache['bad']:self.phase='constructor'
                    elif self.count>512:return self.out('unresolved_source_stack_overflow')
                    else:self.buffer=b'\0'*512;self.phase='copy'
                elif self.phase=='copy':
                    request('copy','CC32260MT!_memcpy',('owned_buffer',self.address,self.count))
                    if not self.cache.get('copied'):
                        if 'captured' not in self.cache:
                            raw=o.copied_bytes
                            if self.count==0:raw=b''
                            if raw is None:raise Missing(('bytes',self.count))
                            if type(raw) is not bytes:raise ValueError('Immutable captured copy bytes required')
                            if len(raw)<self.count:raise Missing(('bytes',self.count))
                            self.cache['captured']=raw[:self.count]
                        receipt('copy_prefix')
                        self.buffer=self.cache['captured']+b'\0'*(512-self.count)
                        self.cache['copied']=True
                    receipt('copy');self.phase='constructor'
                elif self.phase=='constructor':
                    arg='empty_literal_00523469' if self.branch=='bad_read' else 'owned_buffer'
                    request('constructor','004040bc',(arg,))
                    if self.temporary is None:
                        if o.constructor_ansi is not None:
                            if type(o.constructor_ansi) is not bytes:raise ValueError('Immutable captured constructor ANSI value required')
                            self.temporary=o.constructor_ansi
                        elif self.owned:
                            if self.branch=='bad_read':self.temporary=b''
                            else:
                                end=self.buffer.find(b'\0')
                                if end<0:return self.out('unresolved_unterminated_source_buffer')
                                self.temporary=self.buffer[:end]
                        else:raise Missing(('value','constructor_ansi'))
                    receipt('constructor');self.phase='assign'
                elif self.phase=='assign':
                    request('assign','managed ANSI assignment span',('owned_destination','owned_temporary'))
                    if not self.assigned:
                        receipt('assign_prefix');self.destination=self.temporary;self.assigned=True
                    receipt('assign');self.phase='cleanup'
                elif self.phase=='cleanup':
                    normal('cleanup','004040f8',('owned_temporary',2))
                    self.temporary=None;self.phase='epilogue'
                elif self.phase=='epilogue':
                    normal('epilogue','source destination-return/SEH restore span')
                    return self.out('string_ready',complete=True)
                else:raise AssertionError('Unknown string-read phase')
        except Missing as error:return self.out('needs_observation',error.args[0])
