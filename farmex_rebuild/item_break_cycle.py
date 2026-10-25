"""Source item-break caller and clock plans, without game effects.

Inventory/NPC implementations remain opaque normal-return boundaries. The two
work bytes, time operands and action return are independent reached captures.
"""
from dataclasses import dataclass, replace

def _raw(value, bits):
    if value is not None and (type(value) is not int or not 0 <= value < 1 << bits):
        raise ValueError('Raw reached scalar required')

def _receipts(*values):
    if any(value is not None and type(value) is not bool for value in values):
        raise ValueError('Separate normal-return receipts required')

@dataclass(frozen=True)
class ItemBreakClockObservation:
    entry_reached: bool = False
    mode_dword: object = None
    first_tick_returned: object = None
    first_tick_dword: object = None
    last_tick_low: object = None
    last_tick_high: object = None
    speed_dword: object = None
    action_returned: object = None
    second_tick_returned: object = None
    second_tick_dword: object = None

    def __post_init__(self):
        if type(self.entry_reached) is not bool:
            raise ValueError('Explicit clock entry required')
        for value in (self.mode_dword, self.first_tick_dword, self.last_tick_low,
                      self.last_tick_high, self.speed_dword, self.second_tick_dword):
            _raw(value, 32)
        _receipts(self.first_tick_returned, self.action_returned, self.second_tick_returned)

@dataclass(frozen=True)
class ItemBreakCycleObservation:
    entry_reached: bool = False
    gate_561f60: object = None
    enabled_byte: object = None
    first_work_byte: object = None
    inventory_guard_returned: object = None
    second_work_byte: object = None
    npc_returned: object = None
    npc_eax: object = None
    clock_inputs: object = None
    clock_returned: object = None
    stop_returned: object = None
    npc_notice_span_returned: object = None

    def __post_init__(self):
        if type(self.entry_reached) is not bool:
            raise ValueError('Explicit post-prologue cycle entry required')
        for value in (self.gate_561f60, self.enabled_byte, self.first_work_byte, self.second_work_byte):
            _raw(value, 8)
        _raw(self.npc_eax, 32)
        _receipts(self.inventory_guard_returned, self.npc_returned, self.clock_returned,
                  self.stop_returned, self.npc_notice_span_returned)
        if self.clock_inputs is not None and not isinstance(self.clock_inputs, ItemBreakClockObservation):
            raise ValueError('Typed clock observations required')

@dataclass(frozen=True)
class ItemBreakCyclePlan:
    complete: bool
    status: str
    calls: tuple = ()
    stores: tuple = ()
    needed: object = None
    next_address: object = None
    elapsed_signed_qword: object = None
    threshold_signed_dword: object = None
    clock: object = None
    whole_function_verified: bool = False
    native_execution_verified: bool = False
    live_compatibility_verified: bool = False

class _Wait(Exception):
    pass

def _signed(value, bits):
    return value if value < 1 << (bits-1) else value - (1 << bits)

def _clock_plan(o):
    calls = []
    stores = []
    elapsed = threshold = None
    def result(status, needed=None):
        return ItemBreakCyclePlan(needed is None, status, tuple(calls), tuple(stores),
            needed, 0x471131 if needed is None else None, elapsed, threshold)
    def get(key):
        value = getattr(o,key)
        if value is None:
            raise _Wait(key)
        return value
    def normal(key, target, args=()):
        calls.append((target,args,key))
        if getattr(o,key) is not True:
            raise _Wait(key)
    try:
        if not o.entry_reached:
            raise _Wait('entry_reached')
        if get('mode_dword') != 0:
            return result('nonzero_mode_skips_clock')
        normal('first_tick_returned','GetTickCount')
        tick = get('first_tick_dword')
        low = get('last_tick_low')
        high = get('last_tick_high')
        # SUB/SBB uses a zero-extended GetTickCount minus the stored QWORD;
        # there is no DWORD-wrap-only elapsed normalization here.
        elapsed = _signed((tick - ((high << 32) | low)) & ((1 << 64)-1),64)
        threshold = _signed((get('speed_dword') * 1000) & 0xffffffff,32)
        if elapsed < threshold:
            return result('waiting')
        normal('action_returned','004ca9b0',(0x561ef8,))
        normal('second_tick_returned','GetTickCount')
        updated = get('second_tick_dword')
        stores.extend(((0x553d50,4,updated),(0x553d54,4,0)))
        return result('action_returned_clock_updated')
    except _Wait as wait:
        return result('needs_observation',str(wait))

