"""Observed Quest detail header/row updates; no invented requirement/reward data."""
from dataclasses import dataclass,field
from collections.abc import Mapping
from quest_collection import QuestCollection,dword
from quest_record import QuestRecord
from quest_row import QuestRow
from rtl_integer32 import parse_rtl_integer32
from name_codec import WindowsNameCodec

MAIN_PATH='frmMain/MainTab/sheetQuest/LwZoneQuests'
DETAILS_PATH='frmMain/MainTab/sheetQuest/GroupBox53/LwQuestDetails'


@dataclass(frozen=True)
class QuestDetailsContext:
    ticket:int
    generation:int
    phase:int
    selected_row:int
    record_index:object=None
    needed:object=None


@dataclass
class QuestDetailsState:
    headings:tuple=('','')
    rows:tuple=()
    revision:int=0


@dataclass(frozen=True)
class QuestDetailsObservation:
    normal_returns:object=field(default_factory=dict)
    caption_parse_dword:object=None
    level_unicode:object=None
    unicode_values:object=field(default_factory=dict)
    code_pages:object=field(default_factory=dict)


@dataclass(frozen=True)
class QuestDetailsPlan:
    complete:bool
    status:str
    record_index:object=None
    needed:object=None
    calls:tuple=()
    reads:tuple=()
    native_execution_verified:bool=False
    live_compatibility_verified:bool=False


