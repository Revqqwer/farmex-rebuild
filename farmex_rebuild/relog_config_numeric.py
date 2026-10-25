"""Typed reached numeric helper children for the current config control model."""
from dataclasses import dataclass,field,replace
from types import MappingProxyType
from jail_protection import JailObservation
from relog_config import RelogConfigFrame,COMMON,USKO,STEAM,CURRENT_SOURCE
from profile_numeric import ProfileNumericFrame

NAMES=tuple(r[0] for r in COMMON+USKO+STEAM)
LABELS={n+'.read':n for n in NAMES}


@dataclass(frozen=True)
class RelogConfigNumericObservation:
    _names=NAMES
    parent: JailObservation=field(default_factory=JailObservation)
    helpers: object=field(default_factory=dict)
    def __post_init__(self):
        if not isinstance(self.parent,JailObservation):raise ValueError('Typed config parent required')
        helpers=dict(self.helpers)
        if any(k not in self._names or not isinstance(v,JailObservation) for k,v in helpers.items()):
            raise ValueError('Known typed config numeric helper observations required')
        object.__setattr__(self,'helpers',MappingProxyType(helpers))


@dataclass(frozen=True)
class RelogConfigNumericPlan:
    complete: bool
    parent: object
    helpers: object=field(default_factory=dict)
    needed: object=None
    native_execution_verified: bool=False
    live_compatibility_verified: bool=False
    def __post_init__(self):object.__setattr__(self,'helpers',MappingProxyType(dict(self.helpers)))


class RelogConfigNumericFrame:
    _labels=LABELS
    _observation_type=RelogConfigNumericObservation
    def __init__(self,source_sha256=CURRENT_SOURCE):
        self.parent=RelogConfigFrame(source_sha256);self.frames={};self.plans={};self.final=None

    def _plan(self,p,needed=None):return RelogConfigNumericPlan(p.complete,p,self.plans,needed)

    def _consumes_eax(self,name):return True

    def _make_child(self,name,helper,args):
        assert helper in ('0045f508','0045f5f4') and len(args)==4
        a,b,key,section=args;boolean=helper=='0045f508'
        return ProfileNumericFrame('boolean' if boolean else 'dword',section=section,key=key,
                                   path=b if boolean else a,default=a if boolean else b)

    def _bound(self,o):
        values=dict(o.values)
        for name,p in self.plans.items():
            if not p.complete or not self._consumes_eax(name):continue
            key=name+'.eax'
            if key in values and values[key]!=p.return_eax:
                raise ValueError('Config helper EAX conflicts with bound numeric wrapper result')
            values[key]=p.return_eax
        return replace(o,values=values)

    def advance(self,o):
        if not isinstance(o,self._observation_type):raise ValueError('Typed config numeric composition required')
        if self.final is not None:return self.final
        # Every scalar label appears at most once; only the chosen branch runs.
        for _ in range(len(self._labels)+1):
            parent=self._bound(o.parent);normals=dict(parent.normal_returns)
            for label,name in self._labels.items():
                if name not in self.frames or self.frames[name].final is None:normals[label]=False
            p=self.parent.advance(replace(parent,normal_returns=normals))
            if p.complete:self.final=self._plan(p);return self.final
            if p.needed[0]!='normal' or p.needed[1] not in self._labels:return self._plan(p,('parent',p.needed))
            label=p.needed[1];name=self._labels[label]
            if name not in self.frames:
                helper,args,_=p.calls[-1]
                self.frames[name]=self._make_child(name,helper,args)
            self.plans[name]=self.frames[name].advance(replace(o.helpers.get(name,JailObservation()),entry_reached=True))
            if not self.plans[name].complete:return self._plan(p,(name,self.plans[name].needed))
            # Validate/inject before allowing the independent caller return.
            self._bound(o.parent)
            if o.parent.normal_returns.get(label) is not True:return self._plan(p,('parent',('normal',label)))
        raise AssertionError('Unexpected repeated config numeric helper call')