def _cycle_plan(o, context, clock):
    calls = []
    clock_plan = None
    def result(status, needed=None):
        return ItemBreakCyclePlan(needed is None,status,tuple(calls),(),needed,
            0x471353 if needed is None else None,clock=clock_plan)
    def get(key):
        value = getattr(o,key)
        if value is None:
            raise _Wait(key)
        return value
    def normal(key,target,args=()):
        calls.append((target,args,key))
        if getattr(o,key) is not True:
            raise _Wait(key)
    try:
        if not o.entry_reached:
            raise _Wait('entry_reached')
        if get('gate_561f60') == 0:
            return result('outer_gate_zero')
        if get('enabled_byte') == 0:
            return result('settings_disabled')
        if get('first_work_byte') != 0:
            normal('inventory_guard_returned','00470f6c',(context,))
        if get('second_work_byte') == 0:
            return result('second_work_gate_zero')
        normal('npc_returned','00470d98',(context,))
        if get('npc_eax') & 255:
            calls.append(('004710d4',(context,),'clock_returned'))
            clock_plan = clock()
            if not clock_plan.complete:
                raise _Wait('clock_inputs')
            if o.clock_returned is not True:
                raise _Wait('clock_returned')
            return result('clock_child_returned')
        normal('stop_returned','0040ae0c',(0x561f34,0))
        # Two temporary constructors, notice and two cleanups remain one
        # explicitly opaque normal span; no fabricated native string pointers.
        normal('npc_notice_span_returned','004712f3..00471353',
               ('NPC Yakininda Olmalisiniz , Bot Durduruldu !','Bilgi'))
        return result('npc_zero_stop_notice_returned')
    except _Wait as wait:
        return result('needs_observation',str(wait))

class ItemBreakClockFrame:
    def __init__(self):
        self.observation = ItemBreakClockObservation()
        self.final = None
    def advance(self,incoming):
        if not isinstance(incoming,ItemBreakClockObservation):
            raise ValueError('Typed clock observations required')
        if self.final is not None:
            return self.final
        for _ in range(12):
            plan = _clock_plan(self.observation)
            if plan.complete:
                self.final = plan
                return plan
            value = getattr(incoming,plan.needed)
            if value is None or (plan.needed.endswith('_returned') or plan.needed=='entry_reached') and value is not True:
                return plan
            self.observation = replace(self.observation,**{plan.needed:value})
        raise AssertionError('Clock reached capture budget exceeded')

class ItemBreakCycleFrame:
    def __init__(self,*,context=0x569a20):
        _raw(context,32)
        if context is None:
            raise ValueError('Explicit source context required')
        self.context = context
        self.observation = ItemBreakCycleObservation()
        self.clock = ItemBreakClockFrame()
        self.final = None
    def advance(self,incoming):
        if not isinstance(incoming,ItemBreakCycleObservation):
            raise ValueError('Typed cycle observations required')
        if self.final is not None:
            return self.final
        for _ in range(14):
            plan = _cycle_plan(self.observation,self.context,
                lambda:self.clock.advance(incoming.clock_inputs or ItemBreakClockObservation()))
            if plan.complete:
                self.final = plan
                return plan
            if plan.needed=='clock_inputs':
                return plan
            value = getattr(incoming,plan.needed)
            if value is None or (plan.needed.endswith('_returned') or plan.needed=='entry_reached') and value is not True:
                return plan
            self.observation = replace(self.observation,**{plan.needed:value})
        raise AssertionError('Cycle reached capture budget exceeded')
