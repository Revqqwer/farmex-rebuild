"""Richard004eebf4 per-item selection; metadata/lookups remain observations."""
from dataclasses import dataclass
from typing import Optional,Tuple


@dataclass(frozen=True)
class SellFilterObservation:
    mode: int
    excluded_4e7c60: Optional[bool] = None
    excluded_index_4e7be8: Optional[int] = None
    protect_grade_5622cf: Optional[bool] = None
    minimum_grade_5622d0: Optional[int] = None
    extension_id: Optional[int] = None
    type_byte: Optional[int] = None
    list_index_41a5cc: Optional[int] = None
    list_checked_5622e1: Optional[bool] = None
    mode2_index_47677c: Optional[int] = None
    mode2_checked: Optional[bool] = None

    def __post_init__(self):
        for value in (self.mode,self.extension_id,self.minimum_grade_5622d0):
            if value is not None and (type(value) is not int or not 0<=value<=0xffffffff):raise ValueError('Raw DWORD required')
        if self.mode is None:raise ValueError('Observed mode required')
        for value in (self.excluded_index_4e7be8,self.list_index_41a5cc,self.mode2_index_47677c):
            if value is not None and (type(value) is not int or not -0x80000000<=value<0x80000000):raise ValueError('Signed lookup index required')
        for value in (self.type_byte,):
            if value is not None and (type(value) is not int or not 0<=value<=255):raise ValueError('Observed BYTE required')
        for value in (self.excluded_4e7c60,self.protect_grade_5622cf,self.list_checked_5622e1,self.mode2_checked):
            if value is not None and type(value) is not bool:raise ValueError('Observed bool or unknown required')


@dataclass(frozen=True)
class SellFilterDecision:
    status: str
    reason: str = ''
    calls: Tuple[str,...] = ()


class _Missing(Exception):pass


def select_sale_item(observation):
    if not isinstance(observation,SellFilterObservation):raise ValueError('Typed sale selection observation required')
    calls=[]
    def need(value,label):
        if value is None:raise _Missing(label)
        return value
    def result(status,reason):return SellFilterDecision(status,reason,tuple(calls))
    try:
        if observation.mode==2:
            calls.append('0047677c')
            if need(observation.mode2_index_47677c,'0047677c name index')<0:return result('skip','mode2 name absent')
            if need(observation.mode2_checked,'mode2 row+6 checked'):return result('selected','mode2 checked name')
            return result('skip','mode2 row unchecked')
        calls.append('004e7c60')
        if need(observation.excluded_4e7c60,'004e7c60 exclusion'):return result('skip','excluded4e7c60')
        calls.append('004e7be8')
        if need(observation.excluded_index_4e7be8,'004e7be8 exclusion index')!=-1:
            return result('skip','excluded4e7be8')
        if need(observation.protect_grade_5622cf,'grade protection enabled'):
            minimum=need(observation.minimum_grade_5622d0,'minimum grade')
            grade=need(observation.extension_id,'extension ID')%10
            if minimum<=grade and need(observation.type_byte,'type BYTE')!=3:
                return result('skip','protected grade')
        calls.append('0041a5cc')
        if need(observation.list_index_41a5cc,'0041a5cc list index')<1:return result('skip','list index below1')
        if need(observation.list_checked_5622e1,'row+5622e1 checked'):return result('selected','checked list row')
        return result('skip','list row unchecked')
    except _Missing as exc:return result('needs_observation',str(exc))
