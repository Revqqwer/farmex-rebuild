"""4f7040 name-based scroll scan. Fresh ANSI contents, no game memory I/O.

The conversion and slot-name helper are invoked separately per slot. Captured
bytes preserve AnsiString length; no strip, casefold, decode or NUL truncation.
"""
from dataclasses import dataclass, field
from collections.abc import Mapping
from types import MappingProxyType
from typing import Optional
from mining_slot_name import SlotNameObservation, plan_slot_name


@dataclass(frozen=True)
class UpgradeScrollSample:
    converted_key_bytes: Optional[bytes] = None
    slot_name_bytes: Optional[bytes] = None
    slot_name_inputs: Optional[SlotNameObservation] = None

    def __post_init__(self):
        for value in (self.converted_key_bytes, self.slot_name_bytes):
            if value is not None and type(value) is not bytes:
                raise ValueError('Captured immutable ANSI bytes required')
        if self.slot_name_inputs is not None and not isinstance(self.slot_name_inputs, SlotNameObservation):
            raise ValueError('Typed fresh slot-name observation required')


@dataclass(frozen=True)
class UpgradeScrollObservation:
    samples: Mapping = field(default_factory=dict)

    def __post_init__(self):
        if not isinstance(self.samples, Mapping):
            raise ValueError('Per-slot observation mapping required')
        # Do not inspect unreachable sample values before an earlier match.
        if any(type(k) is not int or not 14 <= k <= 41 for k in self.samples):
            raise ValueError('Source inventory slots14..41 required')
        object.__setattr__(self, 'samples', MappingProxyType(dict(self.samples)))


@dataclass(frozen=True)
class UpgradeScrollPlan:
    status: str
    complete: bool
    relative_index: Optional[int] = None
    visited_slots: tuple = ()
    calls: tuple = ()
    slot_name_plans: tuple = ()
    missing: str = ''
    independently_verified: bool = False


def plan_upgrade_scroll(observation):
    if not isinstance(observation, UpgradeScrollObservation):
        raise ValueError('Typed scroll observation required')
    visited = []
    calls = []
    names = []
    for slot in range(14, 42):
        visited.append(slot)
        calls.append(('004073a0', slot))
        sample = observation.samples.get(slot)
        if sample is None or (isinstance(sample, UpgradeScrollSample) and sample.converted_key_bytes is None):
            return UpgradeScrollPlan('needs_key_conversion', False, visited_slots=tuple(visited),
                                     calls=tuple(calls), slot_name_plans=tuple(names),
                                     missing='slot%d fresh004073a0 ANSI contents'%slot)
        if not isinstance(sample, UpgradeScrollSample):
            raise ValueError('Typed reached scroll sample required')
        calls.append(('00463670', slot))
        if sample.slot_name_bytes is not None and sample.slot_name_inputs is not None:
            raise ValueError('Captured name and bound name helper conflict')
        name = sample.slot_name_bytes
        if sample.slot_name_inputs is not None:
            resolved = plan_slot_name(slot, sample.slot_name_inputs)
            names.append((slot, resolved))
            name = resolved.ansi_bytes
        if name is None:
            return UpgradeScrollPlan('needs_slot_name', False, visited_slots=tuple(visited),
                                     calls=tuple(calls), slot_name_plans=tuple(names),
                                     missing='slot%d fresh00463670 ANSI contents'%slot)
        calls.append(('00505118', slot))
        if name == sample.converted_key_bytes:
            return UpgradeScrollPlan('scroll_found', True, slot-14, tuple(visited), tuple(calls), tuple(names))
    return UpgradeScrollPlan('scroll_not_found', True, -1, tuple(visited), tuple(calls), tuple(names))