class QuestDetailsFrame:
    STEPS=(('selection','QuestList.GetItemIndex'),('caption','0045f7f4'),
           ('caption_parse','0050638e'),('caption_cleanup','00505c64'),
           ('level_format','00407360'),('level_concat','00505f10'),
           ('header0_get','TListColumns.GetItem(0)'),('header0_set','00506bc6'),
           ('level_heading_cleanup','00505c64'),('level_number_cleanup','00505c64'),
           ('display_convert','00403d84'),('header1_get','TListColumns.GetItem(1)'),
           ('header1_set','00506bc6'),('display_cleanup','00505c64'),
           ('details_clear','QuestDetails.Clear'),('npc_add','00506ba2'),
           ('npc_caption_convert','00505bb8'),('npc_caption_set','00506bae'),
           ('npc_caption_cleanup','00505c64'),('npc_convert','00403d84'),
           ('npc_subitem','SubItems.Add'),('npc_cleanup','00505c64'),
           ('task_add','00506ba2'),('task_caption_convert','00505bb8'),
           ('task_caption_set','00506bae'),('task_caption_cleanup','00505c64'),
           ('task_convert','00505bb8'),('task_subitem','SubItems.Add'),
           ('task_cleanup','00505c64'),('blank_add','00506ba2'),
           ('reward_add','00506ba2'),('reward_caption_convert','00505bb8'),
           ('reward_caption_set','00506bae'),('reward_caption_cleanup','00505c64'),
           ('reward_convert','00505bb8'),('reward_subitem','SubItems.Add'),
           ('reward_cleanup','00505c64'),('epilogue','004d5738 normal return'))

    def __init__(self,collection,state,main_rows,selected_index,*,use_owned_scalar_model=False):
        if not isinstance(collection,QuestCollection) or not isinstance(state,QuestDetailsState):raise ValueError('Typed own collection and details state required')
        if type(main_rows) is not tuple or any(not isinstance(r,QuestRow) for r in main_rows):raise ValueError('Immutable visible row capture required')
        if type(selected_index) is not int or not -0x80000000<=selected_index<=0x7fffffff:raise ValueError('Signed selected row index required')
        if type(use_owned_scalar_model) is not bool:raise ValueError('Explicit scalar policy required')
        if type(state.headings) is not tuple or any(type(s) is not str for s in state.headings) or type(state.rows) is not tuple or any(not isinstance(r,QuestRow) for r in state.rows):raise ValueError('Typed heading/row state required')
        self.collection=collection;self.state=state;self.main_rows=main_rows;self.selected=selected_index;self.owned=use_owned_scalar_model
        self.phase=0;self.cache={};self.normal=set();self.called=set();self.calls=[];self.reads=[];self.row_indices={};self.final=None
        self.expected=(state.headings,state.rows,state.revision)

    def out(self,status,needed=None,complete=False):
        p=QuestDetailsPlan(complete,status,self.cache.get('record_index'),needed,tuple(self.calls),tuple(self.reads))
        if complete:self.final=p
        return p

    def write(self,*,headings=None,rows=None):
        if headings is not None:self.state.headings=headings
        if rows is not None:self.state.rows=rows
        self.state.revision+=1;self.expected=(self.state.headings,self.state.rows,self.state.revision)

    def advance(self,observation=None):
        if self.final is not None:return self.final
        o=QuestDetailsObservation() if observation is None else observation
        if not isinstance(o,QuestDetailsObservation) or any(not isinstance(v,Mapping) for v in (o.normal_returns,o.unicode_values,o.code_pages)):
            raise ValueError('Typed sparse detail observations required')
        if (self.state.headings,self.state.rows,self.state.revision)!=self.expected:return self.out('details_state_conflict')
        class Missing(Exception):pass
        def record_field(label,attribute,offset):
            if label in self.cache:return self.cache[label]
            index=self.cache['record_index']
            if type(self.collection.records) is not tuple or index>=len(self.collection.records):raise Missing(('owned_record',index))
            r=self.collection.records[index]
            if not isinstance(r,QuestRecord):raise ValueError('Typed Quest record required')
            value=getattr(r,attribute);self.cache[label]=value;self.reads.append((index,offset,label,value));return value
        def unicode_value(role,raw):
            if type(raw) is not bytes:raise ValueError('Immutable source ANSI bytes required')
            if role in self.cache:return self.cache[role]
            value=o.unicode_values.get(role)
            if value is not None:
                if type(value) is not str:raise ValueError('Explicit Unicode conversion result required')
            elif not raw:value=''
            else:
                cp=o.code_pages.get(role)
                if cp is None:raise Missing(('code_page_or_unicode',role))
                value=WindowsNameCodec(cp).decode(raw)
            self.cache[role]=value;return value
        try:
            while self.phase<len(self.STEPS):
                label,helper=self.STEPS[self.phase]
                # Source evaluates the record field before entering conversion.
                if label=='level_format':dword(record_field('level_dword','minimum_dword',0x10))
                if label=='display_convert':record_field('display_bytes','display_bytes',0x14)
                if label=='npc_convert':record_field('npc_bytes','npc_bytes',0x18)
                if label not in self.called:self.calls.append((helper,label));self.called.add(label)
                if label not in self.normal:
                    receipt=o.normal_returns.get(label)
                    if receipt is not None and type(receipt) is not bool:raise ValueError('Normalized normal-return receipt required')
                    if receipt is not True:raise Missing((label,))
                    self.normal.add(label)
                if label=='selection' and self.selected<0:self.phase=len(self.STEPS)-1;continue
                elif label=='caption':
                    if self.selected>=len(self.main_rows):return self.out('unresolved_visible_row',('visible_row',self.selected))
                    self.cache['caption']=self.main_rows[self.selected].caption
                elif label=='caption_parse':
                    if 'record_index' not in self.cache:
                        value=o.caption_parse_dword
                        if value is None:
                            if not self.owned:raise Missing(('caption_parse_dword',))
                            parsed=parse_rtl_integer32(self.cache['caption'])
                            if not parsed.accepted:return self.out('needs_native_StrToInt_exception_path',('caption',parsed.code))
                            value=parsed.dword
                        self.cache['record_index']=dword(value)
                elif label=='level_format':
                    if 'level_unicode' not in self.cache:
                        value=o.level_unicode
                        if value is None:
                            if not self.owned:raise Missing(('level_unicode',))
                            raw=self.cache['level_dword'];value=str(raw if raw<0x80000000 else raw-0x100000000)
                        if type(value) is not str:raise ValueError('Explicit Unicode level text required')
                        self.cache['level_unicode']=value
                elif label in ('header0_get','header1_get'):
                    index=int(label[6])
                    if len(self.state.headings)<=index:return self.out('unresolved_owned_column',('column',index))
                elif label in ('header0_set','header1_set'):
                    headings=list(self.state.headings);index=int(label[6])
                    headings[index]='Level : '+self.cache['level_unicode'] if index==0 else self.cache['display']
                    self.write(headings=tuple(headings))
                elif label=='display_convert':unicode_value('display',self.cache['display_bytes'])
                elif label=='npc_convert':unicode_value('npc',self.cache['npc_bytes'])
                elif label=='task_convert':unicode_value('task',b'G\xf6rev')
                elif label=='reward_convert':unicode_value('reward',b'\xd6d\xfcl')
                elif label=='details_clear':self.write(rows=())
                elif label.endswith('_add'):
                    role=label.split('_')[0];self.row_indices[role]=len(self.state.rows);self.write(rows=self.state.rows+(QuestRow(),))
                elif label.endswith('_caption_set'):
                    role=label.split('_')[0];index=self.row_indices[role];rows=list(self.state.rows)
                    rows[index]=QuestRow('NPC:' if role=='npc' else '-',rows[index].subitems);self.write(rows=tuple(rows))
                elif label.endswith('_subitem'):
                    role=label.split('_')[0];index=self.row_indices[role];rows=list(self.state.rows);old=rows[index]
                    rows[index]=QuestRow(old.caption,old.subitems+(self.cache[role],));self.write(rows=tuple(rows))
                self.phase+=1
            return self.out('no_selection' if self.selected<0 else 'locally_showing_details',complete=True)
        except Missing as error:return self.out('needs_observation',error.args[0])
