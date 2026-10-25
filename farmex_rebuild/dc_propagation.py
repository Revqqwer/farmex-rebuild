"""DC periodic gate and two normal consumer control plans; no remote operations."""
from dataclasses import dataclass,field,replace
from jail_protection import JailObservation,source_vector_count
from jail_preload import JailPreloadFrame,MASK

@dataclass(frozen=True)
class DCPlan:
    complete: bool
    kind: str
    reads: tuple=()
    calls: tuple=()
    payload_intents: tuple=()
    stores: tuple=()
    needed: object=None
    iterations: int=0
    next_address: object=None
    whole_function_verified: bool=False
    native_execution_verified: bool=False
    live_compatibility_verified: bool=False

class DCConsumerFrame(JailPreloadFrame):
    def __init__(self,kind,*,context=0x5690f8):
        if kind not in ('scan','list') or type(context) is not int or not 0<=context<=MASK:
            raise ValueError('Known DC consumer and raw context required')
        self.kind=kind;self.context=context;self.payloads=[]
        super().__init__()
    def _read(self,label,address,width=4):
        self.reads.append((address&MASK,width,label));return (yield from self._value(label))
    def _plan(self,complete=False):
        return DCPlan(complete,self.kind,tuple(self.reads),tuple(self.calls),tuple(self.payloads),(),
                      None if complete else self._needed,self.iterations)
    def _guard(self,p,handle,payload):
        slot=yield from self._read(p+'guard_root_slot',0x553e84)
        yield from self._call(p+'guard_root','0045db9c',(slot,handle))
        root=yield from self._value(p+'guard_root_eax')
        offset=yield from self._read(p+'guard_offset',0x5541f8)
        yield from self._call(p+'guard_byte','0045dbbc',((root+offset)&MASK,handle))
        if (yield from self._value(p+'guard_eax'))&255!=1:return
        results=[]
        # Both chains run before either zero comparison; do not short-circuit.
        for name,root_slot,offset_slot in (('first',0x553f3c,0x5541a0),('second',0x553f64,0x5541e4)):
            q=p+name+'.';slot=yield from self._read(q+'slot',root_slot)
            yield from self._call(q+'root','0045db9c',(slot,handle))
            root=yield from self._value(q+'root_eax');offset=yield from self._read(q+'offset',offset_slot)
            yield from self._call(q+'value','0045db9c',((root+offset)&MASK,handle))
            results.append((yield from self._value(q+'eax')))
        if results==[0,0]:
            self.payloads.append((handle,bytes((payload,))))
            yield from self._call(p+'send','00464834',(1,'source_local_payload',handle))
    def _run(self):
        yield ('entry','0046d904' if self.kind=='scan' else '0046dd70')
        yield from self._call('prologue','source_SEH_prologue_span')
        if self.kind=='list':yield from self._call('scratch_init','00404148',('scratch_ansi',))
        payload=yield from self._read('payload_byte',0x526fa8 if self.kind=='scan' else 0x526faa,1)
        if self.kind=='list':
            index=0
            while True:
                p='row%d.'%index
                first=yield from self._read(p+'count_initial_begin',self.context+0xd0);count=0
                if first:
                    end=yield from self._read(p+'count_end',self.context+0xd4)
                    begin=yield from self._read(p+'count_sub_begin',self.context+0xd0)
                    count=source_vector_count(end,begin)
                if count<=index:break
                begin=yield from self._read(p+'element_begin',self.context+0xd0)
                yield from self._call(p+'string','005050e4',((begin+index*4)&MASK,'scratch_ansi'))
                title=yield from self._value(p+'title_pointer')
                yield from self._call(p+'window','FindWindowA',(title or 0x52704c,0))
                hwnd=yield from self._value(p+'hwnd')
                if hwnd:
                    yield from self._call(p+'pid','GetWindowThreadProcessId',('local_pid',hwnd))
                    pid=yield from self._value(p+'pid_dword')
                    if pid:
                        yield from self._call(p+'open','OpenProcess',(pid,0,0x1fffff))
                        handle=yield from self._value(p+'handle')
                        if handle:yield from self._guard(p,handle,payload)
                self.iterations+=1;index=(index+1)&MASK
        else:
            yield from self._call('initial_text','source_initial_unicode_and_search_ANSI_preparation_span')
            yield from self._call('snapshot','CreateToolhelp32Snapshot',(0,2))
            snapshot=yield from self._value('snapshot_handle')
            if snapshot!=MASK:
                yield from self._call('first','Process32First',('process_entry_size_0x128',snapshot))
                present=yield from self._value('first_eax');index=0
                while present:
                    p='row%d.'%index
                    yield from self._call(p+'executable','opaque_executable_search_preparation')
                    yield from self._call(p+'search','0041ac60')
                    if (yield from self._value(p+'search_eax'))!=MASK:
                        pid=yield from self._value(p+'pid_dword')
                        yield from self._call(p+'open','OpenProcess',(pid,0,0x1fffff))
                        handle=yield from self._value(p+'handle')
                        address=yield from self._read(p+'identity_address',0x55420c)
                        yield from self._call(p+'identity_read','004604d4',(0xff,address,handle))
                        raw=yield from self._value(p+'identity_pointer')
                        yield from self._call(p+'identity_convert','00505bb8',(raw,'identity_unicode'))
                        yield from self._call(p+'compare','00505d4c',('initial_unicode','identity_unicode'))
                        if (yield from self._value(p+'compare_eax'))&255:
                            yield from self._guard(p,handle,payload)
                        yield from self._call(p+'identity_cleanup','00505c64',(2,'identity_unicode'))
                    yield from self._call(p+'next','Process32Next',('process_entry',snapshot))
                    present=yield from self._value(p+'next_eax')
                    yield from self._call(p+'executable_cleanup','00403860',(0,1,'executable_string'))
                    self.iterations+=1;index=(index+1)&MASK
        yield from self._call('final_cleanup','source_string_cleanup_span')
        yield from self._call('epilogue','source_FS_restore_stack_return_span')

