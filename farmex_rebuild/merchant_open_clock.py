"""Pure BUY phase4 clock gate at 422c9e..422cca; no timeout effects."""
from dataclasses import dataclass

@dataclass(frozen=True)
class BuyOpenClockSample:
    tick_dword:int
    pending_stamp_qword:int
    def __post_init__(self):
        for name,bits in (('tick_dword',32),('pending_stamp_qword',64)):
            value=getattr(self,name)
            if type(value) is not int or not 0<=value<1<<bits:raise ValueError('Raw source clock field required: '+name)

@dataclass(frozen=True)
class BuyOpenWaitPlan:
    status:str
    elapsed_bits:object=None
    elapsed_signed:object=None
    timeout_due:object=None
    remaining_ms:object=None
    independently_verified:bool=False

def plan_buy_open_wait(pending_byte,sample=None):
    if type(pending_byte) is not int or not 0<=pending_byte<=255:raise ValueError('Raw pending BYTE required')
    if sample is not None and not isinstance(sample,BuyOpenClockSample):raise ValueError('Typed source clock required')
    if pending_byte==0:return BuyOpenWaitPlan('clear_path',timeout_due=False)
    if sample is None:return BuyOpenWaitPlan('needs_clock')
    # XOR EDX,EDX; SUB EAX,stamp.low; SBB EDX,stamp.high.
    bits=(sample.tick_dword-sample.pending_stamp_qword)&0xffffffffffffffff
    elapsed=bits if bits<1<<63 else bits-(1<<64)
    # EDX==0: unsigned low comparison; otherwise signed EDX<0 waits.
    due=elapsed>=10000
    return BuyOpenWaitPlan('timeout_path' if due else 'waiting',bits,elapsed,due,
                          None if due else 10000-elapsed)

# The same SUB/SBB/signed-high/unsigned-low gate is verified for SELL phase5.
MerchantWaitClockSample=BuyOpenClockSample
plan_merchant_open_wait=plan_buy_open_wait
