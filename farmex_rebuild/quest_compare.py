"""Quest OnCompare scalar result and cleanup continuation, not native sorting."""
from dataclasses import dataclass,field
from collections.abc import Mapping
from quest_row import QuestRow
from quest_collection import dword
from rtl_integer32 import parse_rtl_integer32
from merchant_result_compare import plan_merchant_alpha_sort


@dataclass(frozen=True)
class QuestCompareObservation:
    normal_returns:object=field(default_factory=dict)
    first_parse_dword:object=None
    second_parse_dword:object=None


@dataclass(frozen=True)
class QuestComparePlan:
    complete:bool
    status:str
    result_dword:object=None
    result_written:bool=False
    needed:object=None
    calls:tuple=()
    native_execution_verified:bool=False
    sorting_verified:bool=False

    @property
    def signed_result(self):
        v=self.result_dword
        return None if v is None else v if v<0x80000000 else v-0x100000000


class QuestCompareFrame:
    STEPS=(('first_text_span','SubItems.Strings[0]'),('first_parse','0050638e'),
           ('second_text_span','SubItems.Strings[0]'),('second_parse','0050638e'),
           ('write_result',None),('second_cleanup','00505c64'),
           ('first_cleanup','00505c64'),('epilogue','004b4940 normal return'))

    def __init__(self,first,second,previous_result=None,*,use_owned_integer_model=False):
        if not isinstance(first,QuestRow) or not isinstance(second,QuestRow):raise ValueError('Typed immutable rows required')
        if type(use_owned_integer_model) is not bool:raise ValueError('Explicit integer model selection required')
        if previous_result is not None:dword(previous_result)
        self.rows={'first':first,'second':second};self.owned=use_owned_integer_model
        self.result=previous_result;self.written=False;self.phase=0
        self.normal=set();self.called=set();self.calls=[];self.values={};self.text={};self.final=None

    def out(self,status,needed=None,complete=False):
        p=QuestComparePlan(complete,status,self.result,self.written,needed,tuple(self.calls))
        if complete:self.final=p
        return p

    def advance(self,observation=None):
        if self.final is not None:return self.final
        o=QuestCompareObservation() if observation is None else observation
        if not isinstance(o,QuestCompareObservation) or not isinstance(o.normal_returns,Mapping):
            raise ValueError('Typed sparse comparison observations required')
        while self.phase<len(self.STEPS):
            label,helper=self.STEPS[self.phase]
            if helper is not None:
                if label not in self.called:self.calls.append((helper,label));self.called.add(label)
                if label not in self.normal:
                    receipt=o.normal_returns.get(label)
                    if receipt is not None and type(receipt) is not bool:raise ValueError('Normalized normal-return receipt required')
                    if receipt is not True:return self.out('needs_observation',(label,))
                    self.normal.add(label)
            if label.endswith('_text_span'):
                side=label.split('_')[0];row=self.rows[side]
                if not row.subitems:return self.out('needs_owned_subitem',(side,0))
                text=row.subitems[0]
                if type(text) is not str:raise ValueError('Unicode first subitem required')
                self.text[side]=text
            elif label in ('first_parse','second_parse'):
                side=label.split('_')[0]
                value=getattr(o,side+'_parse_dword')
                if value is None:
                    if not self.owned:return self.out('needs_observation',(side+'_parse_dword',))
                    parsed=parse_rtl_integer32(self.text[side])
                    if not parsed.accepted:return self.out('needs_native_StrToInt_exception_path',(side,parsed.code))
                    value=parsed.dword
                self.values[side]=dword(value)
            elif label=='write_result':
                self.result=(self.values['first']-self.values['second'])&0xffffffff;self.written=True
            self.phase+=1
        return self.out('comparison_returned',complete=True)


def plan_quest_alpha_sort(handle_allocated=None,hwnd=None,message_result=None):
    """Same pinned VCL import as Merchant; returns a request plan, never sorts."""
    return plan_merchant_alpha_sort(handle_allocated,hwnd,message_result)


@dataclass(frozen=True)
class QuestOwnedSortPlan:
    complete:bool
    status:str
    rows:object=None
    permutation:object=None
    needed:object=None
    tie_policy:str='own stable input order; native equal-level order unverified'
    native_execution_verified:bool=False
    sorting_verified:bool=False


def sort_quest_rows_owned(rows):
    """Useful independent-version sort on producer's BYTE-level domain only.

    Outside 0..255 the source DWORD subtraction may overflow or cease being
    transitive. Do not substitute Python's unbounded integer order there.
    This function makes no native call and does not satisfy a normal receipt.
    """
    if type(rows) is not tuple or any(not isinstance(r,QuestRow) for r in rows):
        raise ValueError('Immutable tuple of typed Quest rows required')
    levels=[]
    for i,row in enumerate(rows):
        if not row.subitems:return QuestOwnedSortPlan(False,'needs_subitem',needed=(i,0))
        parsed=parse_rtl_integer32(row.subitems[0])
        if not parsed.accepted:return QuestOwnedSortPlan(False,'needs_native_StrToInt_exception_path',needed=(i,parsed.code))
        if not 0<=parsed.signed<=255:return QuestOwnedSortPlan(False,'outside_producer_level_domain',needed=(i,parsed.dword))
        levels.append(parsed.signed)
    permutation=tuple(sorted(range(len(rows)),key=levels.__getitem__))
    return QuestOwnedSortPlan(True,'own_stable_level_order',tuple(rows[i] for i in permutation),permutation)
