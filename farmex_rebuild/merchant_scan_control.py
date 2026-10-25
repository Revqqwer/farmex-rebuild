"""004b8f2c settings and004be6dc start/stop normal-value projections.

All native helpers/virtual operations/conversions are observed normal returns,
not executed effects. This one-shot snapshot planner is not a resumable frame.
"""
from dataclasses import dataclass,field,replace
from types import MappingProxyType
from merchant_result_filter import raw


def signed32(v):return v if v<0x80000000 else v-0x100000000
def normals(value):
    result=dict(value)
    if any(type(v) is not bool for v in result.values()):raise ValueError('Separate normal-return receipts required')
    return MappingProxyType(result)


@dataclass(frozen=True)
class MerchantScanOptions:
    view_mode_dword: int=0
    sell_byte: int=0
    buy_byte: int=0
    save_byte: int=0
    route_byte: int=0
    def __post_init__(self):
        raw(self.view_mode_dword,32,'view mode')
        for v in (self.sell_byte,self.buy_byte,self.save_byte,self.route_byte):raw(v,8,'setting byte')


@dataclass(frozen=True)
class ScanSettingsObservation:
    combo_index_dword: object=None
    sell_checked_eax: object=None
    buy_checked_eax: object=None
    save_checked_eax: object=None
    route_checked_eax: object=None
    normal_returns: object=field(default_factory=dict)
    def __post_init__(self):
        for v in (self.combo_index_dword,self.sell_checked_eax,self.buy_checked_eax,self.save_checked_eax,self.route_checked_eax):
            if v is not None:raw(v,32,'UI getter EAX')
        object.__setattr__(self,'normal_returns',normals(self.normal_returns))


@dataclass(frozen=True)
class ScanSettingsPlan:
    complete: bool
    status: str
    options: MerchantScanOptions
    steps: tuple=()
    needed: object=None
    native_execution_verified: bool=False


class _Missing(Exception):
    def __init__(self,kind,key):self.needed=(kind,key)


def plan_scan_settings(previous,o=None):
    if not isinstance(previous,MerchantScanOptions):raise ValueError('Typed previous options required')
    o=ScanSettingsObservation() if o is None else o
    if not isinstance(o,ScanSettingsObservation):raise ValueError('Typed settings observations required')
    state=previous;steps=[]
    try:
        for label,field_name,input_name,offset in (
            ('combo','view_mode_dword','combo_index_dword',8),('sell','sell_byte','sell_checked_eax',0xc),
            ('buy','buy_byte','buy_checked_eax',0xd),('save','save_byte','save_checked_eax',0xe),
            ('route','route_byte','route_checked_eax',1)):
            steps.append(('getter',label))
            if o.normal_returns.get(label) is not True:raise _Missing('normal',label)
            value=getattr(o,input_name)
            if value is None:raise _Missing('value',input_name)
            value=int(signed32(value)>0) if label=='combo' else value&255
            state=replace(state,**{field_name:value});steps.append(('store',offset,value))
        return ScanSettingsPlan(True,'own_settings_projected',state,tuple(steps))
    except _Missing as e:return ScanSettingsPlan(False,'needs_observation',state,tuple(steps),e.needed)


def plan_scan_settings_callback(previous,gate_byte,o=None):
    if not isinstance(previous,MerchantScanOptions):raise ValueError('Typed previous options required')
    if gate_byte is None:return ScanSettingsPlan(False,'needs_observation',previous,needed=('value','initialization_gate'))
    raw(gate_byte,8,'initialization gate')
    if gate_byte==0:return ScanSettingsPlan(True,'initialization_gate_closed',previous)
    return plan_scan_settings(previous,o)


@dataclass(frozen=True)
class ScanRouteRowObservation:
    x_unicode: object=None
    y_unicode: object=None
    x_eax: object=None
    y_eax: object=None
    size_dword: object=None
    capacity_dword: object=None
    fast_new_end_eax: object=None
    normal_returns: object=field(default_factory=dict)
    def __post_init__(self):
        for v in (self.x_unicode,self.y_unicode):
            if v is not None and type(v) is not str:raise ValueError('Explicit Unicode route text required')
        for v in (self.x_eax,self.y_eax,self.size_dword,self.capacity_dword,self.fast_new_end_eax):
            if v is not None:raw(v,32,'route scalar EAX')
        object.__setattr__(self,'normal_returns',normals(self.normal_returns))


@dataclass(frozen=True)
class ScanControlState:
    options: MerchantScanOptions=field(default_factory=MerchantScanOptions)
    active_byte: int=0
    busy_byte_0f: int=0
    route_index_dword: int=0
    vector_78: tuple=()
    vector_58: tuple=()
    route_points: tuple=()
    result_records: tuple=()
    button_enabled: tuple=(1,0,1)
    status_text: object=None
    def __post_init__(self):
        if not isinstance(self.options,MerchantScanOptions):raise ValueError('Typed scan options required')
        raw(self.active_byte,8,'active');raw(self.busy_byte_0f,8,'busy');raw(self.route_index_dword,32,'route index')
        for seq in (self.vector_78,self.vector_58,self.route_points,self.result_records):
            if type(seq) is not tuple:raise ValueError('Immutable own vector snapshots required')
        if type(self.button_enabled) is not tuple or len(self.button_enabled)!=3:raise ValueError('Three own UI states required')
        for v in self.button_enabled:raw(v,8,'button byte')
        if self.status_text is not None and type(self.status_text) is not str:raise ValueError('Explicit own status text required')


