"""00424924 normal startup and typed local helper composition; no native work."""
from dataclasses import dataclass,field,replace
from types import MappingProxyType
from jail_preload import JailPreloadFrame,MASK
from jail_protection import JailObservation
from callback_replacement import CallbackReplacementFrame
from detector_code_state import DetectorCodeStateFrame,REGIONS,CURRENT
from relog_config import RelogConfigFrame,CURRENT_SOURCE
from relog_config_numeric import RelogConfigNumericFrame,RelogConfigNumericObservation
from relog_config_profile import RelogConfigProfileFrame,RelogConfigProfileObservation


@dataclass(frozen=True)
class RelogStartupPlan:
    complete: bool
    reads: tuple=()
    calls: tuple=()
    stores: tuple=()
    needed: object=None
    ready_iterations: int=0
    source_sha256: str=''
    whole_function_verified: bool=False
    native_execution_verified: bool=False
    live_compatibility_verified: bool=False


class RelogStartupFrame(JailPreloadFrame):
    def __init__(self,source_sha256):
        if source_sha256 not in REGIONS:raise ValueError('Pinned startup source required')
        self.source_sha256=source_sha256;self.stores=[]
        super().__init__()

    def _plan(self,complete=False):
        return RelogStartupPlan(complete,tuple(self.reads),tuple(self.calls),tuple(self.stores),
          None if complete else self._needed,self.iterations,self.source_sha256)

    def _guard(self,label,address):
        yield from self._call(label,'0045dc44',(address&MASK,))
        return (yield from self._value(label+'_eax'))

    def _object(self,prefix):
        slot=yield from self._read(prefix+'slot',0x553f3c)
        root=yield from self._guard(prefix+'root',slot)
        offset=yield from self._read(prefix+'offset',0x5541a0)
        return (yield from self._guard(prefix+'object',(root+offset)&MASK))

    def _run(self):
        yield ('entry','00424924')
        yield from self._call('prologue','source_frame_setup_span')
        while True:
            prefix='ready%d.'%self.iterations
            obj=yield from self._object(prefix)
            self.iterations+=1
            if obj:break
            yield from self._call(prefix+'sleep','SleepEx',(0,1))
        for label,address in (('prepare','004e30c8' if self.source_sha256==CURRENT else '004e30ac'),
          ('prepare_second','0042489c'),('prepare_third','004248bc'),('prepare_fourth','004d3af4')):
            yield from self._call(label,address)
        # This is a new source chain, not the ready-loop object snapshot.
        obj=yield from self._object('install.')
        table=yield from self._guard('install.table',obj)
        offset=yield from self._read('install.slot_offset',0x554204)
        self.stores.append((0x554210,4,(table+offset)&MASK))
        fresh=yield from self._read('install.slot_fresh',0x554210)
        yield from self._call('replace','0046b8fc',(0x412adc,fresh,0x554220))
        yield from self._call('config','00412f48')
        yield from self._call('code_state',REGIONS[self.source_sha256][2],(1,))
        base=yield from self._read('next_slot_base',0x553f68)
        offset=yield from self._read('next_slot_offset',0x554204)
        self.stores.append((0x554214,4,(base+offset)&MASK))
        yield from self._call('finish_first','004d9358')
        yield from self._call('finish_second','004d925c')
        yield from self._call('epilogue','source_frame_restore_return_span')


@dataclass(frozen=True)
class RelogStartupChildrenObservation:
    parent: JailObservation=field(default_factory=JailObservation)
    replacement: JailObservation=field(default_factory=JailObservation)
    code_state: JailObservation=field(default_factory=JailObservation)
    def __post_init__(self):
        if any(not isinstance(v,JailObservation) for v in (self.parent,self.replacement,self.code_state)):
            raise ValueError('Typed startup/helper observations required')


@dataclass(frozen=True)
class RelogStartupChildrenPlan:
    complete: bool
    parent: object
    children: object=field(default_factory=dict)
    needed: object=None
    native_execution_verified: bool=False
    live_compatibility_verified: bool=False
    def __post_init__(self):object.__setattr__(self,'children',MappingProxyType(dict(self.children)))


