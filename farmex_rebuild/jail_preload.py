"""0045b7d8 saved window preload plans; no Windows/VCL or remote memory calls."""
from dataclasses import dataclass
from jail_protection import JailObservation, source_vector_count

MASK=0xffffffff

@dataclass(frozen=True)
class JailPreloadPlan:
    complete: bool
    reads: tuple=()
    calls: tuple=()
    ui_intents: tuple=()
    needed: object=None
    iterations: int=0
    whole_function_verified: bool=False
    native_execution_verified: bool=False
    live_compatibility_verified: bool=False

class JailPreloadFrame:
    """Consume only reached raw observations; retain earlier UI intents on gaps.

    Kernel API tuples use physical PUSH order. Imported Delphi/virtual methods
    record labelled arguments, not an assumed native callable ABI. VCL object
    chain reads and temporary string spans remain opaque normal receipts.
    """
    def __init__(self):
        self.reads=[];self.calls=[];self.ui=[];self.iterations=0
        self.values={};self.normals={};self.final=None
        self._flow=self._run();self._needed=next(self._flow)

    def _value(self,label):return (yield ('value',label))
    def _read(self,label,address):
        self.reads.append((address&MASK,4,label))
        return (yield from self._value(label))
    def _call(self,label,helper,args=()):
        self.calls.append((helper,args,label));yield ('normal',label)

    def _run(self):
        yield ('entry','0045b7d8')
        yield from self._call('prologue','source_SEH_prologue_span')
        yield from self._call('list_reset','captured_form_list_virtual_13c')
        self.ui.append(('virtual_reset_returned',)) #Does not claim Clear succeeded.
        yield from self._call('scratch_init','00404148',('scratch_ansi',))
        index=0
        while True:
            p='row%d.'%index
            first=yield from self._read(p+'count_initial_begin',0x5691c8)
            count=0
            if first:
                end=yield from self._read(p+'count_end',0x5691cc)
                begin=yield from self._read(p+'count_sub_begin',0x5691c8)
                count=source_vector_count(end,begin)
            if count<=index:break
            yield from self._call(p+'add','captured_form_items_TListItems.Add')
            item=yield from self._value(p+'item_eax')
            self.ui.append(('item_added',item))
            begin=yield from self._read(p+'element_begin',0x5691c8)
            address=(begin+index*4)&MASK
            yield from self._call(p+'string_assign','005050e4',(address,'scratch_ansi'))
            yield from self._call(p+'caption_convert','00403d84',('scratch_ansi','caption_temp'))
            converted=yield from self._value(p+'caption_convert_eax')
            caption=yield from self._read(p+'caption_unicode_pointer',converted)
            yield from self._call(p+'caption','TListItem.SetCaption',(('EAX',item),('EDX',caption)))
            self.ui.append(('caption_set',item,caption))
            yield from self._call(p+'caption_cleanup','00505c64',(2,'caption_temp'))
            yield from self._call(p+'checked','TListItem.SetChecked',(('EAX',item),('DL',1)))
            self.ui.append(('checked_set',item,1))
            title=yield from self._value(p+'title_pointer')
            yield from self._call(p+'find_window','FindWindowA',(title or 0x522210,0))
            hwnd=yield from self._value(p+'hwnd')
            if hwnd:
                yield from self._call(p+'pid','GetWindowThreadProcessId',('local_pid',hwnd))
                pid=yield from self._value(p+'pid_dword')
                # No PID-zero guard between these source calls.
                yield from self._call(p+'open','OpenProcess',(pid,0,0x1fffff))
                handle=yield from self._value(p+'handle')
                if handle:
                    slot=yield from self._read(p+'root_slot',0x553e7c)
                    yield from self._call(p+'root_read','0045db9c',(slot,handle))
                    root=yield from self._value(p+'root_eax')
                    offset=yield from self._read(p+'size_offset',0x553fec)
                    yield from self._call(p+'size_read','0045db9c',((root+offset)&MASK,handle))
                    length=yield from self._value(p+'size_eax')
                    offset=yield from self._read(p+'pointer_offset',0x553fe8)
                    yield from self._call(p+'pointer_read','0045db9c',((root+offset)&MASK,handle))
                    pointer=yield from self._value(p+'pointer_eax')
                    yield from self._call(p+'name_init','00505bb8',(0x522211,'name_unicode'))
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
                else:
                    yield from self._call(p+'failure_text','00505bb8',(0x522212,'failure_unicode'))
                    yield from self._call(p+'failure_subitem','captured_item_plus8_virtual_3c',(('item',item),('literal',b' - ')))
                    self.ui.append(('subitem_literal_returned',item,b' - '))
                    yield from self._call(p+'failure_cleanup','00505c64',(2,'failure_unicode'))
            self.iterations+=1;index=(index+1)&MASK
        yield from self._call('final_cleanup','004040f8',(2,'scratch_ansi'))
        yield from self._call('epilogue','source_FS_restore_stack_return_span')

    def _plan(self,complete=False):
        return JailPreloadPlan(complete,tuple(self.reads),tuple(self.calls),tuple(self.ui),
                               None if complete else self._needed,self.iterations)

    def advance(self,o):
        if not isinstance(o,JailObservation):raise ValueError('Typed raw preload observations required')
        if self.final is not None:return self.final
        while True:
            kind,label=self._needed
            if kind=='entry':
                if not o.entry_reached:return self._plan()
                value=True
            elif kind=='normal':
                if o.normal_returns.get(label) is not True:return self._plan()
                value=True;self.normals[label]=True
            else:
                if label not in o.values:return self._plan()
                value=o.values[label];self.values[label]=value
            try:self._needed=self._flow.send(value)
            except StopIteration:
                self.final=self._plan(True);return self.final
