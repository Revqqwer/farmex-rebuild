"""Bounded0045bac8 discovery continuation and typed0045bab0 refresh composition."""
from dataclasses import dataclass,field,replace
from jail_protection import JailObservation
from jail_preload import JailPreloadFrame,JailPreloadPlan,MASK

@dataclass(frozen=True)
class JailDiscoveryPlan(JailPreloadPlan):
    bounded_entry: str='0045bac8'

class JailDiscoveryFrame(JailPreloadFrame):
    """Reuse reached-only generator machinery; source entry follows preload call."""
    def _plan(self,complete=False):
        return JailDiscoveryPlan(complete,tuple(self.reads),tuple(self.calls),tuple(self.ui),
                                 None if complete else self._needed,self.iterations)

    def _run(self):
        yield ('entry','0045bac8')
        yield from self._call('initial_text','0045bac8..0045bb61_opaque_string_preparation')
        yield from self._call('snapshot','CreateToolhelp32Snapshot',(0,2))
        snapshot=yield from self._value('snapshot_handle')
        if snapshot!=MASK:
            yield from self._call('first','Process32First',('process_entry_size_0x128',snapshot))
            present=yield from self._value('first_eax')
            index=0
            while present:
                p='process%d.'%index
                yield from self._call(p+'executable','0045bbe6..0045bc45_opaque_executable_preparation')
                yield from self._call(p+'search','0041ac60',('search_length',0,'search_pointer','executable_string'))
                search=yield from self._value(p+'search_eax')
                if search!=MASK:
                    pid=yield from self._value(p+'pid')
                    yield from self._call(p+'open','OpenProcess',(pid,0,0x1fffff))
                    handle=yield from self._value(p+'handle')
                    address=yield from self._read(p+'identity_address',0x55420c)
                    yield from self._call(p+'identity_read','004604d4',(0xff,address,handle))
                    raw=yield from self._value(p+'identity_pointer')
                    yield from self._call(p+'identity_convert','00505bb8',(raw,'identity_unicode'))
                    duplicate=False;row=0
                    while True:
                        d=p+'duplicate%d.'%row
                        yield from self._call(d+'count','captured_form_items_TListItems.GetCount')
                        count=yield from self._value(d+'count_eax')
                        signed_count=count-(1<<32) if count&0x80000000 else count
                        signed_row=row-(1<<32) if row&0x80000000 else row
                        if signed_count<=signed_row:break
                        yield from self._call(d+'title','00404a78_then0045f7f4_opaque_title_getter',(row,))
                        yield from self._call(d+'compare','00505d3c',('title_unicode','identity_unicode'))
                        saved=yield from self._value(d+'compare_eax')
                        # EAX is physically saved across this cleanup in source.
                        yield from self._call(d+'cleanup','00505c64',(2,'title_unicode'))
                        if saved&255:duplicate=True;break
                        row=(row+1)&MASK
                    # This comparison is evaluated even after duplicate==True.
                    yield from self._call(p+'exclude','00505d4c',('initial_unicode','identity_unicode'))
                    excluded=yield from self._value(p+'exclude_eax')
                    if excluded&255 and not duplicate:
                        yield from self._call(p+'add','captured_form_items_TListItems.Add')
                        item=yield from self._value(p+'item_eax')
                        self.ui.append(('item_added',item))
                        caption=yield from self._value(p+'identity_unicode_pointer')
                        yield from self._call(p+'caption','TListItem.SetCaption',(('EAX',item),('EDX',caption)))
                        self.ui.append(('caption_set',item,caption))
                        # No SetChecked call exists in this discovery path.
                        slot=yield from self._read(p+'root_slot',0x553e7c)
                        yield from self._call(p+'root_read','0045db9c',(slot,handle))
                        root=yield from self._value(p+'root_eax')
                        offset=yield from self._read(p+'size_offset',0x553fec)
                        yield from self._call(p+'size_read','0045db9c',((root+offset)&MASK,handle))
                        length=yield from self._value(p+'size_eax')
                        offset=yield from self._read(p+'pointer_offset',0x553fe8)
                        yield from self._call(p+'pointer_read','0045db9c',((root+offset)&MASK,handle))
                        pointer=yield from self._value(p+'pointer_eax')
                        yield from self._call(p+'name_init','00505bb8',(0x52221c,'name_unicode'))
                        if length<16:
                            offset=yield from self._read(p+'inline_offset',0x553fe8)
                            pointer=(root+offset)&MASK
                        yield from self._call(p+'name_read','004604d4',(length,pointer,handle))
                        raw=yield from self._value(p+'name_pointer')
                        yield from self._call(p+'name_convert','00505bb8',(raw,'name_temp'))
                        yield from self._call(p+'name_assign','00505c88',('name_temp','name_unicode'))
                        yield from self._call(p+'name_temp_cleanup','00505c64',(2,'name_temp'))
                        name=yield from self._value(p+'name_unicode_pointer')
                        yield from self._call(p+'subitem','captured_item_plus8_virtual_3c',(('item',item),('EDX',name)))
                        self.ui.append(('subitem_call_returned',item,name))
                        yield from self._call(p+'name_cleanup','00505c64',(2,'name_unicode'))
                    yield from self._call(p+'identity_cleanup','00505c64',(2,'identity_unicode'))
                yield from self._call(p+'next','Process32Next',('process_entry',snapshot))
                present=yield from self._value(p+'next_eax')
                yield from self._call(p+'executable_cleanup','00403860',(0,1,'executable_string'))
                self.iterations+=1;index=(index+1)&MASK
        yield from self._call('final_cleanup','source_search_ANSI_initial_Unicode_cleanup_span')
        yield from self._call('epilogue','source_FS_restore_stack_return_span')

