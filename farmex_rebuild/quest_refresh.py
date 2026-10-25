"""Observed source refresh orchestration; no implicit game/provider access."""
from dataclasses import dataclass,field
from collections.abc import Mapping
from quest_candidate import ZONE_MATCHES
from quest_record import QuestPreparedFrame,QuestPreparedObservation
from quest_collection import QuestCollection,QuestVectorHeader,QuestAppendFrame,QuestAppendObservation,quest_extent
from quest_row import QuestRowSink
from quest_list_emit import QuestListFrame,QuestListObservation,QuestNpcSink
from quest_compare import sort_quest_rows_owned

BASE='frmMain/MainTab/sheetQuest/'
BUTTON_PATH=BASE+'btnRefreshQuests'
NPC_PATH=BASE+'cmbQuestNPCList'
LIST_PATH=BASE+'LwZoneQuests'


@dataclass(frozen=True)
class QuestRefreshContext:
    ticket:int
    generation:int
    phase:str
    source_index:int
    needed:object=None


@dataclass
class QuestRefreshState:
    collection:QuestCollection
    rows:QuestRowSink
    npcs:QuestNpcSink
    npc_selected:object=None


@dataclass(frozen=True)
class QuestRefreshObservation:
    normal_returns:object=field(default_factory=dict)
    clear_header:object=None
    zone_matches:object=field(default_factory=dict)
    prepared:object=field(default_factory=dict)
    appends:object=field(default_factory=dict)
    emission:object=None
    sort_permutation:object=None


@dataclass(frozen=True)
class QuestRefreshPlan:
    complete:bool
    status:str
    phase:str
    source_index:int
    zone_code:object=None
    needed:object=None
    calls:tuple=()
    order_policy:object=None
    native_execution_verified:bool=False
    live_compatibility_verified:bool=False