@dataclass(frozen=True)
class ScanControlObservation:
    entry_reached: bool=False
    sell_checked_eax: object=None
    buy_checked_eax: object=None
    row_counts: tuple=()
    rows: tuple=()
    normal_returns: object=field(default_factory=dict)
    def __post_init__(self):
        if type(self.entry_reached) is not bool:raise ValueError('Explicit post-prologue entry required')
        for v in (self.sell_checked_eax,self.buy_checked_eax):
            if v is not None:raw(v,32,'live checkbox getter')
        if type(self.row_counts) is not tuple or type(self.rows) is not tuple:raise ValueError('Ordered route observations required')
        for v in self.row_counts:raw(v,32,'fresh signed row count')
        if any(not isinstance(r,ScanRouteRowObservation) for r in self.rows):raise ValueError('Typed route rows required')
        object.__setattr__(self,'normal_returns',normals(self.normal_returns))


@dataclass(frozen=True)
class ScanControlPlan:
    complete: bool
    status: str
    state: ScanControlState
    steps: tuple=()
    needed: object=None
    forced_combo_index: object=None
    native_execution_verified: bool=False
    live_compatibility_verified: bool=False


def plan_scan_start_stop(previous,start_byte,completed_byte,o=None):
    if not isinstance(previous,ScanControlState):raise ValueError('Typed own scan control state required')
    raw(start_byte,8,'start');raw(completed_byte,8,'completed')
    o=ScanControlObservation() if o is None else o
    if not isinstance(o,ScanControlObservation):raise ValueError('Typed control observations required')
    state=previous;steps=[];forced=None
    def out(ok,status,needed=None):return ScanControlPlan(ok,status,state,tuple(steps),needed,forced)
    def normal(label,target='opaque helper'):
        steps.append(('normal',label,target))
        if o.normal_returns.get(label) is not True:raise _Missing('normal',label)
    def value(v,label):
        if v is None:raise _Missing('value',label)
        return v
    def buttons(values):
        nonlocal state
        for i,(offset,enabled) in enumerate(zip((0xb64,0xb68,0xb6c),values)):
            normal('enable_%x'%offset,'SetEnabled:'+str(enabled))
            updated=list(state.button_enabled);updated[i]=enabled
            state=replace(state,button_enabled=tuple(updated))
    try:
        if not o.entry_reached:raise _Missing('entry','004be6f0')
        if start_byte:
            for field_name in ('vector_78','vector_58','route_points'):
                for part in ('end','begin','erase'):normal('clear_'+field_name+'_'+part)
                state=replace(state,**{field_name:()});steps.append(('clear',field_name))
            state=replace(state,route_index_dword=0);steps.append(('store',4,0))
            for part in ('end','begin','erase'):normal('clear_result_records_'+part)
            state=replace(state,result_records=());steps.append(('clear','result_records'))
            normal('result_list_clear','ListView.virtual+0x13c')
            buttons((0,1,0))
            normal('sell_checked');sell=value(o.sell_checked_eax,'sell_checked_eax')&255
            if sell==0:
                normal('buy_checked');buy=value(o.buy_checked_eax,'buy_checked_eax')&255
                if buy==1:
                    forced=1;normal('select_buying','ComboBox.virtual+0x134')
                    state=replace(state,options=replace(state.options,view_mode_dword=1))
                    steps.append(('store',8,1))
            if state.options.route_byte:
                index=0
                while True:
                    normal('row_count:'+str(index),'TListItems.GetCount')
                    if index>=len(o.row_counts):raise _Missing('route_count',index)
                    if signed32(o.row_counts[index])<=signed32(index):break
                    if index>=len(o.rows):raise _Missing('route_row',index)
                    row=o.rows[index]
                    def rn(label):
                        steps.append(('route_normal',index,label))
                        if row.normal_returns.get(label) is not True:raise _Missing('route_normal',(index,label))
                    def rv(field_name):
                        v=getattr(row,field_name)
                        if v is None:raise _Missing('route_value',(index,field_name))
                        return v
                    rn('x_text');rv('x_unicode');rn('x_parse');x=rv('x_eax');rn('x_cleanup')
                    rn('y_text');rv('y_unicode');rn('y_parse');y=rv('y_eax');rn('y_cleanup')
                    rn('size');size=rv('size_dword');rn('capacity');capacity=rv('capacity_dword')
                    if size<capacity:
                        rn('fast_append');steps.append(('route_copy_pending_end',index,x,y))
                        end=rv('fast_new_end_eax');steps.append(('route_end_store',end))
                    else:
                        rn('grow_end')
                        rn('grow_append')
                    state=replace(state,route_points=state.route_points+((x,y),))
                    index=(index+1)&0xffffffff
            state=replace(state,active_byte=1);steps.append(('store',0,1))
            text='Taraniyor...'
        else:
            state=replace(state,active_byte=0);steps.append(('store',0,0))
            state=replace(state,busy_byte_0f=0);steps.append(('store',0xf,0))
            buttons((1,0,1))
            text='Tarama Tamamlandi !' if completed_byte else 'Hazır'
        normal('status_construct');normal('status_set','TControl.SetText')
        state=replace(state,status_text=text);normal('status_cleanup')
        return out(True,'own_scan_control_projected')
    except _Missing as e:return out(False,'needs_observation',e.needed)