@dataclass(frozen=True)
class JailRefreshObservation:
    outer: JailObservation=field(default_factory=JailObservation)
    preload: JailObservation=field(default_factory=JailObservation)
    discovery: JailObservation=field(default_factory=JailObservation)
    def __post_init__(self):
        if any(not isinstance(o,JailObservation) for o in (self.outer,self.preload,self.discovery)):
            raise ValueError('Typed outer, preload and discovery observations required')

@dataclass(frozen=True)
class JailRefreshPlan:
    complete: bool
    preload: object=None
    discovery: object=None
    needed: object=None
    whole_function_verified: bool=False
    native_execution_verified: bool=False
    live_compatibility_verified: bool=False
    @property
    def ui_intents(self):
        return (() if self.preload is None else self.preload.ui_intents)+(() if self.discovery is None else self.discovery.ui_intents)

class JailRefreshFrame:
    def __init__(self):
        self.stage='entry';self.preload=None;self.discovery=None;self.final=None
        self.preload_plan=None;self.discovery_plan=None
    def _plan(self,needed):
        return JailRefreshPlan(False,self.preload_plan,self.discovery_plan,needed)
    def advance(self,o):
        if not isinstance(o,JailRefreshObservation):raise ValueError('Typed refresh observation required')
        if self.final is not None:return self.final
        if self.stage=='entry':
            if not o.outer.entry_reached:return self._plan(('entry','0045bab0'))
            self.stage='prologue'
        if self.stage=='prologue':
            if o.outer.normal_returns.get('prologue') is not True:return self._plan(('outer_normal','prologue'))
            self.preload=JailPreloadFrame();self.stage='preload'
        if self.stage=='preload':
            self.preload_plan=self.preload.advance(replace(o.preload,entry_reached=True))
            if not self.preload_plan.complete:return self._plan(('preload',self.preload_plan.needed))
            self.stage='preload_return'
        if self.stage=='preload_return':
            if o.outer.normal_returns.get('preload_return') is not True:return self._plan(('outer_normal','preload_return'))
            self.discovery=JailDiscoveryFrame();self.stage='discovery'
        self.discovery_plan=self.discovery.advance(replace(o.discovery,entry_reached=True))
        if not self.discovery_plan.complete:return self._plan(('discovery',self.discovery_plan.needed))
        self.final=JailRefreshPlan(True,self.preload_plan,self.discovery_plan)
        return self.final
