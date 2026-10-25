"""0046b8fc saved-original/copy4 plans and typed relog installation bindings."""
from dataclasses import dataclass,field,replace
from jail_preload import JailPreloadFrame,MASK
from jail_protection import JailObservation
from relog_controller import RelogControllerFrame
from relog_gate import RelogGateFrame


@dataclass(frozen=True)
class CallbackReplacementPlan:
    complete: bool
    reads: tuple = ()
    calls: tuple = ()
    stores: tuple = ()
    copy_intents: tuple = ()
    needed: object = None
    whole_function_verified: bool = False
    native_execution_verified: bool = False
    memory_effects_verified: bool = False
    live_compatibility_verified: bool = False


class CallbackReplacementFrame(JailPreloadFrame):
    """Formal source args(saved_cell,slot,replacement), caller PUSH order reversed.

    Raw source stack argument values are fixed for this normal invocation.
    copy4/guarded reader remain opaque; stores are inert logical projections.
    """
    def __init__(self,*,saved_cell,target_slot,replacement):
        if any(type(v) is not int or not 0<=v<=MASK for v in (saved_cell,target_slot,replacement)):
            raise ValueError('Three raw callback replacement arguments required')
        self.saved_cell=saved_cell;self.target_slot=target_slot;self.replacement=replacement
        self.stores=[];self.copy_intents=[]
        super().__init__()

    def _plan(self,complete=False):
        return CallbackReplacementPlan(complete,tuple(self.reads),tuple(self.calls),tuple(self.stores),
            tuple(self.copy_intents),None if complete else self._needed)

    def _run(self):
        yield ('entry','0046b8fc')
        yield from self._call('prologue','source_frame_setup_span')
        self.reads.append((self.saved_cell,4,'saved_original'))
        if not (yield from self._value('saved_original')):
            yield from self._call('original_reader','0045dc44',(self.target_slot,))
            old=yield from self._value('original_eax')
            self.stores.append((self.saved_cell,4,old))
        self.copy_intents.append((self.target_slot,self.replacement.to_bytes(4,'little')))
        yield from self._call('copy4','memcpy',
            (4,('source_stack_replacement_argument',self.replacement),self.target_slot))
        self.stores.append((self.target_slot,4,self.replacement))
        yield from self._call('epilogue','source_frame_restore_return_span')


@dataclass(frozen=True)
class RelogReplacementObservation:
    parent: JailObservation = field(default_factory=JailObservation)
    replacement: JailObservation = field(default_factory=JailObservation)

    def __post_init__(self):
        if not isinstance(self.parent,JailObservation) or not isinstance(self.replacement,JailObservation):
            raise ValueError('Typed relog and replacement observations required')


@dataclass(frozen=True)
class RelogReplacementPlan:
    complete: bool
    parent: object
    replacement: object = None
    needed: object = None
    native_execution_verified: bool = False
    live_compatibility_verified: bool = False


class RelogReplacementFrame:
    """Bind either reached controller bootstrap or gate installation copy helper."""
    def __init__(self,kind):
        if kind not in ('controller','gate'):raise ValueError('Known relog replacement parent required')
        self.parent=(RelogControllerFrame if kind=='controller' else RelogGateFrame)()
        self.label='bootstrap_replace' if kind=='controller' else 'install_replace'
        self.replacement=self.child_plan=self.final=None

    def _plan(self,p,needed=None):return RelogReplacementPlan(p.complete,p,self.child_plan,needed)

    def advance(self,o):
        if not isinstance(o,RelogReplacementObservation):raise ValueError('Typed relog replacement binding required')
        if self.final is not None:return self.final
        normals=dict(o.parent.normal_returns)
        if self.replacement is None or self.replacement.final is None:normals[self.label]=False
        p=self.parent.advance(replace(o.parent,normal_returns=normals))
        if p.complete:self.final=self._plan(p);return self.final
        if p.needed!=('normal',self.label):return self._plan(p,('parent',p.needed))
        if self.replacement is None:
            helper,args,_=p.calls[-1];assert helper=='0046b8fc' and len(args)==3
            replacement,slot,saved=args
            self.replacement=CallbackReplacementFrame(saved_cell=saved,target_slot=slot,replacement=replacement)
        self.child_plan=self.replacement.advance(replace(o.replacement,entry_reached=True))
        if not self.child_plan.complete:return self._plan(p,('replacement',self.child_plan.needed))
        p=self.parent.advance(o.parent)
        result=self._plan(p,None if p.complete else ('parent',p.needed))
        if p.complete:self.final=result
        return result
