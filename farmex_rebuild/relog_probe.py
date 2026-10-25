"""004e2bc8 normal status dispatcher; detectors and toggle effects stay opaque."""
from dataclasses import dataclass,field,replace
from jail_preload import JailPreloadFrame,MASK
from jail_protection import JailObservation
from relog_controller import RelogControllerFrame
from relog_gate import RelogGateFrame


@dataclass(frozen=True)
class RelogProbePlan:
    complete: bool
    reads: tuple=()
    calls: tuple=()
    stores: tuple=()
    output_code: object=None
    return_al: object=None
    return_eax: object=None
    needed: object=None
    whole_function_verified: bool=False
    native_execution_verified: bool=False
    live_compatibility_verified: bool=False


class RelogProbeFrame(JailPreloadFrame):
    """Output is a symbolic caller-local DWORD, not a native address.

    Success sets AL only; upper EAX is deliberately unknown. Failure XORs EAX.
    The invalid-state path returns zero without writing the caller's local.
    """
    def __init__(self):
        self.stores=[];self.output_code=self.return_al=self.return_eax=None
        super().__init__()

    def _plan(self,complete=False):
        return RelogProbePlan(complete,tuple(self.reads),tuple(self.calls),tuple(self.stores),
          self.output_code,self.return_al,self.return_eax,None if complete else self._needed)

    def _test(self,label,address):
        yield from self._call(label+'_before','004e2a88',(0,))
        yield from self._call(label,address)
        captured=(yield from self._value(label+'_eax'))&255
        yield from self._call(label+'_after','004e2a88',(1,))
        return captured

    def _result(self,code,success):
        self.output_code=code
        self.stores.append(('source_local_dword',4,code))
        self.return_al=int(success)
        if not success:self.return_eax=0

    def _run(self):
        yield ('entry','004e2bc8')
        yield from self._call('prologue','source_frame_setup_span')
        first=yield from self._read('state_initial',0x56ff3c)
        if first==0:
            # INC is a separate source memory read/modify/write after CMP.
            inc=yield from self._read('state_increment',0x56ff3c)
            self.stores.append((0x56ff3c,4,(inc+1)&MASK))
            if (yield from self._test('first','004e146c')):
                self._result(1,True)
            elif not (yield from self._test('second','004e22c8')):
                self._result(2,True)
            elif (yield from self._test('third','004e18ec')):
                self._result(3,True)
            else:self._result(91,False)
        else:
            second=yield from self._read('state_second',0x56ff3c)
            if second==1:
                self.stores.append((0x56ff3c,4,0))
                if (yield from self._test('fourth','004e26dc')):
                    self._result(4,True)
                elif (yield from self._test('fifth','004e299c')):
                    self._result(5,True)
                else:self._result(92,False)
            else:self.return_al=self.return_eax=0
        yield from self._call('epilogue','source_frame_restore_return_span')


@dataclass(frozen=True)
class RelogProbeBindingObservation:
    parent: JailObservation=field(default_factory=JailObservation)
    probe: JailObservation=field(default_factory=JailObservation)
    def __post_init__(self):
        if not isinstance(self.parent,JailObservation) or not isinstance(self.probe,JailObservation):
            raise ValueError('Typed relog parent and probe required')


@dataclass(frozen=True)
class RelogProbeBindingPlan:
    complete: bool
    parent: object
    probe: object=None
    needed: object=None
    native_execution_verified: bool=False
    live_compatibility_verified: bool=False


class RelogProbeBindingFrame:
    """Bind reached probe result, preserving separate caller return receipt."""
    def __init__(self,kind):
        if kind not in ('controller','gate'):raise ValueError('Known relog parent required')
        self.parent=(RelogControllerFrame if kind=='controller' else RelogGateFrame)()
        self.label='bootstrap_probe' if kind=='controller' else 'install_probe'
        self.eax_key=self.label+'_eax'
        self.output_key='bootstrap_local_dword' if kind=='controller' else 'install_probe_local'
        self.child=self.child_plan=self.final=None

    def _plan(self,p,needed=None):return RelogProbeBindingPlan(p.complete,p,self.child_plan,needed)

    def _bound(self,o):
        values=dict(o.values)
        p=self.child_plan
        if p.return_eax is not None:
            if self.eax_key in values and values[self.eax_key]!=p.return_eax:
                raise ValueError('Caller EAX conflicts with source XOR return')
            values[self.eax_key]=p.return_eax
        elif self.eax_key in values and values[self.eax_key]&255!=p.return_al:
            raise ValueError('Caller AL conflicts with captured probe return')
        if p.output_code is not None:
            if self.output_key in values and values[self.output_key]!=p.output_code:
                raise ValueError('Caller local conflicts with source output store')
            values[self.output_key]=p.output_code
        return replace(o,values=values)

    def advance(self,o):
        if not isinstance(o,RelogProbeBindingObservation):raise ValueError('Typed relog probe binding required')
        if self.final is not None:return self.final
        normals=dict(o.parent.normal_returns)
        if self.child is None or self.child.final is None:normals[self.label]=False
        parent=o.parent
        if self.child_plan is not None and self.child_plan.complete:parent=self._bound(parent)
        p=self.parent.advance(replace(parent,normal_returns=normals))
        if p.complete:self.final=self._plan(p);return self.final
        if p.needed!=('normal',self.label):return self._plan(p,('parent',p.needed))
        if self.child is None:
            helper,args,_=p.calls[-1];assert helper=='004e2bc8' and args==('source_local_dword',)
            self.child=RelogProbeFrame()
        self.child_plan=self.child.advance(replace(o.probe,entry_reached=True))
        if not self.child_plan.complete:return self._plan(p,('probe',self.child_plan.needed))
        p=self.parent.advance(self._bound(o.parent))
        result=self._plan(p,None if p.complete else ('parent',p.needed))
        if p.complete:self.final=result
        return result
