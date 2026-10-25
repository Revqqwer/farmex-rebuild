"""Scoped CFG load/probe caller plans; no filesystem or native execution."""
from dataclasses import dataclass
from source_unicode import utf16_key

def _normal(v):
    if v is not None and type(v) is not bool:raise ValueError('Separate normal-return receipt required')
def _rows(v):
    if v is not None:
        if type(v) is not tuple:raise ValueError('Exact immutable Unicode rows required')
        for text in v:utf16_key(text)

@dataclass(frozen=True)
class NameCfgLoadObservation:
    path_copy_returned:object=None
    clear_returned:object=None
    fopen_returned:object=None
    fopen_pointer_dword:object=None
    fclose_returned:object=None
    probe_helper_returned:object=None
    path_conversion_returned:object=None
    load_returned:object=None
    loaded_rows:object=None
    unicode_cleanup_returned:object=None
    path_cleanup_returned:object=None
    def __post_init__(self):
        for v in (self.path_copy_returned,self.clear_returned,self.fopen_returned,self.fclose_returned,self.probe_helper_returned,
                  self.path_conversion_returned,self.load_returned,self.unicode_cleanup_returned,self.path_cleanup_returned):_normal(v)
        v=self.fopen_pointer_dword
        if v is not None and (type(v) is not int or not 0<=v<1<<32):raise ValueError('Raw fopen FILE pointer DWORD required')
        _rows(self.loaded_rows)

@dataclass(frozen=True)
class NameCfgLoadPlan:
    complete:bool
    status:str
    entry:tuple
    state:tuple
    prospective:object=None
    probe_al:object=None
    steps:tuple=()
    missing:str=''
    native_execution_verified:bool=False

def plan_name_cfg_load(rows,o):
    _rows(rows)
    if rows is None or not isinstance(o,NameCfgLoadObservation):raise ValueError('Known rows and typed CFG observation required')
    steps=[];prospective=None;al=None
    class Missing(Exception):pass
    def need(v,label):
        if v is None:raise Missing(label)
        return v
    def normal(v,label):
        steps.append(('normal_return',label))
        if v is not True:raise Missing(label)
    def result(complete,status,missing=''):
        return NameCfgLoadPlan(complete,status,rows,prospective if complete else rows,prospective,al,tuple(steps),missing)
    try:
        normal(o.path_copy_returned,'00504ef8 ANSI path copy')
        normal(o.clear_returned,'TCustomListBox.Clear virtual13c')
        prospective=()
        steps.append(('_fopen','r'))
        normal(o.fopen_returned,'_fopen normal return')
        pointer=need(o.fopen_pointer_dword,'_fopen FILE pointer')
        if pointer:
            steps.append(('_fclose',pointer))
            # Source ignores the integer fclose result and writes AL1 after it.
            normal(o.fclose_returned,'_fclose normal return (integer result ignored)');al=1
        else:al=0
        normal(o.probe_helper_returned,'0045e754 independent normal return')
        if al:
            normal(o.path_conversion_returned,'00403d84 ANSI path to Unicode')
            normal(o.load_returned,'TStrings.LoadFromFile virtual6c')
            prospective=need(o.loaded_rows,'observed post-load Unicode rows')
            normal(o.unicode_cleanup_returned,'loaded path Unicode cleanup')
        normal(o.path_cleanup_returned,'final ANSI path cleanup')
        return result(True,'loaded_rows_modeled' if al else 'unreadable_after_clear')
    except Missing as e:return result(False,'needs_observation',str(e))
