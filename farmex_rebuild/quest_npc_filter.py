"""004b4878 ->004d553c observed NPC filter; own ANSI equality is optional."""
from dataclasses import dataclass,field
from collections.abc import Mapping
from quest_collection import QuestCollection,quest_extent
from quest_record import QuestRecord
from quest_row import QuestRowSink,QuestRowFrame,QuestRowObservation
from quest_compare import sort_quest_rows_owned
from name_codec import WindowsNameCodec


@dataclass(frozen=True)
class QuestNpcFilterObservation:
    normal_returns:object=field(default_factory=dict)
    selected_ansi:object=None
    code_page:object=None
    hepsi_equal:object=None
    npc_equal:object=field(default_factory=dict)
    rows:object=field(default_factory=dict)
    sort_permutation:object=None


@dataclass(frozen=True)
class QuestNpcFilterPlan:
    complete:bool
    status:str
    collection_index:int
    selected_ansi:object=None
    all_npcs:object=None
    needed:object=None
    calls:tuple=()
    equality_policy:str='captured source equality outcomes'
    order_policy:object=None
    native_execution_verified:bool=False
    live_compatibility_verified:bool=False


class QuestNpcFilterFrame:
    PREFIX=(('selection','NPC.GetItemIndex'),('rows_clear','QuestList.Clear'),
            ('selected_text','NPC.Items.Strings[index]'),('selected_convert','004073a0'),
            ('selected_unicode_cleanup','00505c64'),('hepsi_literal','004040bc'),
            ('hepsi_compare','00505134'),('hepsi_cleanup','004040f8'))

    def __init__(self,collection,rows,selection_index,combo_items,*,equality_mode='captured',sort_mode='captured'):
        if not isinstance(collection,QuestCollection) or not isinstance(rows,QuestRowSink):raise ValueError('Typed collection and own row sink required')
        if type(selection_index) is not int or not -0x80000000<=selection_index<=0x7fffffff:raise ValueError('Signed item index required')
        if type(combo_items) is not tuple or any(type(v) is not str for v in combo_items):raise ValueError('Explicit Unicode NPC options required')
        if equality_mode not in ('captured','owned_bytes') or sort_mode not in ('captured','owned'):raise ValueError('Explicit own or captured policies required')
        self.collection=collection;self.rows=rows;self.selection=selection_index;self.items=combo_items
        self.equality_mode=equality_mode;self.sort_mode=sort_mode;self.order_policy=None
        self.phase='prefix';self.prefix_index=0;self.index=0;self.ansi=None;self.text=None;self.all=None
        self.matches={};self.npc_inputs={};self.row=None;self.final=None
        self.normal=set();self.called=set();self.calls=[];self.expected=(rows.rows,rows.revision)

    def out(self,status,needed=None,complete=False):
        p=QuestNpcFilterPlan(complete,status,self.index,self.ansi,self.all,needed,tuple(self.calls),
            'owned exact ANSI bytes; native codepage comparison unverified' if self.equality_mode=='owned_bytes' else 'captured source equality outcomes',self.order_policy)
        if complete:self.final=p
        return p

    def advance(self,observation=None):
        if self.final is not None:return self.final
        o=QuestNpcFilterObservation() if observation is None else observation
        if not isinstance(o,QuestNpcFilterObservation) or any(not isinstance(v,Mapping) for v in (o.normal_returns,o.npc_equal,o.rows)):
            raise ValueError('Typed sparse NPC-filter observations required')
        if (self.rows.rows,self.rows.revision)!=self.expected:return self.out('row_sink_conflict')
        class Missing(Exception):pass
        def normal(label,helper):
            if label not in self.called:self.calls.append((helper,label));self.called.add(label)
            if label in self.normal:return
            value=o.normal_returns.get(label)
            if value is not None and type(value) is not bool:raise ValueError('Normalized normal-return receipt required')
            if value is not True:raise Missing((label,))
            self.normal.add(label)
        def record():
            if type(self.collection.records) is not tuple or self.index>=len(self.collection.records):raise Missing(('owned_record',self.index))
            r=self.collection.records[self.index]
            if not isinstance(r,QuestRecord):raise ValueError('Typed Quest record required')
            return r
        def boolean(value,label):
            if value is None:raise Missing((label,))
            if type(value) is not bool:raise ValueError('Normalized equality outcome required')
            return value
        try:
            while True:
                if self.phase=='prefix':
                    if self.prefix_index==len(self.PREFIX):self.phase='count';continue
                    label,helper=self.PREFIX[self.prefix_index];normal(label,helper)
                    if label=='rows_clear':
                        self.rows.rows=();self.rows.revision+=1;self.expected=(self.rows.rows,self.rows.revision)
                    elif label=='selected_text':
                        if not 0<=self.selection<len(self.items):return self.out('unresolved_native_item_index',('selected_index',self.selection))
                        self.text=self.items[self.selection]
                    elif label=='selected_convert' and self.ansi is None:
                        if o.selected_ansi is not None:
                            if type(o.selected_ansi) is not bytes:raise ValueError('Immutable captured ANSI selection required')
                            self.ansi=o.selected_ansi
                        elif not self.text:self.ansi=b''
                        elif o.code_page is None:raise Missing(('code_page_or_selected_ansi',))
                        else:self.ansi=WindowsNameCodec(o.code_page).encode(self.text)[0]
                    elif label=='hepsi_compare' and self.all is None:
                        self.all=(self.ansi==b'HEPSI') if self.equality_mode=='owned_bytes' else boolean(o.hepsi_equal,'hepsi_equal')
                    self.prefix_index+=1
                elif self.phase=='count':
                    if self.collection.header is None:raise Missing(('collection_header',self.index))
                    count=quest_extent(self.collection.header)
                    if not count.complete:raise Missing(('collection_header',self.index,count.needed))
                    if count.raw_count<=self.index:self.phase='sort';continue
                    if self.all:self.phase='row_init'
                    else:self.phase='match'
                elif self.phase=='match':
                    if self.index not in self.npc_inputs:
                        npc=record().npc_bytes
                        if type(npc) is not bytes:raise ValueError('Immutable NPC ANSI bytes required')
                        self.npc_inputs[self.index]=npc
                    normal(('npc_compare',self.index),'00505134')
                    if self.index not in self.matches:
                        self.matches[self.index]=(self.npc_inputs[self.index]==self.ansi) if self.equality_mode=='owned_bytes' else boolean(o.npc_equal.get(self.index),('npc_equal',self.index))
                    self.phase='row_init' if self.matches[self.index] else 'next'
                elif self.phase=='row_init':
                    r=record();self.row=QuestRowFrame(self.rows,self.index,r.minimum_dword,r.display_bytes);self.phase='row'
                elif self.phase=='row':
                    try:p=self.row.advance(o.rows.get(self.index,QuestRowObservation()))
                    finally:self.expected=(self.rows.rows,self.rows.revision)
                    if not p.complete:return self.out(p.status,('row',self.index,p.needed))
                    self.phase='next'
                elif self.phase=='next':self.index+=1;self.row=None;self.phase='count'
                elif self.phase=='sort':
                    normal('sort_returned','00506b78')
                    if self.sort_mode=='owned':
                        p=sort_quest_rows_owned(self.rows.rows)
                        if not p.complete:return self.out(p.status,('sort',p.needed))
                        self.rows.rows=p.rows;self.order_policy=p.tie_policy
                    else:
                        permutation=o.sort_permutation
                        if permutation is None:raise Missing(('sort_permutation',))
                        if type(permutation) is not tuple or any(type(i) is not int for i in permutation) or sorted(permutation)!=list(range(len(self.rows.rows))):raise ValueError('Complete captured row permutation required')
                        self.rows.rows=tuple(self.rows.rows[i] for i in permutation);self.order_policy='explicit captured permutation'
                    self.rows.revision+=1;self.expected=(self.rows.rows,self.rows.revision);self.phase='cleanup'
                elif self.phase=='cleanup':normal('selected_ansi_cleanup','004040f8');self.phase='epilogue'
                elif self.phase=='epilogue':
                    normal('epilogue','004d553c normal return');return self.out('locally_filtered',complete=True)
                else:raise ValueError('Unknown NPC-filter phase')
        except Missing as error:return self.out('needs_observation',error.args[0])