class DCPeriodicFrame(JailPreloadFrame):
    def __init__(self,*,context=0x562194):
        if type(context) is not int or not 0<=context<=MASK:raise ValueError('Raw caller context required')
        self.context=context;self.stores=[];self.next_address=None
        super().__init__()
    def _read(self,label,address,width=4):
        self.reads.append((address&MASK,width,label));return (yield from self._value(label))
    def _plan(self,complete=False):
        return DCPlan(complete,'periodic',tuple(self.reads),tuple(self.calls),(),tuple(self.stores),
                      None if complete else self._needed,0,self.next_address)
    def _run(self):
        yield ('entry','00459981')
        if (yield from self._read('context_6e_byte',self.context+0x6e,1)):
            self.next_address=0x45998e;return
        self.next_address=0x459c5a
        if not (yield from self._read('enabled_byte',0x5691b1,1)):return
        yield from self._call('tick','GetTickCount')
        tick=yield from self._value('tick_eax');stamp=yield from self._read('stamp',0x553ce4)
        if ((tick-stamp)&MASK)<300000:return
        only=yield from self._read('list_only_byte',0x5691b2,1)
        yield from self._call('consumer','0046dd70' if only else '0046d904',(0x5690f8,))
        yield from self._call('post_tick','GetTickCount')
        fresh=yield from self._value('post_tick_eax');self.stores.append((0x553ce4,4,fresh))

@dataclass(frozen=True)
class DCCascadeObservation:
    parent: JailObservation=field(default_factory=JailObservation)
    consumer: JailObservation=field(default_factory=JailObservation)
    def __post_init__(self):
        if not isinstance(self.parent,JailObservation) or not isinstance(self.consumer,JailObservation):
            raise ValueError('Typed DC parent and consumer required')

@dataclass(frozen=True)
class DCCascadePlan:
    complete: bool
    parent: object
    consumer: object=None
    needed: object=None
    native_execution_verified: bool=False
    live_compatibility_verified: bool=False

class DCCascadeFrame:
    def __init__(self,*,context=0x562194):
        self.parent=DCPeriodicFrame(context=context);self.consumer=None;self.final=None
    def advance(self,o):
        if not isinstance(o,DCCascadeObservation):raise ValueError('Typed DC cascade observation required')
        if self.final is not None:return self.final
        normals=dict(o.parent.normal_returns)
        if self.consumer is None or self.consumer.final is None:normals['consumer']=False
        p=self.parent.advance(replace(o.parent,normal_returns=normals))
        if p.complete:
            self.final=DCCascadePlan(True,p,None if self.consumer is None else self.consumer.final);return self.final
        if p.needed!=('normal','consumer'):return DCCascadePlan(False,p,needed=('parent',p.needed))
        if self.consumer is None:
            self.consumer=DCConsumerFrame('list' if p.calls[-1][0]=='0046dd70' else 'scan',context=p.calls[-1][1][0])
        child=self.consumer.advance(replace(o.consumer,entry_reached=True))
        if not child.complete:return DCCascadePlan(False,p,child,('consumer',child.needed))
        p=self.parent.advance(o.parent);result=DCCascadePlan(p.complete,p,child,None if p.complete else ('parent',p.needed))
        if p.complete:self.final=result
        return result
