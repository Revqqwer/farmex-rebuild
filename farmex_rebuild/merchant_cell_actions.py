"""004b9784 normal-value click projection; all effects are inert intents.

Screen-X arithmetic, selected-index gate and effect order follow pinned source.
Helper normal returns, conversions and post-FSTP float bits are independent
observations. The one-shot plan is also consumed by an own prefix-caching
frame; neither executes native inputs, writes or sends.
"""
from dataclasses import dataclass,field,replace
from types import MappingProxyType
from merchant_result_filter import raw
from action_queue import QueueState
from private_chat_request import PrivateChatObservation,PrivateChatRequestFrame
from motion_genie_helpers import MotionGenieObservation,MotionGenieFrame


def signed32(value):return value if value<0x80000000 else value-0x100000000


@dataclass(frozen=True)
class MerchantCellState:
    active_byte: int=0
    busy_byte_0f: int=0
    def __post_init__(self):
        raw(self.active_byte,8,'active byte');raw(self.busy_byte_0f,8,'busy byte')


@dataclass(frozen=True)
class MerchantCellObservation:
    selected_index_dword: object=None
    cursor_x_dword: object=None
    form_left_dword: object=None
    list_left_dword: object=None
    cursor_result_dword: object=None
    caption_unicode: object=None
    caption_ansi: object=None
    x_unicode: object=None
    y_unicode: object=None
    x_float32_bits: object=None
    y_float32_bits: object=None
    normal_returns: object=field(default_factory=dict)
    caption_ansi_dword: object=None
    private_chat_inputs: object=None
    movement_inputs: object=None
    def __post_init__(self):
        for name in ('selected_index_dword','cursor_x_dword','form_left_dword','list_left_dword',
                     'cursor_result_dword','x_float32_bits','y_float32_bits','caption_ansi_dword'):
            v=getattr(self,name)
            if v is not None:raw(v,32,name)
        for name in ('caption_unicode','x_unicode','y_unicode'):
            v=getattr(self,name)
            if v is not None and type(v) is not str:raise ValueError('Explicit decoded Unicode text required')
        if self.caption_ansi is not None and type(self.caption_ansi) is not bytes:
            raise ValueError('Explicit immutable converted caption bytes required')
        returns=dict(self.normal_returns)
        if any(type(v) is not bool for v in returns.values()):raise ValueError('Separate normal-return observations required')
        object.__setattr__(self,'normal_returns',MappingProxyType(returns))
        if self.private_chat_inputs is not None and not isinstance(self.private_chat_inputs,PrivateChatObservation):
            raise ValueError('Typed private-chat child observations required')
        if self.movement_inputs is not None and not isinstance(self.movement_inputs,MotionGenieObservation):
            raise ValueError('Typed movement child observations required')


@dataclass(frozen=True)
class MerchantEnableIntent:
    form_field_offset: int
    enabled_byte: int
    normal_return_observed: bool


@dataclass(frozen=True)
class MerchantCellPlan:
    complete: bool
    status: str
    state: MerchantCellState
    action: object=None
    selected_index: object=None
    relative_x_dword: object=None
    steps: tuple=()
    ui_enables: tuple=()
    private_chat_target: object=None
    private_chat_context: object=None
    movement_push_order: tuple=()
    needed: object=None
    native_execution_verified: bool=False
    delivery_verified: bool=False
    live_compatibility_verified: bool=False
    queue: object=None
    private_chat_plan: object=None
    movement_plan: object=None


class _Missing(Exception):
    def __init__(self,kind,key):self.needed=(kind,key)