class RelogStartupChildrenFrame:
    """Both children derive arguments only from reached actual source calls."""
    _labels=('replace','code_state')
    _observation_type=RelogStartupChildrenObservation
    def __init__(self,source_sha256):
        self.parent=RelogStartupFrame(source_sha256);self.frames={};self.plans={};self.final=None

    def _plan(self,p,needed=None):return RelogStartupChildrenPlan(p.complete,p,self.plans,needed)

    def _make_child(self,label,helper,args):
        if label=='replace':
            assert helper=='0046b8fc' and len(args)==3
            replacement,slot,saved=args
            return CallbackReplacementFrame(saved_cell=saved,target_slot=slot,replacement=replacement)
        assert label=='code_state' and helper==REGIONS[self.parent.source_sha256][2] and args==(1,)
        return DetectorCodeStateFrame(self.parent.source_sha256,args[0])

    def _child_observation(self,o,label):return o.replacement if label=='replace' else o.code_state

    def _entered_child_observation(self,obs,label):return replace(obs,entry_reached=True)

    def advance(self,o):
        if not isinstance(o,self._observation_type):raise ValueError('Typed startup composition required')
        if self.final is not None:return self.final
        # Each configured label occurs at most once in this source path.
        for _ in range(len(self._labels)+1):
            normals=dict(o.parent.normal_returns)
            for label in self._labels:
                if label not in self.frames or self.frames[label].final is None:normals[label]=False
            p=self.parent.advance(replace(o.parent,normal_returns=normals))
            if p.complete:self.final=self._plan(p);return self.final
            if p.needed[0]!='normal' or p.needed[1] not in self._labels:
                return self._plan(p,('parent',p.needed))
            label=p.needed[1];helper,args,_=p.calls[-1]
            if label not in self.frames:
                self.frames[label]=self._make_child(label,helper,args)
            child=self.frames[label]
            obs=self._child_observation(o,label)
            self.plans[label]=child.advance(self._entered_child_observation(obs,label))
            if not self.plans[label].complete:return self._plan(p,(label,self.plans[label].needed))
            if o.parent.normal_returns.get(label) is not True:
                return self._plan(p,('parent',('normal',label)))
        raise AssertionError('Unexpected additional startup child call')


@dataclass(frozen=True)
class RelogStartupConfigObservation(RelogStartupChildrenObservation):
    config: JailObservation=field(default_factory=JailObservation)
    def __post_init__(self):
        super().__post_init__()
        if not isinstance(self.config,JailObservation):raise ValueError('Typed startup config child required')


class RelogStartupConfigFrame(RelogStartupChildrenFrame):
    """Current-source replacement -> config -> code-state normal composition."""
    _labels=('replace','config','code_state')
    _observation_type=RelogStartupConfigObservation
    def __init__(self,source_sha256=CURRENT_SOURCE):
        if source_sha256!=CURRENT_SOURCE:raise ValueError('Current config-compatible startup source required')
        super().__init__(source_sha256)

    def _make_child(self,label,helper,args):
        if label=='config':
            assert helper=='00412f48' and args==()
            return RelogConfigFrame(self.parent.source_sha256)
        return super()._make_child(label,helper,args)

    def _child_observation(self,o,label):
        return o.config if label=='config' else super()._child_observation(o,label)


@dataclass(frozen=True)
class RelogStartupNumericObservation(RelogStartupConfigObservation):
    config: RelogConfigNumericObservation=field(default_factory=RelogConfigNumericObservation)
    def __post_init__(self):
        RelogStartupChildrenObservation.__post_init__(self)
        if not isinstance(self.config,RelogConfigNumericObservation):raise ValueError('Typed numeric config composition required')


class RelogStartupNumericFrame(RelogStartupConfigFrame):
    _observation_type=RelogStartupNumericObservation
    def _make_child(self,label,helper,args):
        if label=='config':
            assert helper=='00412f48' and args==()
            return RelogConfigNumericFrame(self.parent.source_sha256)
        return super()._make_child(label,helper,args)

    def _entered_child_observation(self,obs,label):
        if label=='config':return replace(obs,parent=replace(obs.parent,entry_reached=True))
        return super()._entered_child_observation(obs,label)


@dataclass(frozen=True)
class RelogStartupProfileObservation(RelogStartupNumericObservation):
    config: RelogConfigProfileObservation=field(default_factory=RelogConfigProfileObservation)
    def __post_init__(self):
        RelogStartupChildrenObservation.__post_init__(self)
        if not isinstance(self.config,RelogConfigProfileObservation):raise ValueError('Typed all-profile config composition required')


class RelogStartupProfileFrame(RelogStartupNumericFrame):
    _observation_type=RelogStartupProfileObservation
    def _make_child(self,label,helper,args):
        if label=='config':
            assert helper=='00412f48' and args==()
            return RelogConfigProfileFrame(self.parent.source_sha256)
        return super()._make_child(label,helper,args)
