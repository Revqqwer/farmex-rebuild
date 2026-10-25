"""Quest refresh string/record continuation, before vector insertion or UI.

Read/helper values and normal spans are explicit captures. Managed string
ownership, native ABI/SEH and vector allocation are not executed or certified.
"""
from dataclasses import dataclass,field
from collections.abc import Mapping
from quest_candidate import QuestCandidatePlan,QuestCandidateFrame

EXCLUDED_NPC=b'[Familiar Tamer] Kate'
LAYOUTS={'display':(0x20,0x10,50),'script':(0x48,0x38,15),'npc':(0x14,4,15)}


def raw(value):
    if value is not None and (type(value) is not int or not 0<=value<=0xffffffff):raise ValueError('Raw DWORD required')


@dataclass(frozen=True)
class QuestStringObservation:
    storage_dword:object=None
    pointer_dword:object=None
    bad_read_dword:object=None
    captured:object=None
    helper_returned:object=None


@dataclass(frozen=True)
class QuestStringPlan:
    complete:bool
    status:str
    ansi_bytes:object=None
    storage_dword:object=None
    copy_address:object=None
    copy_count:object=None
    needed:object=None
    reads:tuple=()
    native_execution_verified:bool=False


class QuestStringFrame:
    def __init__(self,kind,base_dword):
        if kind not in LAYOUTS:raise ValueError('Known Quest string layout required')
        raw(base_dword)
        if base_dword is None:raise ValueError('Known source base DWORD required')
        self.kind=kind;self.base=base_dword;self.phase='storage';self.cache={};self.reads=[];self.final=None
    def out(self,status,complete=False,data=None,needed=None):
        p=QuestStringPlan(complete,status,data,self.cache.get('storage'),self.cache.get('address'),self.cache.get('count'),needed,tuple(self.reads))
        if complete:self.final=p
        return p
    def advance(self,o=None):
        if self.final is not None:return self.final
        o=QuestStringObservation() if o is None else o
        if not isinstance(o,QuestStringObservation):raise ValueError('Typed Quest string capture required')
        storage_offset,data_offset,small_count=LAYOUTS[self.kind]
        class Missing(Exception):pass
        def value(name,key):
            if key not in self.cache:
                v=getattr(o,name);raw(v)
                if v is None:raise Missing((name,))
                self.cache[key]=v
            return self.cache[key]
        try:
            while True:
                if self.phase=='storage':
                    storage=value('storage_dword','storage')
                    self.reads.append(((self.base+storage_offset)&0xffffffff,32,'storage',storage))
                    signed=storage if storage<0x80000000 else storage-0x100000000
                    self.cache['count']=storage if signed>=16 else small_count
                    if signed>=16:self.phase='pointer'
                    else:self.cache['address']=(self.base+data_offset)&0xffffffff;self.phase='guard'
                elif self.phase=='pointer':
                    pointer=value('pointer_dword','pointer');self.cache['address']=pointer
                    self.reads.append(((self.base+data_offset)&0xffffffff,32,'pointer',pointer));self.phase='guard'
                elif self.phase=='guard':
                    bad=value('bad_read_dword','bad')
                    if bad:self.cache['bytes']=b'';self.phase='return'
                    elif self.cache['count']>512:return self.out('unresolved_source_stack_overflow')
                    else:self.phase='copy'
                elif self.phase=='copy':
                    if 'captured' not in self.cache:
                        data=o.captured
                        if data is None:raise Missing(('captured_bytes',self.cache['count']))
                        if type(data) is not bytes:raise ValueError('Immutable captured source bytes required')
                        if len(data)<self.cache['count']:raise Missing(('captured_bytes',self.cache['count']))
                        self.cache['captured']=data[:self.cache['count']]
                    local=self.cache['captured']+b'\0'*(512-self.cache['count'])
                    at=local.find(b'\0')
                    if at<0:return self.out('unresolved_unterminated_source_buffer')
                    self.cache['bytes']=local[:at];self.phase='return'
                elif self.phase=='return':
                    normal=o.helper_returned
                    if normal is not None and type(normal) is not bool:raise ValueError('Explicit string helper normal return required')
                    if normal is not True:raise Missing(('helper_returned',))
                    return self.out('string_ready',True,self.cache['bytes'])
                else:raise ValueError('Unknown Quest string phase')
        except Missing as error:return self.out('needs_observation',needed=error.args[0])


