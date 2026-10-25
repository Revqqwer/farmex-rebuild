"""Optional numeric and string profile source children for config control."""
from dataclasses import dataclass
from relog_config_numeric import RelogConfigNumericFrame,RelogConfigNumericObservation,NAMES,LABELS
from profile_string import ProfileStringFrame

STRING_NAMES=('captcha_detail','id','pw')


@dataclass(frozen=True)
class RelogConfigProfileObservation(RelogConfigNumericObservation):
    _names=NAMES+STRING_NAMES


class RelogConfigProfileFrame(RelogConfigNumericFrame):
    _labels={**LABELS,**{n+'.read':n for n in STRING_NAMES}}
    _observation_type=RelogConfigProfileObservation
    def _consumes_eax(self,name):return name not in STRING_NAMES
    def _make_child(self,name,helper,args):
        if name in STRING_NAMES:
            assert helper=='0045f228' and len(args)==5
            default,path,key,section,output=args
            return ProfileStringFrame(section=section,key=key,path=path,default=default,output=output)
        return super()._make_child(name,helper,args)
