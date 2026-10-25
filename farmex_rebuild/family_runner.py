"""Stateful local family routing; no class discovery, runtime override prediction or IO."""
from dataclasses import dataclass
from class_family import select_class_family,dispatch_class_family,FamilySelection
from job_dispatcher import HEADS,JobState
from alternate_dispatcher import AlternateState

@dataclass(frozen=True)
class FamilyTick:
    selection: FamilySelection
    result: object = None

class FamilyRunner:
    def __init__(self):
        self.normal_states={job:JobState() for job in HEADS}
        self.legal_states={job:AlternateState() for job in HEADS}

    def tick(self,job,values,snapshot,*,runtime_byte=None,blocked_74=None,normal_guard_45dc44=None,replies=None):
        selection=select_class_family(job,values,runtime_byte=runtime_byte,blocked_74=blocked_74,
                                      normal_guard_45dc44=normal_guard_45dc44)
        result=dispatch_class_family(job,selection,snapshot,normal_state=self.normal_states[job],
                                     legal_state=self.legal_states[job],replies=replies)
        if result is not None:
            if selection.family=='normal':self.normal_states[job]=result.state
            else:self.legal_states[job]=result.state
        return FamilyTick(selection,result)
