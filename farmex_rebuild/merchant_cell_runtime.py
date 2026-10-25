"""Owned semantic PM/GIT cell actions; no source HWNDs or native receipts.

This frontend uses table column identity. The original hardcoded screen-X
handler remains a separate source model with unverified geometry/ABI.
"""
from dataclasses import dataclass
from action_queue import QueueState,enqueue
from merchant_cell_actions import MerchantCellState
from merchant_result_rows import MerchantResultRow
from merchant_coordinate_float import plan_merchant_coordinate_float


@dataclass(frozen=True)
class OwnedMerchantCellResult:
    complete: bool
    status: str
    action: object
    state: MerchantCellState
    queue: QueueState
    record_index: object=None
    payload: object=None
    conversion: object=None
    coordinate_plans: tuple=()
    movement_push_order: tuple=()
    source_cell_frame_executed: bool=False
    native_execution_verified: bool=False
    delivery_verified: bool=False
    live_compatibility_verified: bool=False


class OwnedMerchantCells:
    def __init__(self,queue=None):
        self.queue=QueueState() if queue is None else queue
        if not isinstance(self.queue,QueueState):raise ValueError('Own queue required')
        self.state=MerchantCellState();self.movements=();self.last=None

    def activate(self,row,column,*,codec_factory=None,codepage_reader=None,clock=None,admission_gate=1):
        if row is not None and not isinstance(row,MerchantResultRow):raise ValueError('Typed current row required')
        if type(column) is not int or not 0<=column<1<<32:raise ValueError('Own column index required')
        action=None;payload=None;conversion=None;coordinates=[];pushes=()
        def result(ok,status):
            self.last=OwnedMerchantCellResult(ok,status,action,self.state,self.queue,
                None if row is None else row.record_index,payload,conversion,tuple(coordinates),pushes)
            return self.last
        if row is None:return result(True,'no_selected_row')
        if column not in (4,5):return result(True,'not_action_column')
        if column==4:
            action='private_chat'
            if not callable(codec_factory) or not callable(codepage_reader):return result(False,'needs_local_caption_codec')
            try:
                codec=codec_factory(codepage_reader())
                encoded,used=codec.encode(row.caption)
                if type(encoded) is not bytes:raise ValueError('Own codec must return immutable bytes')
                conversion=(codec.code_page,encoded,used)
            except (OSError,ValueError) as error:return result(False,'local_caption_conversion:'+str(error))
            name=encoded.split(b'\0',1)[0]
            if len(name)>100:return result(False,'unresolved_source_stack_alias_copy')
            payload=b'\x35\x01'+len(name).to_bytes(2,'little')+name
            if admission_gate is None:return result(False,'needs_own_queue_gate')
            tick=None
            if admission_gate:
                if not callable(clock):return result(False,'needs_own_clock')
                tick=clock()
            decision=enqueue(self.queue,payload,len(payload),0,admission_gate,tick)
            if decision.state is None:return result(False,decision.status)
            self.queue=decision.state
            return result(True,decision.status)
        action='move_to_seller'
        # Own state writes follow source ordering, while native UI enable
        # receipts/scan-session effects remain in the separate source model.
        self.state=MerchantCellState(0,0)
        if len(row.subitems)<7:return result(False,'needs_coordinate_columns')
        for index in (5,6):
            p=plan_merchant_coordinate_float(row.subitems[index]);coordinates.append(p)
            if not p.complete:return result(False,'coordinate:'+p.status)
        pushes=(coordinates[1].float32_bits,coordinates[0].float32_bits)
        self.movements+=((row.record_index,pushes),)
        return result(True,'own_movement_target_prepared')
