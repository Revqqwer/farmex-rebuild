"""4d5e8c/4d5f60 metadata paths and fresh-count bulk loops, captured local data.

These source bodies do not call the selected-Take path or queue a quest packet.
Do not describe completion as a server quest take/cancel acknowledgement.
"""
from dataclasses import dataclass,field
from collections.abc import Mapping
from rtl_integer32 import parse_rtl_integer32

BASE='frmMain/MainTab/sheetQuest/'
LIST_PATH=BASE+'LwZoneQuests'
METHODS={BASE+'btnTakeAllQuests':'take_all',BASE+'btnCancelAllQuests':'cancel_all',
         BASE+'GroupBox53/btnCancelQuest':'cancel'}


def raw(value):
    if value is not None and (type(value) is not int or not 0<=value<=0xffffffff):raise ValueError('Raw DWORD required')


@dataclass(frozen=True)
class QuestMetadataRecord:
    entry0_dword:object=None
    data_pointer_dword:object=None
    field_1c_dword:object=None
    def __post_init__(self):
        for value in vars(self).values():raw(value)


@dataclass(frozen=True)
class QuestMetadataDatabase:
    array_dword:object=None
    records:tuple=()
    def __post_init__(self):
        raw(self.array_dword)
        if type(self.records) is not tuple or any(not isinstance(r,QuestMetadataRecord) for r in self.records):
            raise ValueError('Bounded immutable captured record tuple required')


@dataclass(frozen=True)
class QuestMetadataObservation:
    selection_returned:object=None
    setup_returns:object=field(default_factory=dict)
    caption_returns:object=field(default_factory=dict)
    conversion_returns:object=field(default_factory=dict)
    cleanup_returns:object=field(default_factory=dict)
    read_returns:object=field(default_factory=dict)
    epilogue_returns:object=field(default_factory=dict)
    database:object=None


@dataclass(frozen=True)
class QuestMetadataResult:
    status:str
    complete:bool=False
    done:bool=False
    needed:object=None
    reads:tuple=()
    processed_rows:int=0
    error:object=None
    native_execution_verified:bool=False
    live_compatibility_verified:bool=False


@dataclass(frozen=True)
class QuestMetadataContext:
    invocation:int
    generation:int
    method:str
    phase:str
    row:int
    needed:object=None


