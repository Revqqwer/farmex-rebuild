"""00466dc4 time scalar and004632b4 identity-helper observation projection.

No current clock, process read, guessed character name, or implicit codec.
"""
from dataclasses import dataclass,field
from types import MappingProxyType
from merchant_result_filter import raw


def signed(v):return v if v<0x80000000 else v-0x100000000


def build_source_time_fragment(tm_dwords):
    """Nine captured DWORDs copied from CRT localtime; no calendar correction.

    Source uses raw tm_mon, not tm_mon+1, and adds1900 to tm_year with DWORD
    wrap. Every component uses signed%i without padding. Time zone is external.
    """
    if type(tm_dwords) is not tuple or len(tm_dwords)!=9:raise ValueError('Nine explicit localtime DWORDs required')
    for v in tm_dwords:raw(v,32,'localtime DWORD')
    sec,minute,hour,day,month,year=tm_dwords[:6]
    return ('%d.%d.%d  %d-%d-%d'%(signed(day),signed(month),signed((year+1900)&0xffffffff),
            signed(hour),signed(minute),signed(sec))).encode('ascii')


@dataclass(frozen=True)
class ExportIdentityObservation:
    entry_process_handle:object=None
    root_pointer_value:object=None
    storage_offset:object=None
    data_offset:object=None
    owner_eax:object=None
    storage_eax:object=None
    data_eax:object=None
    fresh_inline_data_offset:object=None
    copied_ansi:object=None
    converted_unicode:object=None
    final_ansi:object=None
    normal_returns:object=field(default_factory=dict)
    def __post_init__(self):
        for value in (self.entry_process_handle,self.root_pointer_value,self.storage_offset,self.data_offset,
                      self.owner_eax,self.storage_eax,self.data_eax,self.fresh_inline_data_offset):
            if value is not None:raw(value,32,'identity DWORD')
        for value in (self.copied_ansi,self.final_ansi):
            if value is not None and type(value) is not bytes:raise ValueError('Explicit ANSI output required')
        if self.converted_unicode is not None and type(self.converted_unicode) is not str:
            raise ValueError('Explicit Unicode conversion output required')
        n=dict(self.normal_returns)
        if any(type(v) is not bool for v in n.values()):raise ValueError('Independent normal-return receipts required')
        object.__setattr__(self,'normal_returns',MappingProxyType(n))


@dataclass(frozen=True)
class ExportIdentityPlan:
    complete:bool
    status:str
    ansi_result:object=None
    copy_address:object=None
    copy_count:object=None
    steps:tuple=()
    needed:object=None
    native_execution_verified:bool=False
    live_compatibility_verified:bool=False


class _Missing(Exception):
    def __init__(self,kind,label):self.needed=(kind,label)


def plan_export_identity(o=None):
    o=ExportIdentityObservation() if o is None else o
    if not isinstance(o,ExportIdentityObservation):raise ValueError('Typed identity observations required')
    steps=[];address=None;count=None;result=None
    def value(name):
        v=getattr(o,name)
        if v is None:raise _Missing('value',name)
        return v
    def normal(name):
        steps.append(('normal',name))
        if o.normal_returns.get(name) is not True:raise _Missing('normal',name)
    def finish(ok,needed=None):
        return ExportIdentityPlan(ok,'own_identity_projected' if ok else 'needs_observation',
                                  result,address,count,tuple(steps),needed)
    try:
        normal('entry_process');value('entry_process_handle') # GetCurrentProcess, result unused.
        root=value('root_pointer_value');steps.append(('read32','owner',root))
        normal('owner');owner=value('owner_eax')
        at=(owner+value('storage_offset'))&0xffffffff;steps.append(('read32','storage',at))
        normal('storage');storage=value('storage_eax')
        at=(owner+value('data_offset'))&0xffffffff;steps.append(('read32','data',at))
        normal('data');pointer=value('data_eax') # Source reads this even for inline.
        if storage>=16:address=pointer;count=storage
        else:address=(owner+value('fresh_inline_data_offset'))&0xffffffff;count=255
        steps.append(('copy_0045dca8',address,count));normal('copy');value('copied_ansi')
        normal('copy_to_unicode');value('converted_unicode')
        normal('copy_cleanup')
        normal('unicode_to_ansi');encoded=value('final_ansi')
        normal('assign');result=encoded
        normal('result_cleanup');normal('unicode_cleanup')
        return finish(True)
    except _Missing as e:return finish(False,e.needed)