class QuestRefreshFrame:
    PREFIX=(('npc_clear','NPC.Clear'),('hepsi_convert','00505bb8'),('hepsi_add','NPC.Items.Add'),
            ('hepsi_cleanup','00505c64'),('npc_select_zero','NPC.SetItemIndex'),
            ('rows_clear','QuestList.Clear'),('vector_end','004d7030'),
            ('vector_begin','004d700c'),('vector_erase','004d7054'),
            ('clear_header',None),('init_script','00404148'),('init_display','00404148'),
            ('init_npc','00404148'),('region_query','0046209c'),
            ('init_region','00404148'),('region_resolve','004620bc'))
    TAIL=('tail_region','tail_npc','tail_display','tail_script','epilogue')

    def __init__(self,state,*,sort_mode='captured'):
        if not isinstance(state,QuestRefreshState) or not isinstance(state.collection,QuestCollection) or not isinstance(state.rows,QuestRowSink) or not isinstance(state.npcs,QuestNpcSink):
            raise ValueError('Typed owned refresh state required')
        if sort_mode not in ('captured','owned'):raise ValueError('Explicit captured or owned ordering policy required')
        self.state=state;self.sort_mode=sort_mode;self.order_policy=None
        self.phase='prefix';self.prefix_index=0;self.zone_index=0;self.zone_code=None;self.matches={}
        self.index=0;self.prepared=None;self.append=None;self.emitter=None
        self.normal=set();self.called=set();self.calls=[];self.tail_index=0;self.no_zone=False;self.final=None
        self.expected=self.snapshot()

    def snapshot(self):
        s=self.state
        return (id(s.collection),id(s.rows),id(s.npcs),s.collection.records,s.collection.header,s.collection.revision,
                s.rows.rows,s.rows.revision,s.npcs.items,s.npcs.revision,s.npc_selected)

    def out(self,status,needed=None,complete=False):
        if status!='refresh_state_conflict':self.expected=self.snapshot()
        p=QuestRefreshPlan(complete,status,self.phase,self.index,self.zone_code,needed,tuple(self.calls),self.order_policy)
        if complete:self.final=p
        return p

    def advance(self,observation=None):
        if self.final is not None:return self.final
        o=QuestRefreshObservation() if observation is None else observation
        if not isinstance(o,QuestRefreshObservation) or any(not isinstance(v,Mapping) for v in (o.normal_returns,o.zone_matches,o.prepared,o.appends)):
            raise ValueError('Typed sparse refresh observations required')
        if self.snapshot()!=self.expected:return self.out('refresh_state_conflict')
        class Missing(Exception):pass
        def normal(label,helper):
            if label not in self.called:self.calls.append((helper,label));self.called.add(label)
            if label in self.normal:return
            receipt=o.normal_returns.get(label)
            if receipt is not None and type(receipt) is not bool:raise ValueError('Normalized normal-return receipt required')
            if receipt is not True:raise Missing((label,))
            self.normal.add(label)
        s=self.state
        try:
            while True:
                if self.phase=='prefix':
                    if self.prefix_index==len(self.PREFIX):self.phase='zone';continue
                    label,helper=self.PREFIX[self.prefix_index]
                    if helper is not None:normal(label,helper)
                    if label=='npc_clear':s.npcs.items=();s.npcs.revision+=1
                    elif label=='hepsi_add':s.npcs.items+=('HEPSI',);s.npcs.revision+=1
                    elif label=='npc_select_zero':s.npc_selected=0
                    elif label=='rows_clear':s.rows.rows=();s.rows.revision+=1
                    elif label=='clear_header':
                        if o.clear_header is None:raise Missing(('clear_header',))
                        count=quest_extent(o.clear_header)
                        if not count.complete:raise Missing(('clear_header',count.needed))
                        if count.raw_count!=0:return self.out('unresolved_clear_header',('empty_collection',))
                        s.collection.records=();s.collection.header=o.clear_header;s.collection.revision+=1
                    self.prefix_index+=1
                    self.expected=self.snapshot()
                elif self.phase=='zone':
                    if self.zone_index==len(ZONE_MATCHES):
                        self.zone_code=0;self.no_zone=True;self.phase='tail';continue
                    name,code=ZONE_MATCHES[self.zone_index]
                    normal(('zone_literal',name),'004040bc')
                    normal(('zone_compare',name),'00505134')
                    if name not in self.matches:
                        value=o.zone_matches.get(name)
                        if value is None:raise Missing(('zone_match',name))
                        if type(value) is not bool:raise ValueError('Normalized region equality result required')
                        self.matches[name]=value
                    normal(('zone_cleanup',name),'004040f8')
                    if self.matches[name]:self.zone_code=code;self.phase='scan'
                    else:self.zone_index+=1
                elif self.phase=='scan':
                    if self.index>30000:
                        self.emitter=QuestListFrame(s.collection,s.rows,s.npcs);self.phase='emit';continue
                    if self.prepared is None:self.prepared=QuestPreparedFrame(self.index,self.zone_code)
                    p=self.prepared.advance(o.prepared.get(self.index,QuestPreparedObservation()))
                    if not p.complete:return self.out(p.status,('candidate',self.index,p.needed))
                    if p.eligible_for_append:
                        if self.append is None:self.append=QuestAppendFrame(s.collection,p.record)
                        self.phase='append'
                    elif p.record_plan is not None:self.phase='candidate_cleanup'
                    else:self.phase='next'
                elif self.phase=='append':
                    try:p=self.append.advance(o.appends.get(self.index,QuestAppendObservation()))
                    finally:self.expected=self.snapshot()
                    if not p.complete:return self.out(p.status,('append',self.index,p.needed))
                    self.phase='candidate_cleanup'
                elif self.phase=='candidate_cleanup':
                    normal(('candidate_cleanup',self.index),'004040f8');self.phase='next'
                elif self.phase=='next':
                    self.index+=1;self.prepared=None;self.append=None;self.phase='scan'
                elif self.phase=='emit':
                    try:p=self.emitter.advance(o.emission if o.emission is not None else QuestListObservation())
                    finally:self.expected=self.snapshot()
                    if not p.complete:return self.out(p.status,('emission',p.needed))
                    self.phase='sort'
                elif self.phase=='sort':
                    normal('sort_returned','00506b78')
                    if self.sort_mode=='owned':
                        p=sort_quest_rows_owned(s.rows.rows)
                        if not p.complete:return self.out(p.status,('sort',p.needed))
                        s.rows.rows=p.rows;self.order_policy=p.tie_policy
                    else:
                        permutation=o.sort_permutation
                        if permutation is None:raise Missing(('sort_permutation',))
                        if type(permutation) is not tuple or any(type(i) is not int for i in permutation) or sorted(permutation)!=list(range(len(s.rows.rows))):
                            raise ValueError('Explicit complete captured row permutation required')
                        s.rows.rows=tuple(s.rows.rows[i] for i in permutation)
                        self.order_policy='explicit captured permutation; native execution not independently verified'
                    s.rows.revision+=1;self.expected=self.snapshot();self.phase='tail'
                elif self.phase=='tail':
                    if self.tail_index==len(self.TAIL):
                        return self.out('locally_refreshed_no_zone' if self.no_zone else 'locally_refreshed',complete=True)
                    label=self.TAIL[self.tail_index]
                    normal(label,'004d6668 normal return' if label=='epilogue' else '004040f8')
                    self.tail_index+=1
                else:raise ValueError('Unknown refresh phase')
        except Missing as error:return self.out('needs_observation',error.args[0])
