"""Scoped profile detector return and startup sender-field projection.

No filesystem probe, runtime global read/write or native initializer execution.
GetExeName/ANSI/ExtractFilePath/concat preceding FileExists remain observations.
"""
from dataclasses import dataclass,field
from types import MappingProxyType
from native_sender import SOURCE_SENDER_DEFAULTS

def _raw(value,bits,optional=False):
    if optional and value is None:return
    if type(value) is not int or not 0<=value<1<<bits:
        raise ValueError('Raw unsigned %d-bit profile observation required'%bits)

def _returns(instance):
    values=dict(instance.helper_returns)
    if any(type(v) is not bool for v in values.values()):
        raise ValueError('Separate profile helper normal-return receipts required')
    object.__setattr__(instance,'helper_returns',MappingProxyType(values))

@dataclass(frozen=True)
class ProfileDetectionObservation:
    file_exists_eax: object = None
    helper_returns: object = field(default_factory=dict)
    def __post_init__(self):
        _raw(self.file_exists_eax,32,True);_returns(self)

@dataclass(frozen=True)
class ProfileDetectionPlan:
    complete: bool
    mode_dword: object = None
    calls: tuple = ()
    missing: str = ''
    native_execution_verified: bool = False
    input_snapshot: object = None
    def __post_init__(self):
        if type(self.complete) is not bool or (self.mode_dword is not None and (type(self.mode_dword) is not int or self.mode_dword not in (1,2))):
            raise ValueError('Typed scoped detection result required')
        if self.complete and (self.mode_dword is None or self.missing):
            raise ValueError('Known mode and completed cleanup required')
        if type(self.native_execution_verified) is not bool:raise ValueError('Boolean native verification flag required')

def plan_profile_detection_tail(o):
    """Explicit entry before FileExists return; does not infer candidate path."""
    if not isinstance(o,ProfileDetectionObservation):raise ValueError('Typed profile detection observations required')
    calls=[];mode=None
    def result(ok,missing=''):return ProfileDetectionPlan(ok,mode,tuple(calls),missing,input_snapshot=o)
    for label in ('file_exists','candidate_cleanup','detection_cleanup'):
        calls.append(('normal_return',label))
        if o.helper_returns.get(label) is not True:return result(False,label+' normal return')
        if label=='file_exists' and o.file_exists_eax is None:return result(False,'FileExists EAX')
        if label=='candidate_cleanup':mode=2 if o.file_exists_eax&255 else 1
    return result(True)

def validate_profile_detection_plan(plan):
    """A bound child's conclusions must match its generated captured-input plan."""
    if not isinstance(plan,ProfileDetectionPlan) or not isinstance(plan.input_snapshot,ProfileDetectionObservation):
        raise ValueError('Generated profile detection snapshot required')
    if plan_profile_detection_tail(plan.input_snapshot)!=plan:
        raise ValueError('Bound profile detection differs from its generated snapshot')

@dataclass(frozen=True)
class ProfileSelectionObservation:
    detector_eax: object = None
    detection: object = None
    mode_read_steam: object = None
    mode_read_us: object = None
    use_owned_mode_reads: bool = False
    helper_returns: object = field(default_factory=dict)
    def __post_init__(self):
        _raw(self.detector_eax,32,True)
        _raw(self.mode_read_steam,8,True);_raw(self.mode_read_us,8,True)
        if self.detection is not None and not isinstance(self.detection,ProfileDetectionPlan):
            raise ValueError('Typed bound profile detection plan required')
        if type(self.use_owned_mode_reads) is not bool:raise ValueError('Explicit stable own-mode selection required')
        _returns(self)

@dataclass(frozen=True)
class ProfileSelectionPlan:
    complete: bool
    selected_tables: tuple = ()
    stores: tuple = ()
    calls: tuple = ()
    projected_sender_globals: tuple = ()
    missing: str = ''
    native_execution_verified: bool = False
    full_initializer_verified: bool = False

def plan_profile_sender_selection(o):
    """Reached0049f470..0049f4c0 only; table effects project two known fields."""
    if not isinstance(o,ProfileSelectionObservation):raise ValueError('Typed profile selection observations required')
    stores=[];calls=[];tables=[];sender={}
    class Missing(Exception):pass
    def result(ok,missing=''):
        return ProfileSelectionPlan(ok,tuple(tables),tuple(stores),tuple(calls),tuple(sender.items()),missing)
    def normal(label):
        calls.append(('normal_return',label))
        if o.helper_returns.get(label) is not True:raise Missing(label+' normal return')
    def fresh(field,label,owned):
        raw=getattr(o,field)
        if o.use_owned_mode_reads:
            if raw is not None:raise ValueError('Owned mode projection conflicts with raw reached mode observation')
            return owned
        if raw is None:raise Missing(label+' mode BYTE')
        return raw
    try:
        calls.append(('004a199c',0x553e3c))
        if o.detection is not None:
            if o.detector_eax is not None:raise ValueError('Bound detection conflicts with raw detector EAX')
            validate_profile_detection_plan(o.detection)
            if not o.detection.complete:raise Missing('bound detection: '+o.detection.missing)
            eax=o.detection.mode_dword
        else:eax=o.detector_eax
        normal('detect_profile')
        if eax is None:raise Missing('detector EAX')
        owned=eax&255;stores.append((0x553e46,1,owned))
        # Two distinct source reads. A Steam constructor can precede a later US read.
        for profile,field,expected,version,address in (
            ('current_steam','mode_read_steam',2,0x10097f,'004e4398'),
            ('current_us','mode_read_us',1,0x1009d4,'004fd640')):
            mode=fresh(field,profile,owned);calls.append(('read_mode',0x553e46,mode))
            if mode!=expected:continue
            stores.append((0x553e48,4,version));tables.append(profile)
            calls.append((address,0x553e3c))
            # Prospective scoped projection, not execution of the entire constructor.
            for slot,value in SOURCE_SENDER_DEFAULTS[profile]:
                stores.append((slot,4,value));sender[slot]=value
            normal(profile+'_initializer')
        return result(True)
    except Missing as error:return result(False,str(error))