def plan_merchant_cell_click(state,observation):
    if not isinstance(state,MerchantCellState) or not isinstance(observation,MerchantCellObservation):
        raise ValueError('Typed own cell state and observations required')
    o=observation;steps=[];enables=[];action=None;selected=None;relative=None;pm=None;pushes=()
    def result(complete,status,needed=None):
        return MerchantCellPlan(complete,status,state,action,selected,relative,tuple(steps),tuple(enables),
            pm,0x561ef8 if pm is not None else None,pushes,needed)
    def need(name):
        steps.append(('value',name))
        value=getattr(o,name)
        if value is None:raise _Missing('value',name)
        return value
    def normal(label,target,args=()):
        steps.append(('normal',label,target,args))
        if o.normal_returns.get(label) is not True:raise _Missing('normal',label)
    try:
        normal('selected_index','ListView.virtual+0x130')
        selected=signed32(need('selected_index_dword'))
        if selected<0:return result(True,'no_selected_row')
        normal('cursor_pos','GetCursorPos')
        # Source ignores BOOL and reads only POINT.x. Never fabricate x=0 for
        # a failed call; its explicit observed local value is still required.
        normal('form_left','TCustomForm.GetLeft')
        left=need('form_left_dword');list_left=need('list_left_dword')
        cursor=need('cursor_x_dword')
        relative=(cursor-((left+list_left)&0xffffffff))&0xffffffff
        value=signed32(relative)
        if 0x2df<=value<=0x307:action='private_chat'
        elif 0x30c<=value<=0x334:action='move_to_seller'
        else:return result(True,'outside_action_windows')
        if action=='private_chat':
            normal('pm_caption','0045f7f4',(selected,))
            caption=need('caption_unicode')
            normal('pm_conversion','004073a0',(caption,0))
            pm=need('caption_ansi')
            normal('private_chat','004ca220',(0x561ef8,pm))
            normal('pm_ansi_cleanup','004040f8')
            normal('pm_unicode_cleanup','00505c64')
            return result(True,'own_private_chat_projection')
        state=replace(state,active_byte=0)
        steps.append(('store','context+0',1,0))
        state=replace(state,busy_byte_0f=0)
        steps.append(('store','context+0x0f',1,0))
        # Pinned TButton/TControl VMT+94 resolves SetEnabled. Actual loaded
        # form objects/overrides and nested control events remain unverified.
        for offset,enabled in ((0xb64,1),(0xb68,0),(0xb6c,1)):
            label='enable_%x'%offset
            enables.append(MerchantEnableIntent(offset,enabled,o.normal_returns.get(label) is True))
            normal(label,'Control.virtual+0x94',(offset,enabled))
        normal('x_text','0045f6e0',(selected,5));x_text=need('x_unicode')
        normal('x_float','StrToFloat',(x_text,));x=need('x_float32_bits')
        steps.append(('FSTP32','x',x));normal('x_cleanup','00505c64')
        normal('y_text','0045f6e0',(selected,6));y_text=need('y_unicode')
        normal('y_float','StrToFloat',(y_text,));y=need('y_float32_bits')
        steps.append(('FSTP32','y',y));normal('y_cleanup','00505c64')
        pushes=(y,x)
        normal('movement','004646b4',pushes)
        return result(True,'own_movement_projection')
    except _Missing as error:
        return result(False,'needs_observation',error.needed)


class MerchantCellFrame:
    """Cache only demanded prefix inputs; compose optional typed child frames.

    The pure plan is replayed, not executed. UI/store intents are snapshots;
    callers must not treat every returned step as a fresh native instruction.
    Child completion never supplies the separate parent normal-return receipt.
    """
    def __init__(self,state=None,queue=None,*,bind_private_chat=True,bind_movement=True):
        self.initial=MerchantCellState() if state is None else state
        self.queue=QueueState() if queue is None else queue
        if not isinstance(self.initial,MerchantCellState) or not isinstance(self.queue,QueueState):
            raise ValueError('Own typed state and queue required')
        if type(bind_private_chat) is not bool or type(bind_movement) is not bool:
            raise ValueError('Explicit child binding booleans required')
        self.bind_private_chat=bind_private_chat;self.bind_movement=bind_movement
        self.observation=MerchantCellObservation();self.private_child=None;self.motion_child=None
        self.private_plan=None;self.motion_plan=None;self.final=None

    def _decorate(self,p,needed=None):
        return replace(p,queue=self.queue,private_chat_plan=self.private_plan,movement_plan=self.motion_plan,
            complete=False if needed is not None else p.complete,
            status='needs_observation' if needed is not None else p.status,
            needed=p.needed if needed is None else needed)

    def advance(self,o):
        if not isinstance(o,MerchantCellObservation):raise ValueError('Typed cell observations required')
        if self.final is not None:return self.final
        for _ in range(96):
            p=plan_merchant_cell_click(self.initial,self.observation)
            if p.complete:
                self.final=self._decorate(p)
                return self.final
            kind,key=p.needed
            if kind=='value':
                value=getattr(o,key)
                if value is None:return self._decorate(p)
                self.observation=replace(self.observation,**{key:value})
                continue
            if key=='private_chat' and self.bind_private_chat:
                if self.private_child is None:
                    handle=o.caption_ansi_dword
                    if handle is None:return self._decorate(p,('value','caption_ansi_dword'))
                    self.private_child=PrivateChatRequestFrame(handle,self.queue,context=p.private_chat_context)
                self.private_plan=self.private_child.advance(o.private_chat_inputs or PrivateChatObservation())
                self.queue=self.private_plan.queue
                if not self.private_plan.complete:
                    return self._decorate(p,('private_chat',self.private_plan.needed))
            elif key=='movement' and self.bind_movement:
                if self.motion_child is None:self.motion_child=MotionGenieFrame('004646b4',p.movement_push_order)
                self.motion_plan=self.motion_child.advance(o.movement_inputs or MotionGenieObservation())
                if not self.motion_plan.complete:
                    return self._decorate(p,('movement',self.motion_plan.request))
            if o.normal_returns.get(key) is not True:return self._decorate(p)
            self.observation=replace(self.observation,normal_returns={**self.observation.normal_returns,key:True})
        raise ValueError('Cell frame exceeded bounded prefix budget')
