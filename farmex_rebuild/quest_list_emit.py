"""Refresh's collection-to-row/NPC stage, stopping before the native sort."""
from dataclasses import dataclass,field
from collections.abc import Mapping
from quest_collection import QuestCollection,QuestVectorHeader,quest_extent
from quest_record import QuestRecord
from quest_row import QuestRowSink,QuestRowFrame,QuestRowObservation
from name_codec import WindowsNameCodec


@dataclass
class QuestNpcSink:
    items:tuple=()
    revision:int=0


@dataclass(frozen=True)
class QuestListObservation:
    rows:object=field(default_factory=dict)
    normal_returns:object=field(default_factory=dict)
    npc_contains:object=field(default_factory=dict)
    code_page:object=None


@dataclass(frozen=True)
class QuestListPlan:
    complete:bool
    status:str
    collection_index:int
    needed:object=None
    calls:tuple=()
    sort_verified:bool=False
    native_execution_verified:bool=False
    live_compatibility_verified:bool=False


class QuestListFrame:
    def __init__(self,collection,rows,npcs):
        if not isinstance(collection,QuestCollection) or not isinstance(rows,QuestRowSink) or not isinstance(npcs,QuestNpcSink):
            raise ValueError('Typed collection and owned row/NPC sinks required')
        if type(npcs.items) is not tuple or any(type(v) is not str for v in npcs.items):
            raise ValueError('Immutable Unicode NPC baseline required')
        self.collection=collection;self.rows=rows;self.npcs=npcs
        self.expected_npcs=npcs.items;self.npc_revision=npcs.revision
        self.expected_rows=rows.rows;self.row_revision=rows.revision
        self.index=0;self.phase='count';self.row=None;self.npc=None;self.text=None
        self.called=set();self.normal=set();self.calls=[];self.contains={};self.final=None

    def out(self,status,needed=None,complete=False):
        p=QuestListPlan(complete,status,self.index,needed,tuple(self.calls))
        if complete:self.final=p
        return p

    def advance(self,observation=None):
        if self.final is not None:return self.final
        o=QuestListObservation() if observation is None else observation
        if not isinstance(o,QuestListObservation) or any(not isinstance(v,Mapping) for v in (o.rows,o.normal_returns,o.npc_contains)):
            raise ValueError('Typed sparse list observations required')
        if self.npcs.items!=self.expected_npcs or self.npcs.revision!=self.npc_revision:
            return self.out('npc_sink_conflict')
        # During a pending row, its frame owns row conflict detection.
        if self.phase!='row' and (self.rows.rows!=self.expected_rows or self.rows.revision!=self.row_revision):
            return self.out('row_sink_conflict')
        class Missing(Exception):pass
        def normal(label,helper):
            key=(self.index,label)
            if key not in self.called:self.calls.append((helper,key));self.called.add(key)
            if key in self.normal:return
            value=o.normal_returns.get(key)
            if value is not None and type(value) is not bool:raise ValueError('Normalized normal-return receipt required')
            if value is not True:raise Missing(key)
            self.normal.add(key)
        def record():
            if type(self.collection.records) is not tuple or self.index>=len(self.collection.records):
                raise Missing((self.index,'owned_record'))
            value=self.collection.records[self.index]
            if not isinstance(value,QuestRecord):raise ValueError('Typed Quest record required')
            return value
        try:
            while True:
                if self.phase=='count':
                    h=self.collection.header
                    if h is None:raise Missing((self.index,'collection_header'))
                    if not isinstance(h,QuestVectorHeader):raise ValueError('Typed current collection header required')
                    count=quest_extent(h)
                    if not count.complete:raise Missing((self.index,'collection_header',count.needed))
                    if count.raw_count<=self.index:return self.out('rows_and_npcs_emitted_sort_pending',complete=True)
                    r=record()
                    self.row=QuestRowFrame(self.rows,self.index,r.minimum_dword,r.display_bytes)
                    self.phase='row'
                elif self.phase=='row':
                    try:p=self.row.advance(o.rows.get(self.index,QuestRowObservation()))
                    finally:self.expected_rows=self.rows.rows;self.row_revision=self.rows.revision
                    if not p.complete:return self.out(p.status,('row',self.index,p.needed))
                    self.expected_rows=self.rows.rows;self.row_revision=self.rows.revision
                    # Source reads record+18 after 004d540c returns, not at
                    # row-helper entry. Keep this separate fresh access.
                    self.phase='npc_read'
                elif self.phase=='npc_read':
                    self.npc=record().npc_bytes
                    if type(self.npc) is not bytes:raise ValueError('Immutable NPC ANSI bytes required')
                    self.phase='contains'
                elif self.phase=='contains':
                    normal('contains','00467d90')
                    if self.index not in self.contains:
                        value=o.npc_contains.get(self.index)
                        if value is None:raise Missing((self.index,'contains_AL'))
                        if type(value) is not bool:raise ValueError('Normalized containment AL required')
                        self.contains[self.index]=value
                    self.phase='next' if self.contains[self.index] else 'npc_convert'
                elif self.phase=='npc_convert':
                    normal('npc_convert','00403d84')
                    if self.text is None:
                        if not self.npc:self.text=''
                        elif o.code_page is None:raise Missing((self.index,'code_page'))
                        else:self.text=WindowsNameCodec(o.code_page).decode(self.npc)
                    self.phase='npc_add'
                elif self.phase=='npc_add':
                    normal('npc_add','NPC.Items.Add')
                    self.npcs.items=self.expected_npcs+(self.text,);self.npcs.revision+=1
                    self.expected_npcs=self.npcs.items;self.npc_revision=self.npcs.revision
                    self.phase='npc_cleanup'
                elif self.phase=='npc_cleanup':
                    normal('npc_cleanup','00505c64');self.phase='next'
                elif self.phase=='next':
                    self.index+=1;self.row=None;self.npc=None;self.text=None;self.phase='count'
                else:raise ValueError('Unknown emission phase')
        except Missing as error:return self.out('needs_observation',error.args[0])
