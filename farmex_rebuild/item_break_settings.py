"""Bounded 00470cd5..00470d87 settings replay; scalar/call plans only.

The fresh enable read follows opaque VCL/cleanup calls and must not be inferred
from the earlier store. Normal helper receipts never certify game effects.
"""
from dataclasses import dataclass, field, replace
from protection_settings import (
    ProtectionSettingsFrame, ProtectionSettingsObservation,
    plan_protection_settings,
)

OPS = (('flag', 0xec0, 0), ('number', 0xec8, 4, 1))
ITEM_BREAK_FIELDS = (
    (0xec0, 'frmMain/MainTab/sheetCrash/GroupBox20/chAutoCrashItems'),
    (0xec8, 'frmMain/MainTab/sheetCrash/GroupBox20/txtCrashItemSpeed'),
    (0xa28, 'frmMain/MainTab/sheetCrash/GroupBox14/rdAbbys'),
)

def _prefix_plan(observation, *, context=0x569a20, _child=None):
    return plan_protection_settings(
        observation, context=context, _child=_child, _ops=OPS,
        _entry='00470cd5', _exit=0x470d3e, _prologue=False,
    )

class _PrefixFrame(ProtectionSettingsFrame):
    _planner = staticmethod(_prefix_plan)

@dataclass(frozen=True)
class ItemBreakSettingsObservation:
    settings: object = field(default_factory=ProtectionSettingsObservation)
    reset_checked_returned: object = None
    reset_checked_eax: object = None
    fresh_enabled_byte: object = None
    toggle_returned: object = None

    def __post_init__(self):
        if not isinstance(self.settings, ProtectionSettingsObservation):
            raise ValueError('Typed settings prefix required')
        for value in (self.reset_checked_returned, self.toggle_returned):
            if value is not None and type(value) is not bool:
                raise ValueError('Separate getter/toggle normal receipts required')
        for value, bits in ((self.reset_checked_eax, 32), (self.fresh_enabled_byte, 8)):
            if value is not None and (type(value) is not int or not 0 <= value < 1 << bits):
                raise ValueError('Raw reached getter or enable operand required')

@dataclass(frozen=True)
class ItemBreakSettingsPlan:
    complete: bool
    settings: object
    calls: tuple = ()
    stores: tuple = ()
    needed: object = None
    next_address: object = None
    toggle_argument: object = None
    toggle_physical_pushes: tuple = ()
    whole_function_verified: bool = False
    lexical_conversion_verified: bool = False
    native_execution_verified: bool = False
    live_compatibility_verified: bool = False

def _suffix(prefix, context, observation):
    calls = list(prefix.calls)
    stores = list(prefix.stores)
    argument = None
    pushes = ()

    def result(needed=None):
        return ItemBreakSettingsPlan(
            needed is None, prefix, tuple(calls), tuple(stores), needed,
            0x470d87 if needed is None else None, argument, pushes,
        )

    calls.append(('VCL_Checked_getter_span', ('form_field', 0xa28), 'reset_checked_a28'))
    if observation.reset_checked_returned is not True:
        return result('reset_checked_returned')
    if observation.reset_checked_eax is None:
        return result('reset_checked_eax')
    if observation.reset_checked_eax & 0xff:
        stores.append(((context + 0xc) & 0xffffffff, 4, 0))
    if observation.fresh_enabled_byte is None:
        return result('fresh_enabled_byte')
    argument = int(observation.fresh_enabled_byte != 0)
    pushes = (argument, 0x561f34)
    calls.append(('0040ae0c', (0x561f34, argument), 'toggle_returned'))
    if observation.toggle_returned is not True:
        return result('toggle_returned')
    return result()

class ItemBreakSettingsFrame:
    """Reached-only capture; completed prefix/suffix are retained across gaps."""
    def __init__(self, *, context=0x569a20):
        self.context = context
        self.prefix = _PrefixFrame(context=context)
        self.observation = ItemBreakSettingsObservation()
        self.final = None

    def advance(self, incoming):
        if not isinstance(incoming, ItemBreakSettingsObservation):
            raise ValueError('Typed item-break observations required')
        if self.final is not None:
            return self.final
        prefix = self.prefix.advance(incoming.settings)
        if not prefix.complete:
            return ItemBreakSettingsPlan(False, prefix, prefix.calls, prefix.stores,
                                         ('settings', prefix.needed))
        for _ in range(5):
            plan = _suffix(prefix, self.context, self.observation)
            if plan.complete:
                self.final = plan
                return plan
            value = getattr(incoming, plan.needed)
            if value is None or (plan.needed.endswith('_returned') and value is not True):
                return plan
            self.observation = replace(self.observation, **{plan.needed: value})
        raise AssertionError('Item-break suffix capture budget exceeded')
