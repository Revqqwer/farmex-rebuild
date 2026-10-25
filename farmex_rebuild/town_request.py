"""Pinned client48 stop branch; inert own packet snapshot, no hook or IO."""
from dataclasses import dataclass,replace
from jail_preload import JailPreloadFrame
from jail_protection import JailObservation
from profile_numeric import CURRENT_SOURCE

@dataclass(frozen=True)
class TownRequestPlan:
 complete:bool
 reads:tuple=()
 calls:tuple=()
 needed:object=None
 next_address:object=None
 planned_eax:object=None
 source_ret_pop_bytes:object=None
 source_sha256:str=CURRENT_SOURCE
 whole_handler_verified:bool=False
 native_execution_verified:bool=False
 live_compatibility_verified:bool=False

class TownRequestFrame(JailPreloadFrame):
 def __init__(self,packet,*,source_sha256=CURRENT_SOURCE):
  if type(packet) is not bytes or not packet:raise ValueError('Nonempty immutable owned packet required')
  if source_sha256!=CURRENT_SOURCE:raise ValueError('Pinned current Town source required')
  self.packet=packet;self.next_address=self.planned_eax=self.ret_pop=None
  super().__init__()
 def _run(self):
  yield ('entry','004e35de')
  if self.packet[0]!=0x48:
   self.next_address=0x4e361b;return
  self.reads.append((0x562252,1,'town_request_stop_byte'))
  enabled=yield from self._value('town_request_stop_byte')
  if enabled:yield from self._call('town_request_stop','0040ae0c',(0,0x561f34))
  # Normal MOV EAX1 / saved-FS restore / jump / stack epilogue / RET0xc.
  # These are planned bits, not native ABI or exception-path evidence.
  self.planned_eax=1;self.ret_pop=12;self.next_address=0x4e3ca7
 def _plan(self,complete=False):
  return TownRequestPlan(complete,tuple(self.reads),tuple(self.calls),None if complete else self._needed,
                         self.next_address,self.planned_eax,self.ret_pop)

# Source byte0 compare chain: address, opcode, match body, nonmatch header.
PREFIX_CASES=((0x4e315e,0x06,0x4e3163,0x4e319d),
 (0x4e31a4,0x10,0x4e31a9,0x4e3203),(0x4e320a,0x20,0x4e3213,0x4e34af),
 (0x4e34b6,0x33,0x4e34bf,0x4e35de))

@dataclass(frozen=True)
class TownRequestDispatchPlan:
 complete:bool
 status:str
 opcode_reads:tuple=()
 child:object=None
 source_return_dword:object=None
 source_ret_pop_bytes:object=None
 next_address:object=None
 needed:object=None
 whole_dispatcher_verified:bool=False
 native_execution_verified:bool=False
 live_compatibility_verified:bool=False

class TownRequestDispatchFrame:
 def __init__(self,packet):
  if type(packet) is not bytes:raise ValueError('Immutable owned packet snapshot required')
  self.packet=packet;self.setup=False;self.child=self.final=None
 def advance(self,o,*,dispatcher_setup_returned=None):
  if not isinstance(o,JailObservation):raise ValueError('Typed Town observations required')
  if dispatcher_setup_returned is not None and type(dispatcher_setup_returned) is not bool:
   raise ValueError('Separate prologue normal receipt required')
  if self.final is not None:return self.final
  if not self.setup:
   if dispatcher_setup_returned is not True:return TownRequestDispatchPlan(False,'needs_dispatcher_setup',needed=('normal','004e3144_prologue'))
   self.setup=True
  if not self.packet:return TownRequestDispatchPlan(False,'unsupported_packet_span',needed=('unsupported','packet_byte0'))
  opcode=self.packet[0];reads=[]
  for address,case,body,continuation in PREFIX_CASES:
   reads.append((address,opcode,case))
   if opcode==case:return TownRequestDispatchPlan(False,'earlier_branch_not_bound',tuple(reads),next_address=body)
  if self.child is None:self.child=TownRequestFrame(self.packet)
  child=self.child.advance(replace(o,entry_reached=True))
  if not child.complete:return TownRequestDispatchPlan(False,'needs_town_observation',tuple(reads),child,needed=child.needed)
  if opcode!=0x48:return TownRequestDispatchPlan(False,'later_branch_not_bound',tuple(reads),child,next_address=child.next_address)
  self.final=TownRequestDispatchPlan(True,'town_normal_source_return',tuple(reads),child,
                                    child.planned_eax,child.source_ret_pop_bytes,child.next_address)
  return self.final