@dataclass(frozen=True)
class QuestPreparedObservation:
    candidate:object=None
    record:object=None


@dataclass(frozen=True)
class QuestPreparedPlan:
    complete:bool
    status:str
    eligible_for_append:bool=False
    record:object=None
    candidate_plan:object=None
    record_plan:object=None
    needed:object=None
    native_execution_verified:bool=False
    live_compatibility_verified:bool=False


class QuestPreparedFrame:
    def __init__(self,source_index,zone_code):
        self.candidate=QuestCandidateFrame(source_index,zone_code);self.record=None;self.final=None
    def advance(self,o=None):
        if self.final is not None:return self.final
        o=QuestPreparedObservation() if o is None else o
        if not isinstance(o,QuestPreparedObservation):raise ValueError('Typed prepared candidate captures required')
        candidate=self.candidate.advance(o.candidate)
        if not candidate.complete:return QuestPreparedPlan(False,'needs_candidate',candidate_plan=candidate,needed=candidate.needed)
        if not candidate.eligible:
            self.final=QuestPreparedPlan(True,'candidate_rejected',candidate_plan=candidate);return self.final
        if self.record is None:self.record=QuestRecordFrame(candidate)
        record=self.record.advance(o.record)
        p=QuestPreparedPlan(record.complete,record.status,record.eligible_for_append,record.record,candidate,record,record.needed)
        if p.complete:self.final=p
        return p


@dataclass(frozen=True)
class QuestRecord:
    source_index:int
    data_pointer_dword:int
    script_bytes:bytes
    script_storage_dword:int
    minimum_dword:int
    display_bytes:bytes
    npc_bytes:bytes
    def fields(self):
        return {0:self.source_index,4:self.data_pointer_dword,8:self.script_bytes,0xc:self.script_storage_dword,
                0x10:self.minimum_dword,0x14:self.display_bytes,0x18:self.npc_bytes}


@dataclass(frozen=True)
class QuestRecordObservation:
    values:object=field(default_factory=dict)
    normal_returns:object=field(default_factory=dict)
    strings:object=field(default_factory=dict)


@dataclass(frozen=True)
class QuestRecordPlan:
    complete:bool
    status:str
    eligible_for_append:bool=False
    record:object=None
    needed:object=None
    reads:tuple=()
    calls:tuple=()
    native_execution_verified:bool=False
    live_compatibility_verified:bool=False
    string_reads:tuple=()


