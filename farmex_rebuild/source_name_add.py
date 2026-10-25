"""0042400c/00424180 normal add-text caller; separate fresh reads and spans."""
from dataclasses import dataclass
from source_name_lists import NameListRefreshPlan
from source_unicode import utf16_key
from source_ui_name_scan import UiNameScanPlan

@dataclass(frozen=True)
class NameAddObservation:
    nonempty_span_returned:object=None
    nonempty_al:object=None
    duplicate_span_returned:object=None
    duplicate_al:object=None
    append_getter_returned:object=None
    append_text:object=None
    append_cleanup_span_returned:object=None
    refresh_execution:object=None
    refresh_returned:object=None
    duplicate_execution:object=None
    duplicate_input_ansi:object=None
    def __post_init__(self):
        for v in (self.nonempty_span_returned,self.duplicate_span_returned,self.append_getter_returned,
                  self.append_cleanup_span_returned,self.refresh_returned):
            if v is not None and type(v) is not bool:raise ValueError('Separate normal span receipt required')
        for v in (self.nonempty_al,self.duplicate_al):
            if v is not None and (type(v) is not int or v not in (0,1)):raise ValueError('Normalized source boolean AL required')
        if self.append_text is not None:utf16_key(self.append_text)
        if self.refresh_execution is not None and not isinstance(self.refresh_execution,NameListRefreshPlan):raise ValueError('Typed refresh execution required')
        if self.duplicate_execution is not None and not isinstance(self.duplicate_execution,UiNameScanPlan):raise ValueError('Typed duplicate scan plan required')
        if self.duplicate_input_ansi is not None and type(self.duplicate_input_ansi) is not bytes:raise ValueError('Exact second-getter ANSI input required')

@dataclass(frozen=True)
class NameAddPlan:
    complete:bool
    status:str
    kind:str
    entry:tuple
    state:tuple
    prospective:tuple
    append_text:object=None
    steps:tuple=()
    refresh_execution:object=None
    missing:str=''
    native_execution_verified:bool=False
    duplicate_execution:object=None

def plan_name_add(kind,rows,o):
    if kind not in ('white','black') or not isinstance(o,NameAddObservation):raise ValueError('Known list and typed add observation required')
    if type(rows) is not tuple:raise ValueError('Own immutable Unicode rows required')
    for text in rows:utf16_key(text)
    prospective=rows;steps=[];text=None;bound=None;duplicate=None
    class Missing(Exception):pass
    def need(v,label):
        if v is None:raise Missing(label)
        return v
    def normal(v,label):
        steps.append(('normal_return',label))
        if v is not True:raise Missing(label)
    def result(complete,status,missing=''):
        return NameAddPlan(complete,status,kind,rows,prospective if complete else rows,prospective,text,tuple(steps),bound,missing,duplicate_execution=duplicate)
    try:
        normal(o.nonempty_span_returned,'first fresh getter/00505d4c/temporary cleanups')
        if need(o.nonempty_al,'source nonempty AL')==0:return result(True,'empty_input_skipped')
        normal(o.duplicate_span_returned,'second fresh getter/ANSI conversion/0046601c/temporary cleanups')
        duplicate=o.duplicate_execution
        if duplicate is not None:
            if o.duplicate_al is not None:raise ValueError('Bound duplicate scan conflicts with raw AL')
            ansi=need(o.duplicate_input_ansi,'second getter post-conversion ANSI bytes')
            if duplicate.input_ansi_bytes is None or duplicate.input_ansi_bytes!=ansi:raise ValueError('Bound duplicate scan input mismatch')
            if not duplicate.complete:raise Missing('bound duplicate scan: '+duplicate.missing)
            duplicate_al=need(duplicate.al,'bound duplicate AL')
        else:duplicate_al=need(o.duplicate_al,'source duplicate-helper AL')
        if duplicate_al!=0:return result(True,'duplicate_skipped')
        normal(o.append_getter_returned,'third fresh Unicode getter')
        text=need(o.append_text,'third fresh append Unicode text')
        # It need not equal either earlier getter, or even remain nonempty.
        steps.append(('virtual_add',kind,0x3c,text))
        normal(o.append_cleanup_span_returned,'virtual Add and temporary Unicode cleanup')
        prospective=rows+(text,)
        steps.append(('0046c3b8',))
        bound=o.refresh_execution
        if bound is not None and not bound.complete:raise Missing('bound refresh: '+bound.missing)
        normal(o.refresh_returned,'0046c3b8 independent normal return')
        return result(True,'append_refresh_modeled')
    except Missing as e:return result(False,'needs_observation',str(e))
