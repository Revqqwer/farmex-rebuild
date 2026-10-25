"""Captured 004d540c continuation into owned rows; no VCL/native execution."""
from dataclasses import dataclass,field
from collections.abc import Mapping
from name_codec import WindowsNameCodec
from quest_collection import dword


@dataclass(frozen=True)
class QuestRow:
    caption:str=''
    subitems:tuple=()


@dataclass
class QuestRowSink:
    rows:tuple=()
    revision:int=0


@dataclass(frozen=True)
class QuestRowObservation:
    normal_returns:object=field(default_factory=dict)
    code_page:object=None


@dataclass(frozen=True)
class QuestRowPlan:
    complete:bool
    status:str
    row_index:object=None
    needed:object=None
    calls:tuple=()
    native_execution_verified:bool=False
    live_compatibility_verified:bool=False


class QuestRowFrame:
    # Each receipt is a distinct reached call, including three independent
    # Unicode cleanups. A helper result alone is not its normal-return proof.
    STEPS=(('parameter_copy','00504ef8'),('row_add','00506ba2'),
           ('index_format','005063a6'),('caption_set','00506bae'),
           ('caption_cleanup','00505c64'),('level_format','005063a6'),
           ('level_add','SubItems.Add'),('level_cleanup','00505c64'),
           ('display_convert','00403d84'),('display_add','SubItems.Add'),
           ('display_cleanup','00505c64'),('parameter_cleanup','004040f8'),
           ('epilogue','004d540c normal return'))

    def __init__(self,sink,collection_index,minimum_level,display_ansi):
        if not isinstance(sink,QuestRowSink) or type(sink.rows) is not tuple:
            raise ValueError('Owned row sink required')
        if any(not isinstance(r,QuestRow) for r in sink.rows):raise ValueError('Typed rows required')
        self.index=dword(collection_index)
        if type(minimum_level) is not int or not 0<=minimum_level<=255:
            raise ValueError('Fresh zero-extended minimum-level byte required')
        if type(display_ansi) is not bytes:raise ValueError('Immutable display ANSI bytes required')
        self.level=minimum_level;self.display=display_ansi;self.sink=sink
        self.expected=sink.rows;self.revision=sink.revision;self.row_index=None
        self.phase=0;self.normal=set();self.called=set();self.calls=[];self.text={};self.final=None

    def out(self,status,needed=None,complete=False):
        plan=QuestRowPlan(complete,status,self.row_index,needed,tuple(self.calls))
        if complete:self.final=plan
        return plan

    def write(self,row=None):
        rows=list(self.expected)
        if row is None:
            self.row_index=len(rows);rows.append(QuestRow())
        else:rows[self.row_index]=row
        self.sink.rows=tuple(rows);self.sink.revision+=1
        self.expected=self.sink.rows;self.revision=self.sink.revision

    def advance(self,observation=None):
        if self.final is not None:return self.final
        o=QuestRowObservation() if observation is None else observation
        if not isinstance(o,QuestRowObservation) or not isinstance(o.normal_returns,Mapping):
            raise ValueError('Typed row observation and normal-return mapping required')
        if self.sink.rows!=self.expected or self.sink.revision!=self.revision:
            return self.out('row_sink_conflict')
        while self.phase<len(self.STEPS):
            label,helper=self.STEPS[self.phase]
            if label not in self.called:self.calls.append((helper,label));self.called.add(label)
            if label not in self.normal:
                receipt=o.normal_returns.get(label)
                if receipt is not None and type(receipt) is not bool:
                    raise ValueError('Explicit normalized normal-return receipt required')
                if receipt is not True:return self.out('needs_observation',(label,))
                self.normal.add(label)
            if label=='row_add':self.write()
            elif label=='index_format':
                signed=self.index if self.index<0x80000000 else self.index-0x100000000
                self.text['index']=str(signed)
            elif label=='caption_set':
                self.write(QuestRow(self.text['index'],self.expected[self.row_index].subitems))
            elif label=='level_format':self.text['level']=str(self.level)
            elif label=='display_convert':
                if 'display' not in self.text:
                    if not self.display:self.text['display']=''
                    elif o.code_page is None:return self.out('needs_observation',('code_page',))
                    else:self.text['display']=WindowsNameCodec(o.code_page).decode(self.display)
            elif label in ('level_add','display_add'):
                old=self.expected[self.row_index]
                self.write(QuestRow(old.caption,old.subitems+(self.text[label.split('_')[0]],)))
            self.phase+=1
        return self.out('locally_emitted_row',complete=True)
