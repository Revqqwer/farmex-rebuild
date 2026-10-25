"""Stable owned packet -> source nonmatching opcode chain -> TP model.

No real packet object/pointer, hook, memory read or game call is installed.
Other matching branches stop at their actual body rather than bypassing them.
"""
from dataclasses import dataclass,replace
from teleport_protection import TPFrame,TPObservation

# (comparison address, opcode, matched body, nonmatch continuation)
PREFIX_CASES=(
 (0x4d82c7,0x08,0x4d82d0,0x4d83a1),
 (0x4d83ab,0x10,0x4d83b4,0x4d8492),
 (0x4d849c,0x11,0x4d84a1,0x4d84f7),
 (0x4d8501,0x12,0x4d850a,0x4d85b1),
 (0x4d85bb,0x14,0x4d85c0,0x4d85d1),
 (0x4d85db,0x15,0x4d85e0,0x4d861c),
 (0x4d8626,0x17,0x4d862b,0x4d865c),
 (0x4d8666,0x18,0x4d866b,0x4d869c),
 (0x4d86a6,0x1a,0x4d86ab,0x4d86dc),
 (0x4d86e6,0x1b,0x4d86eb,0x4d871c),
 (0x4d8726,0x21,0x4d872f,0x4d8808),
 (0x4d8812,0x23,0x4d8817,0x4d885a),
 (0x4d8864,0x24,0x4d8869,0x4d889f),
 (0x4d88a9,0x26,0x4d88ae,0x4d88e4))

@dataclass(frozen=True)
class IncomingTPDispatchPlan:
    complete:bool
    status:str
    opcode_reads:tuple=()
    child:object=None
    source_return_dword:object=None
    source_ret_pop_bytes:object=None
    next_address:object=None
    missing:str=''
    whole_dispatcher_verified:bool=False
    native_execution_verified:bool=False
    live_compatibility_verified:bool=False

class IncomingTPDispatchFrame:
    def __init__(self,packet):
        if type(packet) is not bytes:raise ValueError('Immutable owned packet snapshot required')
        self.packet=packet;self.setup=False;self.child=None;self.final=None
    def advance(self,o,*,dispatcher_setup_returned=None):
        if not isinstance(o,TPObservation):raise ValueError('Typed TP child observations required')
        if dispatcher_setup_returned is not None and type(dispatcher_setup_returned) is not bool:
            raise ValueError('Separate dispatcher prologue normal receipt required')
        if self.final is not None:return self.final
        if not self.setup:
            if dispatcher_setup_returned is not True:
                return IncomingTPDispatchPlan(False,'needs_dispatcher_setup',missing='004d82a4 prologue normal return')
            self.setup=True
        if not self.packet:return IncomingTPDispatchPlan(False,'unsupported_packet_span',missing='packet byte0 unavailable')
        reads=[];opcode=self.packet[0]
        for address,case,body,continuation in PREFIX_CASES:
            reads.append((address,opcode,case))
            if opcode==case:
                return IncomingTPDispatchPlan(False,'earlier_branch_not_bound',tuple(reads),
                    next_address=body,missing='Earlier opcode%02x body must be modeled separately'%case)
        if self.child is None:self.child=TPFrame('event',packet=self.packet)
        # All14 failed comparisons jump through side-effect-free compare
        # headers to004d88e4. Child entry is derived, not caller asserted.
        child=self.child.advance(replace(o,entry_reached=True))
        if not child.complete:
            return IncomingTPDispatchPlan(False,'needs_tp_observation',tuple(reads),child,missing=child.missing)
        if opcode!=0x27:
            return IncomingTPDispatchPlan(False,'later_branch_not_bound',tuple(reads),child,
                next_address=child.next_address,missing='Later dispatcher branches outside this TP composition')
        if child.next_address!=0x4d8a84 or child.planned_eax!=1:
            raise AssertionError('TP child did not reach the verified EAX1 tail')
        # MOV EAX1, saved-FS restore, direct jump to MOV ESP/POP EBP/RET4.
        # These are normal source result bits only, not executed ABI evidence.
        self.final=IncomingTPDispatchPlan(True,'tp_normal_source_return',tuple(reads),child,
            source_return_dword=1,source_ret_pop_bytes=4,next_address=0x4d9233)
        return self.final
