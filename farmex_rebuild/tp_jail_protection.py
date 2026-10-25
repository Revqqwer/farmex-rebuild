"""Optional typed jail child at the reached TP helper, with outer return separate."""
from dataclasses import dataclass, field, replace
from teleport_protection import TPObservation, TPFrame
from jail_protection import JailObservation, JailFrame

@dataclass(frozen=True)
class TPJailObservation:
    tp: TPObservation = field(default_factory=TPObservation)
    jail: JailObservation = field(default_factory=JailObservation)
    def __post_init__(self):
        if not isinstance(self.tp, TPObservation) or not isinstance(self.jail, JailObservation):
            raise ValueError('Typed TP and jail observations required')

@dataclass(frozen=True)
class TPJailPlan:
    complete: bool
    parent: object
    child: object = None
    needed: object = None
    native_execution_verified: bool = False
    live_compatibility_verified: bool = False

class TPJailFrame:
    def __init__(self, *, packet):
        self.parent = TPFrame('event', packet=packet)
        self.child = None
        self.child_label = None
        self.final = None

    def advance(self, o):
        if not isinstance(o, TPJailObservation):
            raise ValueError('Typed TP jail composition required')
        if self.final is not None:
            return self.final
        normals = dict(o.tp.normal_returns)
        # No parent receipt can skip a selected, unfinished child.
        if self.child is None or self.child.final is None:
            normals.update(jail_list=False, jail_all=False)
        p = self.parent.advance(replace(o.tp, normal_returns=normals))
        if p.complete:
            self.final = TPJailPlan(True, p, None if self.child is None else self.child.final)
            return self.final
        if p.needed not in (('normal', 'jail_list'), ('normal', 'jail_all')):
            return TPJailPlan(False, p, needed=('parent', p.needed))
        label = p.needed[1]
        if self.child is None:
            self.child_label = label
            self.child = JailFrame('list' if label == 'jail_list' else 'scan', context=p.calls[-1][1][0])
        if label != self.child_label:
            raise AssertionError('Reached jail branch changed within one invocation')
        # The source call derives entry; prologue/inner normal receipts stay explicit.
        child = self.child.advance(replace(o.jail, entry_reached=True))
        if not child.complete:
            return TPJailPlan(False, p, child, ('child', child.needed))
        # Even a completed child cannot manufacture its caller's normal return.
        p = self.parent.advance(o.tp)
        result = TPJailPlan(p.complete, p, child, None if p.complete else ('parent', p.needed))
        if result.complete:
            self.final = result
        return result