class QuestRecordFrame:
    def __init__(self,candidate):
        if not isinstance(candidate,QuestCandidatePlan) or not candidate.complete or not candidate.eligible:
            raise ValueError('Completed eligible candidate required')
        raw(candidate.pointer)
        if not candidate.pointer or type(candidate.source_index) is not int or not 0<=candidate.source_index<=30000:
            raise ValueError('Valid reached source record required')
        self.candidate=candidate;self.phase='display_key';self.cache={};self.normal=set();self.called=set()
        self.reads=[];self.calls=[];self.strings={};self.record=None;self.final=None
    def out(self,status,complete=False,eligible=False,needed=None):
        p=QuestRecordPlan(complete,status,eligible,self.record,needed,tuple(self.reads),tuple(self.calls),
            string_reads=tuple((kind,tuple(frame.reads)) for kind,frame in self.strings.items()))
        if complete:self.final=p
        return p
    def advance(self,o=None):
        if self.final is not None:return self.final
        o=QuestRecordObservation() if o is None else o
        if not isinstance(o,QuestRecordObservation) or any(not isinstance(v,Mapping) for v in (o.values,o.normal_returns,o.strings)):
            raise ValueError('Typed sparse record captures required')
        class Missing(Exception):pass
        def normal(label,helper,args=()):
            if label not in self.called:self.calls.append((helper,args,label));self.called.add(label)
            if label in self.normal:return
            v=o.normal_returns.get(label)
            if v is not None and type(v) is not bool:raise ValueError('Explicit record helper normal return required')
            if v is not True:raise Missing(('normal',label))
            self.normal.add(label)
        def value(label,helper,args=(),width=32,address=None):
            if label in self.cache:return self.cache[label]
            normal(label,helper,args)
            if label not in o.values:raise Missing(('value',label))
            v=o.values[label]
            if type(v) is not int or not 0<=v<1<<width:raise ValueError('Raw reached record value required')
            self.cache[label]=v
            if address is not None:self.reads.append((address,width,label,v))
            return v
        def read(label,offset,width=32):
            address=(self.candidate.pointer+offset)&0xffffffff
            return value(label,'0045dbdc' if width==8 else '0045dc44',(address,),width,address)
        def string(kind,base):
            if kind not in self.strings:self.strings[kind]=QuestStringFrame(kind,base)
            p=self.strings[kind].advance(o.strings.get(kind))
            if not p.complete:raise Missing(('string',kind,p.status,p.needed))
            return p
        try:
            while True:
                if self.phase=='display_key':read('display_key',0x50);self.phase='display_lookup'
                elif self.phase=='display_lookup':
                    value('display_lookup_eax','004d51f0',('owned_quest_context',self.cache['display_key']));self.phase='display'
                elif self.phase=='display':
                    p=string('display',self.cache['display_lookup_eax']);self.cache['display_bytes']=p.ansi_bytes
                    normal('display_string_span','opaque_string_assignment_cleanup_span');self.phase='script'
                elif self.phase=='script':
                    p=string('script',self.candidate.pointer);self.cache['script_bytes']=p.ansi_bytes;self.cache['script_storage']=p.storage_dword
                    normal('script_string_span','opaque_string_assignment_cleanup_span');self.phase='minimum'
                elif self.phase=='minimum':read('fresh_minimum',5,8);self.phase='display_assignment'
                elif self.phase=='display_assignment':normal('display_assignment_returned','005050e4');self.phase='npc_key'
                elif self.phase=='npc_key':read('npc_key',0x1c);self.phase='npc_lookup'
                elif self.phase=='npc_lookup':
                    if 'npc_helper' not in self.called:
                        self.calls.append(('004d52c0',('owned_quest_context',self.cache['npc_key']),'npc_helper'));self.called.add('npc_helper')
                    pointer=value('npc_lookup_eax','004d526c',('owned_quest_context',self.cache['npc_key']))
                    if pointer==0:self.cache['npc_bytes']=b'';self.phase='npc_return'
                    else:self.phase='npc'
                elif self.phase=='npc':
                    p=string('npc',self.cache['npc_lookup_eax']);self.cache['npc_bytes']=p.ansi_bytes;self.phase='npc_return'
                elif self.phase=='npc_return':
                    normal('npc_helper','004d52c0')
                    normal('npc_assignment_span','opaque_string_assignment_cleanup_span')
                    self.record=QuestRecord(self.candidate.source_index,self.candidate.pointer,self.cache['script_bytes'],
                        self.cache['script_storage'],self.cache['fresh_minimum'],self.cache['display_bytes'],self.cache['npc_bytes'])
                    self.phase='compare'
                elif self.phase=='compare':
                    normal('npc_comparison','00505154',(self.cache['npc_bytes'],EXCLUDED_NPC))
                    if 'npc_not_excluded' not in self.cache:
                        v=o.values.get('npc_not_excluded')
                        if v is None:raise Missing(('value','npc_not_excluded'))
                        if type(v) is not bool:raise ValueError('Explicit normalized source inequality result required')
                        self.cache['npc_not_excluded']=v
                    normal('npc_comparison_cleanup','004040f8');self.phase='record'
                elif self.phase=='record':
                    allowed=self.cache['npc_not_excluded']
                    return self.out('ready_for_append' if allowed else 'npc_excluded',True,allowed)
                else:raise ValueError('Unknown Quest record phase')
        except Missing as error:return self.out('needs_observation',needed=error.args[0])