class QuestMetadataFrame:
    def __init__(self,method,sink):
        if method not in ('take_all','cancel_all','cancel'):raise ValueError('Known metadata callback required')
        self.method=method;self.sink=sink;self.index=0;self.processed=0
        self.phase='selection' if method=='cancel' else 'count'
        self.cache={};self.reads=[];self.busy=False;self.result=QuestMetadataResult('queued')
    def out(self,status,complete=False,done=False,needed=None,error=None):
        self.result=QuestMetadataResult(status,complete,done,needed,tuple(self.reads),self.processed,error);return self.result
    def cancel(self,reason):
        if not self.result.done:self.out('cancelled',done=True,error=reason)
        return self.result
    def hold(self,error):
        if not self.result.done:self.out('needs_observation',needed=self.result.needed,error=str(error))
        return self.result
    def advance(self,o=None):
        if self.result.done or self.busy:return self.result
        o=QuestMetadataObservation() if o is None else o
        if not isinstance(o,QuestMetadataObservation):raise ValueError('Typed Quest metadata observation required')
        self.busy=True
        class Missing(Exception):pass
        def normal(group):
            key=('normal',group)
            if self.cache.get(key) is True:return
            if group=='selection_returned':value=o.selection_returned
            else:
                data=getattr(o,group)
                if not isinstance(data,Mapping):raise ValueError('Indexed normal returns required')
                value=data.get(self.index)
            if value is not None and type(value) is not bool:raise ValueError('Explicit source normal return required')
            if value is not True:raise Missing((group,self.index))
            self.cache[key]=True
        def signed(value):
            if type(value) is not int or not -0x80000000<=value<0x80000000:raise ValueError('Own signed row index/count required')
            return value
        def database():
            if o.database is None:raise Missing(('captured_database',self.index))
            if not isinstance(o.database,QuestMetadataDatabase):raise ValueError('Typed captured database required')
            return o.database
        def record():
            db=database();number=self.cache['record_index']
            if number>=len(db.records):return None
            return db.records[number]
        try:
            for _ in range(64):
                self.out('advancing',needed=(self.phase,self.index))
                if self.phase=='selection':
                    self.index=signed(self.sink.selected_index());self.phase='selection_return'
                elif self.phase=='selection_return':normal('selection_returned');self.phase='setup'
                elif self.phase=='count':
                    if signed(self.sink.count())<=self.index:return self.out('metadata_read_complete',True,True)
                    self.phase='setup'
                elif self.phase=='setup':
                    normal('setup_returns');self.phase='epilogue' if self.index<0 else 'caption'
                elif self.phase=='caption':
                    value=self.sink.caption(self.index)
                    if type(value) is not str:raise ValueError('Own caption Unicode required')
                    self.cache['caption']=value;self.phase='caption_return'
                elif self.phase=='caption_return':normal('caption_returns');self.phase='parse'
                elif self.phase=='parse':
                    value=parse_rtl_integer32(self.cache['caption'])
                    if not value.accepted:raise Missing(('caption_exception_outcome',self.index,value.code))
                    normal('conversion_returns');self.cache['record_index']=value.dword;self.phase='cleanup'
                elif self.phase=='cleanup':normal('cleanup_returns');self.phase='database'
                elif self.phase=='database':
                    db=database()
                    if db.array_dword is None:raise Missing(('record_array_dword',self.index))
                    if db.array_dword==0:raise Missing(('native_null_record_array',self.index))
                    if record() is None:return self.out('outside_fixture_database',done=True,error='Own bounds reject source unchecked addressing')
                    self.cache['base']=db.array_dword;self.phase='entry'
                elif self.phase=='entry':
                    entry=record()
                    if entry is None:return self.out('outside_fixture_database',done=True,error='Captured tuple changed')
                    number=self.cache['record_index'];address=(self.cache['base']+number*28)&0xffffffff
                    if self.method=='take_all':
                        if entry.entry0_dword is None:raise Missing(('entry0_dword',self.index))
                        self.reads.append((self.index,number,address,entry.entry0_dword,'direct_entry0'))
                        self.phase='epilogue'
                    else:
                        if entry.data_pointer_dword is None:raise Missing(('data_pointer_dword',self.index))
                        self.cache['pointer']=entry.data_pointer_dword
                        self.reads.append((self.index,number,(address+4)&0xffffffff,entry.data_pointer_dword,'direct_data_pointer'))
                        self.phase='guarded_read'
                elif self.phase=='guarded_read':
                    # The result is captured before the helper normal receipt;
                    # do not reread a different value while that receipt waits.
                    if 'read_value' not in self.cache:
                        entry=record()
                        if entry is None:return self.out('outside_fixture_database',done=True,error='Captured tuple changed')
                        if entry.field_1c_dword is None:raise Missing(('field_1c_dword',self.index))
                        self.cache['read_value']=entry.field_1c_dword
                    normal('read_returns')
                    self.reads.append((self.index,self.cache['record_index'],(self.cache['pointer']+0x1c)&0xffffffff,
                                       self.cache['read_value'],'guarded_0045dc44'))
                    self.phase='epilogue'
                elif self.phase=='epilogue':
                    normal('epilogue_returns')
                    if self.index>=0:self.processed+=1
                    if self.method=='cancel':return self.out('metadata_read_complete' if self.index>=0 else 'no_selection',True,True)
                    self.index+=1;self.cache={};self.phase='count'
                else:raise ValueError('Unknown Quest metadata phase')
            return self.out('continuation',needed=('own_chunk',))
        except Missing as error:return self.out('needs_observation',needed=error.args[0])
        finally:self.busy=False
