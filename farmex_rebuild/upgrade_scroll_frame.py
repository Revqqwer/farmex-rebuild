"""Reached-only scroll scan continuation; existing lower name planner, no IO."""
from dataclasses import dataclass
from upgrade_scroll import UpgradeScrollObservation,UpgradeScrollSample
from mining_slot_name import SlotNameObservation,plan_slot_name
from item_name import ItemNameObservation


@dataclass(frozen=True)
class UpgradeScrollFrameResult:
    complete:bool
    relative_index:object=None
    needed:object=None
    visited_slots:tuple=()
    native_execution_verified:bool=False


class UpgradeScrollFrame:
    def __init__(self):
        self.slot=14;self.keys={};self.names={};self.lower={};self.modes={};self.visited=[];self.final=None
    def advance(self,o=None):
        if self.final is not None:return self.final
        o=UpgradeScrollObservation() if o is None else o
        if not isinstance(o,UpgradeScrollObservation):raise ValueError('Typed scroll scan required')
        def pending(needed):return UpgradeScrollFrameResult(False,needed=needed,visited_slots=tuple(self.visited))
        for _ in range(28):
            slot=self.slot
            if slot>41:
                self.final=UpgradeScrollFrameResult(True,-1,visited_slots=tuple(self.visited));return self.final
            if slot not in self.visited:self.visited.append(slot)
            sample=o.samples.get(slot)
            if sample is not None and not isinstance(sample,UpgradeScrollSample):raise ValueError('Typed reached scroll sample required')
            if slot not in self.keys:
                if sample is None or sample.converted_key_bytes is None:return pending((slot,'converted_key_bytes'))
                self.keys[slot]=sample.converted_key_bytes
            if slot not in self.names:
                if sample is None:return pending((slot,'slot_name'))
                if sample.slot_name_bytes is not None and sample.slot_name_inputs is not None:raise ValueError('Scroll name sources conflict')
                if sample.slot_name_bytes is not None:
                    if self.modes.get(slot)=='lower':raise ValueError('Ready name cannot bypass lower scroll name')
                    self.modes[slot]='ready';self.names[slot]=sample.slot_name_bytes
                else:
                    if sample.slot_name_inputs is None:return pending((slot,'slot_name'))
                    self.modes[slot]='lower';incoming=sample.slot_name_inputs;cache=self.lower.setdefault(slot,{})
                    def reader(field,count):
                        if field in cache:return cache[field]
                        if field.startswith('name.'):
                            n=incoming.name or ItemNameObservation();value=getattr(n,field[5:])
                        else:value=getattr(incoming,field)
                        if value is not None:
                            if field=='name.captured':
                                if len(value)<count:return value
                                value=value[:count]
                            cache[field]=value
                        return value
                    p=plan_slot_name(slot,SlotNameObservation(),_observation_reader=reader)
                    if p.ansi_bytes is None:return pending((slot,'lower_name',p.status,p.missing))
                    self.names[slot]=p.ansi_bytes
            if self.keys[slot]==self.names[slot]:
                self.final=UpgradeScrollFrameResult(True,slot-14,visited_slots=tuple(self.visited));return self.final
            self.slot+=1
        self.final=UpgradeScrollFrameResult(True,-1,visited_slots=tuple(self.visited))
        return self.final
