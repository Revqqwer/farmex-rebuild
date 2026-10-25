"""Relog selector wrappers and optional controller children; no native calls."""
from dataclasses import dataclass, field, replace
from types import MappingProxyType
from jail_preload import JailPreloadFrame, MASK
from jail_protection import JailObservation
from relog_controller import RelogControllerFrame

ENTRIES={'first':'0041272c','second':'0041279c','confirm':'004127c4','advance':'004126f4',
         'ui_select':'00412828','ui_advance':'00412858'}
LABELS={'select_first':'first','select_second':'second','confirm':'confirm','advance':'advance'}


@dataclass(frozen=True)
class RelogSelectionPlan:
    complete: bool
    kind: str
    argument: object = None
    reads: tuple = ()
    calls: tuple = ()
    return_eax: object = None
    needed: object = None
    whole_function_verified: bool = False
    native_execution_verified: bool = False
    live_compatibility_verified: bool = False


class RelogSelectionFrame(JailPreloadFrame):
    def __init__(self,kind,*,argument=None):
        if kind not in ENTRIES:
            raise ValueError('Known relog selector required')
        if kind in ('first','second','ui_select'):
            if type(argument) is not int or not 0<=argument<=MASK:
                raise ValueError('Raw selector DWORD argument required')
        elif argument is not None:
            raise ValueError('This source wrapper has no argument')
        self.kind=kind;self.argument=argument;self.return_eax=None
        super().__init__()

    def _read(self,label,address):
        self.reads.append((address&MASK,4,label))
        return (yield from self._value(label))

    def _guard(self,label,address):
        yield from self._call(label,'0045dc44',(address&MASK,))
        return (yield from self._value(label+'_eax'))

    def _plan(self,complete=False):
        return RelogSelectionPlan(complete,self.kind,self.argument,tuple(self.reads),tuple(self.calls),
                                   self.return_eax,None if complete else self._needed)

    def _run(self):
        yield ('entry',ENTRIES[self.kind])
        yield from self._call('prologue','source_frame_setup_span')
        if self.kind in ('first','confirm'):
            slot=yield from self._read('guard_slot',0x553f3c)
            root=yield from self._guard('guard_root',slot)
            offset=yield from self._read('guard_base_offset',0x5541a0)
            base=yield from self._guard('guard_base',root+offset)
            offset=yield from self._read('guard_item_offset',0x5541d4 if self.kind=='first' else 0x5541bc)
            address=(base+offset)&MASK
            if self.kind=='first':
                stride=yield from self._read('guard_stride',0x5541e0)
                address=(address+self.argument*stride)&MASK
            item=yield from self._guard('guard_item',address)
        # This is a NEW direct pointer chain, not the earlier guarded base.
        ui=self.kind in ('ui_select','ui_advance')
        slot=yield from self._read('direct_slot',0x553f64 if ui else 0x553f3c)
        root=yield from self._read('direct_root',slot)
        if self.kind=='ui_advance':
            obj=root
        else:
            offset=yield from self._read('direct_base_offset',0x5541e4 if ui else 0x5541a0)
            obj=yield from self._read('direct_object',root+offset)
        if self.kind in ('second','ui_advance'):
            target=yield from self._read('direct_target',0x553f74 if ui else 0x553f40)
            args=() if ui else (self.argument,)
        else:
            if self.kind=='advance':
                offset=yield from self._read('direct_item_offset',0x5541d0)
                item=yield from self._read('direct_item',obj+offset)
            elif self.kind=='ui_select':
                item=self.argument
            offset=yield from self._read('dispatch_offset',0x554200)
            table=yield from self._read('dispatch_vtable',obj)
            target=yield from self._read('dispatch_target',table+offset)
            args=(0x10000000 if self.kind=='first' else 1,item)
        yield from self._call('dispatch','captured_game_dispatch',
                              (('ECX',obj),('target',target),('physical_pushes',args)))
        self.return_eax=yield from self._value('dispatch_eax')
        yield from self._call('epilogue','source_frame_restore_return_span')


@dataclass(frozen=True)
class RelogControllerSelectionsObservation:
    _allowed_labels=LABELS
    parent: JailObservation = field(default_factory=JailObservation)
    children: object = field(default_factory=dict)

    def __post_init__(self):
        if not isinstance(self.parent,JailObservation):
            raise ValueError('Typed controller parent required')
        children=dict(self.children)
        if any(k not in self._allowed_labels or not isinstance(v,JailObservation) for k,v in children.items()):
            raise ValueError('Known reached selector labels and raw child observations required')
        object.__setattr__(self,'children',MappingProxyType(children))


@dataclass(frozen=True)
class RelogControllerSelectionsPlan:
    complete: bool
    parent: object
    children: object
    needed: object = None
    whole_function_verified: bool = False
    native_execution_verified: bool = False
    live_compatibility_verified: bool = False


class RelogControllerSelectionsFrame:
    """Bind any requested reached selector; child and outer returns stay separate."""
    _parent_type=RelogControllerFrame
    _labels=LABELS
    _max_calls=4

    def __init__(self):
        self.parent=self._parent_type();self.children={};self.child_plans={};self.final=None

    def _plan(self,p,needed=None):
        return RelogControllerSelectionsPlan(p.complete,p,MappingProxyType(dict(self.child_plans)),needed)

    def advance(self,o):
        if not isinstance(o,RelogControllerSelectionsObservation):
            raise ValueError('Typed controller/selector observations required')
        for label in o.children:
            if self.parent.normals.get(label) is True and label not in self.children:
                raise ValueError('Cannot retroactively bind opaque relog selector')
        if self.final is not None:return self.final
        # At most four distinct selector calls exist in one source invocation.
        for _ in range(self._max_calls+1):
            normals=dict(o.parent.normal_returns)
            for label in set(o.children)|set(self.children):
                if label not in self.children or self.children[label].final is None:
                    normals[label]=False
            p=self.parent.advance(replace(o.parent,normal_returns=normals))
            if p.complete:
                self.final=self._plan(p);return self.final
            kind,label=p.needed
            if kind!='normal' or label not in set(o.children)|set(self.children):
                return self._plan(p,('parent',p.needed))
            if label not in self.children:
                helper,args,_=p.calls[-1];selector=self._labels[label]
                assert helper==ENTRIES[selector]
                argument=args[0] if selector in ('first','second','ui_select') else None
                self.children[label]=RelogSelectionFrame(selector,argument=argument)
            child=self.children[label].advance(replace(o.children.get(label,JailObservation()),entry_reached=True))
            self.child_plans[label]=child
            if not child.complete:return self._plan(p,('child',label,child.needed))
            if o.parent.normal_returns.get(label) is not True:
                return self._plan(p,('parent',p.needed))
        raise AssertionError('More selector continuations than source call sites')
