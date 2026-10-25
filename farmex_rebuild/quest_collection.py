"""Owned Quest vector projection and captured append branches; no native heap IO."""
from dataclasses import dataclass
from quest_record import QuestRecord


def dword(value):
    if type(value) is not int or not 0<=value<=0xffffffff:raise ValueError('Raw captured DWORD required')
    return value


@dataclass(frozen=True)
class QuestVectorHeader:
    begin:object=None
    end:object=None
    capacity_end:object=None


@dataclass(frozen=True)
class QuestExtentPlan:
    complete:bool
    raw_count:object=None
    needed:object=None
    reads:tuple=()


def quest_extent(header,capacity=False):
    if not isinstance(header,QuestVectorHeader):raise ValueError('Typed header capture required')
    reads=[]
    if header.begin is None:return QuestExtentPlan(False,needed='begin')
    begin=dword(header.begin);reads.append((0x10,begin))
    if begin==0:return QuestExtentPlan(True,0,reads=tuple(reads))
    last=header.capacity_end if capacity else header.end
    if last is None:return QuestExtentPlan(False,needed='capacity_end' if capacity else 'end',reads=tuple(reads))
    last=dword(last);reads.append((0x18 if capacity else 0x14,last))
    delta=(last-begin)&0xffffffff
    signed=delta if delta<0x80000000 else delta-0x100000000
    count=abs(signed)//28
    if signed<0:count=-count
    return QuestExtentPlan(True,count&0xffffffff,reads=tuple(reads))


@dataclass
class QuestCollection:
    records:tuple=()
    header:object=None
    revision:int=0


@dataclass(frozen=True)
class QuestAppendObservation:
    size_header:object=None
    capacity_header:object=None
    size_returned:object=None
    capacity_returned:object=None
    inplace_returned:object=None
    inplace_end_dword:object=None
    reallocate_returned:object=None
    post_header:object=None
    reallocate_end_returned:object=None


@dataclass(frozen=True)
class QuestAppendPlan:
    complete:bool
    status:str
    branch:object=None
    committed:bool=False
    needed:object=None
    calls:tuple=()
    native_execution_verified:bool=False
    live_compatibility_verified:bool=False


class QuestAppendFrame:
    def __init__(self,state,record):
        if not isinstance(state,QuestCollection) or type(state.records) is not tuple or not isinstance(record,QuestRecord):
            raise ValueError('Owned collection and logical Quest record required')
        self.state=state;self.record=record;self.before=state.records;self.revision=state.revision
        self.phase='size';self.branch=None;self.cache={};self.normal=set();self.called=set();self.calls=[]
        self.committed=False;self.final=None
    def out(self,status,complete=False,needed=None):
        p=QuestAppendPlan(complete,status,self.branch,self.committed,needed,tuple(self.calls))
        if complete:self.final=p
        return p
    def advance(self,o=None):
        if self.final is not None:return self.final
        o=QuestAppendObservation() if o is None else o
        if not isinstance(o,QuestAppendObservation):raise ValueError('Typed append observations required')
        expected=self.before+(self.record,) if self.committed else self.before
        if self.state.revision!=self.revision or self.state.records!=expected:return self.out('collection_conflict')
        class Missing(Exception):pass
        def normal(label,helper):
            if label not in self.called:self.calls.append((helper,label));self.called.add(label)
            if label in self.normal:return
            v=getattr(o,label)
            if v is not None and type(v) is not bool:raise ValueError('Explicit helper normal return required')
            if v is not True:raise Missing((label,))
            self.normal.add(label)
        def extent(which):
            key=which+'_header'
            if key not in self.cache:
                h=getattr(o,key)
                if h is None:raise Missing((key,))
                plan=quest_extent(h,which=='capacity')
                if not plan.complete:raise Missing((key,plan.needed))
                self.cache[key]=h;self.cache[which]=plan.raw_count
            return self.cache[which]
        def commit(header):
            if not self.committed:
                self.state.records=self.before+(self.record,);self.state.revision+=1;self.revision=self.state.revision
                self.committed=True
            self.state.header=header
        try:
            while True:
                if self.phase=='size':
                    normal('size_returned','004d7104');extent('size');self.phase='capacity'
                elif self.phase=='capacity':
                    normal('capacity_returned','004d712c');extent('capacity')
                    self.branch='inplace' if self.cache['size']<self.cache['capacity'] else 'reallocate'
                    if self.cache['size']!=len(self.before):return self.out('unresolved_captured_size',needed=('owned_record_count',self.cache['size']))
                    self.phase=self.branch
                elif self.phase=='inplace':
                    normal('inplace_returned','004d7154')
                    if o.inplace_end_dword is None:raise Missing(('inplace_end_dword',))
                    end=dword(o.inplace_end_dword);self.cache['end']=end
                    old=self.state.header if isinstance(self.state.header,QuestVectorHeader) else QuestVectorHeader()
                    # The source caller writes EAX to end immediately. Keep
                    # that known prefix before post-header evidence arrives.
                    commit(QuestVectorHeader(old.begin,end,old.capacity_end));self.phase='post'
                elif self.phase=='reallocate':
                    normal('reallocate_end_returned','004d7030')
                    normal('reallocate_returned','004d71b0');self.phase='post'
                elif self.phase=='post':
                    if o.post_header is None:raise Missing(('post_header',))
                    h=o.post_header;plan=quest_extent(h)
                    if not plan.complete:raise Missing(('post_header',plan.needed))
                    if self.branch=='inplace' and h.end!=self.cache['end']:
                        return self.out('unresolved_post_header',needed=('caller_end_store',self.cache['end']))
                    if plan.raw_count!=len(self.before)+1:return self.out('unresolved_post_header',needed=('post_count',len(self.before)+1))
                    commit(h)
                    return self.out('locally_appended',True)
                else:raise ValueError('Unknown Quest append phase')
        except Missing as error:return self.out('needs_observation',needed=error.args[0])
