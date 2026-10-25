"""00423d5c/00423eb4 target-add normal caller composition; no native IO."""
from dataclasses import dataclass
from source_target_name import TargetIdPlan,NameByIndexPlan
from source_ui_name_scan import UiNameScanPlan
from source_name_lists import NameListRefreshPlan
from source_unicode import utf16_key

@dataclass(frozen=True)
class TargetAddObservation:
    target_ids:tuple=()
    target_id_executions:tuple=()
    target_id_returned:tuple=()
    invalid_alert_span_returned:object=None
    name_ansi_bytes:object=None
    name_execution:object=None
    name_returned:object=None
    duplicate_al:object=None
    duplicate_execution:object=None
    duplicate_returned:object=None
    append_unicode_text:object=None
    append_span_returned:object=None
    refresh_execution:object=None
    refresh_returned:object=None
    name_cleanup_returned:object=None
    def __post_init__(self):
        for v in (self.target_ids,self.target_id_executions,self.target_id_returned):
            if type(v) is not tuple:raise ValueError('Ordered immutable target call observations required')
        for v in self.target_ids:
            if v is not None and (type(v) is not int or not 0<=v<1<<32):raise ValueError('Raw target DWORD required')
        if any(v is not None and not isinstance(v,TargetIdPlan) for v in self.target_id_executions):raise ValueError('Typed target reader plans required')
        for v in self.target_id_returned+(self.invalid_alert_span_returned,self.name_returned,self.duplicate_returned,
                self.append_span_returned,self.refresh_returned,self.name_cleanup_returned):
            if v is not None and type(v) is not bool:raise ValueError('Explicit normal helper/span return required')
        if self.name_ansi_bytes is not None and type(self.name_ansi_bytes) is not bytes:raise ValueError('Exact output ANSI name required')
        if self.name_execution is not None and not isinstance(self.name_execution,NameByIndexPlan):raise ValueError('Typed name-by-index plan required')
        if self.duplicate_al is not None and (type(self.duplicate_al) is not int or self.duplicate_al not in (0,1)):raise ValueError('Normalized duplicate AL required')
        if self.duplicate_execution is not None and not isinstance(self.duplicate_execution,UiNameScanPlan):raise ValueError('Typed UI scan plan required')
        if self.append_unicode_text is not None:utf16_key(self.append_unicode_text)
        if self.refresh_execution is not None and not isinstance(self.refresh_execution,NameListRefreshPlan):raise ValueError('Typed refresh plan required')

@dataclass(frozen=True)
class TargetAddPlan:
    complete:bool
    status:str
    kind:str
    entry:tuple
    state:tuple
    prospective:tuple
    target_samples:tuple=()
    steps:tuple=()
    target_plans:tuple=()
    name_plan:object=None
    duplicate_plan:object=None
    refresh_plan:object=None
    missing:str=''
    native_execution_verified:bool=False

def plan_target_add(kind,rows,o):
    if kind not in ('white','black') or not isinstance(o,TargetAddObservation):raise ValueError('Known list and typed target-add observation required')
    if type(rows) is not tuple:raise ValueError('Own immutable Unicode list required')
    for text in rows:utf16_key(text)
    prospective=rows;steps=[];targets=[];readers=[];name_plan=None;duplicate_plan=None;refresh_plan=None
    class Missing(Exception):pass
    def need(v,label):
        if v is None:raise Missing(label)
        return v
    def normal(v,label):
        steps.append(('normal_return',label))
        if v is not True:raise Missing(label)
    def result(complete,status,missing=''):
        return TargetAddPlan(complete,status,kind,rows,prospective if complete else rows,prospective,
            tuple(targets),tuple(steps),tuple(readers),name_plan,duplicate_plan,refresh_plan,missing)
    def target(index):
        steps.append(('00462630',index))
        raw=o.target_ids[index] if index<len(o.target_ids) else None
        bound=o.target_id_executions[index] if index<len(o.target_id_executions) else None
        if bound is not None:
            readers.append((index,bound))
            if raw is not None:raise ValueError('Bound target reader conflicts with raw same-call DWORD')
            if not bound.complete:raise Missing('bound target reader: '+bound.missing)
            normal(o.target_id_returned[index] if index<len(o.target_id_returned) else None,'00462630 bound call%d normal return'%index)
            raw=bound.target_id_dword
        value=need(raw,'fresh target DWORD call%d'%index);targets.append(value)
        return value
    try:
        first=target(0)
        valid=first!=0
        if valid:valid=target(1)<=3000
        if not valid:
            steps.append(('00464d10','Secili Hedef Bulunamadi !','Listeye eklemek icin hedef seciniz !'))
            normal(o.invalid_alert_span_returned,'invalid-target notice/string cleanup span')
            return result(True,'invalid_target_no_add')
        index=target(2);steps.append(('00466144',index))
        name_plan=o.name_execution;ansi=o.name_ansi_bytes
        if name_plan is not None:
            if ansi is not None:raise ValueError('Bound name reader conflicts with raw ANSI output')
            if name_plan.index_dword!=index:raise ValueError('Bound name index must match third fresh target sample')
            if not name_plan.complete:raise Missing('bound name reader: '+name_plan.missing)
            ansi=name_plan.ansi_bytes
        normal(o.name_returned,'00466144 independent normal return')
        ansi=need(ansi,'name helper output ANSI bytes')
        # No empty-name guard exists between source name helper and duplicate scan.
        steps.append(('0046601c',kind,ansi));duplicate_plan=o.duplicate_execution
        if duplicate_plan is not None:
            if o.duplicate_al is not None:raise ValueError('Bound duplicate scan conflicts with raw AL')
            if duplicate_plan.input_ansi_bytes is None or duplicate_plan.input_ansi_bytes!=ansi:raise ValueError('Duplicate scan must use captured helper output ANSI name')
            if not duplicate_plan.complete:raise Missing('bound duplicate scan: '+duplicate_plan.missing)
            al=need(duplicate_plan.al,'bound duplicate AL')
        else:al=need(o.duplicate_al,'source duplicate AL')
        normal(o.duplicate_returned,'0046601c independent normal return')
        if al:
            normal(o.name_cleanup_returned,'final local ANSI name cleanup')
            return result(True,'target_duplicate_skipped')
        text=need(o.append_unicode_text,'separate ANSI-to-Unicode append text')
        steps.append(('00403d84/virtual_Add',kind,0x3c,text))
        normal(o.append_span_returned,'append conversion/Add/temporary cleanup span')
        prospective=rows+(text,)
        steps.append(('0046c3b8',));refresh_plan=o.refresh_execution
        if refresh_plan is not None and not refresh_plan.complete:raise Missing('bound refresh: '+refresh_plan.missing)
        normal(o.refresh_returned,'0046c3b8 independent normal return')
        normal(o.name_cleanup_returned,'final local ANSI name cleanup')
        return result(True,'target_append_refresh_modeled')
    except Missing as e:return result(False,'needs_observation',str(e))
