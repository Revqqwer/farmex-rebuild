"""Two reached Genie duration stores; immutable own text, no UI/game writes."""
from dataclasses import dataclass
from source_integer import SourceIntegerObservation,SourceIntegerFrame

DURATION_SPECS={
 'resume_seconds':('frmMain/MainTab/SheetKoruma/grpAntiCRSlot/txtanticrwaitclosegenie',60,0x569114),
 'notice_minutes':('frmMain/MainTab/SheetKoruma/grpNoticeKontrol/txtbnkgenieclosetime',30,0x569144),
}

@dataclass(frozen=True)
class GenieDurationPlan:
    complete:bool
    field:str
    conversion:object
    stores:tuple=()
    missing:str=''
    native_execution_verified:bool=False

class GenieDurationFrame:
    def __init__(self,field,text):
        if field not in DURATION_SPECS:raise ValueError('Known Genie duration field required')
        self.field=field;self.text=text;self.spec=DURATION_SPECS[field]
        self.child=SourceIntegerFrame(text,self.spec[1]);self.final=None
    def advance(self,o=None,*,helper_returned=None):
        if helper_returned is not None and type(helper_returned) is not bool:raise ValueError('Separate source conversion helper normal return required')
        if self.final is not None:return self.final
        child=self.child.advance(SourceIntegerObservation() if o is None else o)
        if not child.complete:return GenieDurationPlan(False,self.field,child,missing=child.missing)
        if helper_returned is not True:return GenieDurationPlan(False,self.field,child,missing='0045ef80 outer normal return')
        self.final=GenieDurationPlan(True,self.field,child,((self.spec[2],4,child.low_dword),))
        return self.final
