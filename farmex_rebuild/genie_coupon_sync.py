"""00458143..004581b9 normal coupon-gate byte synchronization; inert only."""
from dataclasses import dataclass,field,replace
from jail_preload import JailPreloadFrame,MASK
from jail_protection import JailObservation
from genie_settings import GenieSettingsFrame,GenieSettingsObservation
from profile_numeric import CURRENT_SOURCE


@dataclass(frozen=True)
class GenieCouponSyncPlan:
    complete: bool
    reads: tuple=()
    calls: tuple=()
    write_intents: tuple=()
    needed: object=None
    next_address: object=None
    source_sha256: str=CURRENT_SOURCE
    native_execution_verified: bool=False
    byte_effects_verified: bool=False
    live_compatibility_verified: bool=False


class GenieCouponSyncFrame(JailPreloadFrame):
    def __init__(self,*,context=0x562194,source_sha256=CURRENT_SOURCE):
        if source_sha256!=CURRENT_SOURCE:raise ValueError('Current coupon-sync source required')
        if type(context) is not int or not 0<=context<=MASK:raise ValueError('Raw source context required')
        self.context=context;self.write_intents=[];self.next_address=None
        super().__init__()

    def _plan(self,complete=False):
        return GenieCouponSyncPlan(complete,tuple(self.reads),tuple(self.calls),tuple(self.write_intents),
          None if complete else self._needed,self.next_address)

    def _guard(self,label,address,helper='0045dc44'):
        yield from self._call(label,helper,(address&MASK,))
        return (yield from self._value(label+'_eax'))

    def _run(self):
        yield ('entry','00458143')
        slot=yield from self._read('root_slot',0x553e80)
        root=yield from self._guard('root',slot)
        offset=yield from self._read('table_offset',0x554168)
        table=yield from self._guard('table',root+offset)
        offset=yield from self._read('byte_offset',0x554174)
        address=(table+offset)&MASK
        self.reads.append(((self.context+0xba)&MASK,1,'coupon_flag_byte'))
        enabled=yield from self._value('coupon_flag_byte')
        current=(yield from self._guard('byte_read',address,'0045dbdc'))&255
        requested=1 if enabled and current==0 else 0 if not enabled and current==1 else None
        if requested is not None:
            self.write_intents.append((address,1,requested))
            yield from self._call('byte_write','0045de4c',(requested,address))
        self.next_address=0x4581b9


@dataclass(frozen=True)
class GenieSettingsSyncObservation:
    settings: GenieSettingsObservation=field(default_factory=GenieSettingsObservation)
    sync: JailObservation=field(default_factory=JailObservation)
    def __post_init__(self):
        if not isinstance(self.settings,GenieSettingsObservation) or not isinstance(self.sync,JailObservation):
            raise ValueError('Typed settings and coupon-sync observations required')


@dataclass(frozen=True)
class GenieSettingsSyncPlan:
    complete: bool
    settings: object
    sync: object=None
    needed: object=None
    native_execution_verified: bool=False
    live_compatibility_verified: bool=False


class GenieSettingsSyncFrame:
    """Same-function fallthrough derives entry; fresh BA never comes from a cache."""
    def __init__(self,*,context=0x562194):
        self.settings=GenieSettingsFrame(context=context);self.context=context
        self.sync=self.sync_plan=self.final=None

    def advance(self,o):
        if not isinstance(o,GenieSettingsSyncObservation):raise ValueError('Typed Genie settings/sync composition required')
        if self.final is not None:return self.final
        p=self.settings.advance(o.settings)
        if not p.complete:return GenieSettingsSyncPlan(False,p,self.sync_plan,('settings',p.needed))
        assert p.next_address==0x458143
        if self.sync is None:self.sync=GenieCouponSyncFrame(context=self.context)
        self.sync_plan=self.sync.advance(replace(o.sync,entry_reached=True))
        result=GenieSettingsSyncPlan(self.sync_plan.complete,p,self.sync_plan,
                                     None if self.sync_plan.complete else ('sync',self.sync_plan.needed))
        if result.complete:self.final=result
        return result
