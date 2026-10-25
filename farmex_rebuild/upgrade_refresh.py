"""Captured Upgrade inventory refresh, source004f77a0. No process reads.

Every reached guarded read and normal receipt is distinct. Item naming uses
the existing supplied-pointer byte planner; Unicode uses the shared captured
00403d84 continuation. Own list sink effects are not native VCL execution.
"""
from dataclasses import dataclass,field,replace
from collections.abc import Mapping
from source_coin import GuardedDwordSample,GuardedByteSample,plan_guarded_dword,plan_guarded_byte
from item_name import ItemNameObservation,plan_item_name
from npc_unicode import NpcUnicodeFrame

BUTTON_PATH='frmMain/MainTab/SheetUpgrade/grpUpgradeItems/btnUpgradeRefresh'


@dataclass(frozen=True)
class GuardedCapture:
    sample:object=None
    returned:object=None


@dataclass(frozen=True)
class UpgradeRefreshSlot:
    offset_dword:object=None
    record:object=None
    lookup:object=None
    metadata:object=None
    base:object=None
    variant_first:object=None
    name_init_returned:object=None
    name:object=None
    name_returned:object=None
    unicode:object=None
    assignment_returned:object=None
    unicode_cleanup_returned:object=None
    ansi_cleanup_returned:object=None
    variant_fresh:object=None
    kind:object=None
    caption_returned:object=None
    concat_returned:object=None
    row_cleanup_returned:object=None


@dataclass(frozen=True)
class UpgradeRefreshObservation:
    gate_byte:object=None
    initial_text_returned:object=None
    global_root_dword:object=None
    root:object=None
    inventory_offset_dword:object=None
    inventory:object=None
    slots:object=field(default_factory=dict)
    final_cleanup_returned:object=None


@dataclass(frozen=True)
class UpgradeRefreshResult:
    complete:bool
    done:bool
    status:str
    needed:object=None
    row:object=None
    rows_added:int=0
    slot:int=14
    requests:tuple=()
    error:object=None
    native_execution_verified:bool=False
    live_compatibility_verified:bool=False


class UpgradeRefreshFrame:
    method='refresh'
    def __init__(self,sink):
        self.sink=sink;self.phase='gate';self.slot=14;self.row=None;self.rows_added=0
        self.cache={};self.reads={};self.requests=[];self.name_fields={};self.names={};self.unicode={}
        self.local_name='';self.inventory=None;self.lookup=None;self.metadata=None;self.item_id=None;self.grade=None
        self.busy=False;self.result=UpgradeRefreshResult(False,False,'queued')

    def _out(self,status,complete=False,done=False,needed=None,error=None):
        self.result=UpgradeRefreshResult(complete,done,status,needed,self.row,self.rows_added,self.slot,tuple(self.requests),error)
        return self.result

    def cancel(self,reason):
        if not self.result.done:self._out('cancelled',done=True,error=reason)
        return self.result

    def hold(self,error):
        if not self.result.done:self._out('needs_observation',needed=self.result.needed,error=str(error))
        return self.result

    def advance(self,o=None):
        if self.result.done or self.busy:return self.result
        o=UpgradeRefreshObservation() if o is None else o
        if not isinstance(o,UpgradeRefreshObservation):raise ValueError('Typed Upgrade refresh observations required')
        self.busy=True
        class Missing(Exception):pass
        def need(scope,source,name,kind='dword'):
            key=(scope,name)
            if key in self.cache:return self.cache[key]
            value=getattr(source,name)
            if value is None:raise Missing(key)
            if kind=='normal':
                if type(value) is not bool:raise ValueError('Explicit reached refresh normal receipt required')
                if value is not True:raise Missing(key)
            else:
                bits=8 if kind=='byte' else 32
                if type(value) is not int or not 0<=value<(1<<bits):raise ValueError('Raw reached refresh integer required')
            self.cache[key]=value;return value
        def normal(scope,source,name):return need(scope,source,name,'normal')
        def guarded(key,address,incoming,width=32):
            address&=0xffffffff
            state=self.reads.get(key)
            if state is None:
                state={};self.reads[key]=state;self.requests.append((key,address,width))
            if 'result' in state:return state['result']
            planner=plan_guarded_dword if width==32 else plan_guarded_byte
            sample_type=GuardedDwordSample if width==32 else GuardedByteSample
            for _ in range(3):
                p=planner(address,state.get('sample'))
                if p.complete:break
                sub='protection_return_dword' if state.get('sample') is None or state['sample'].protection_return_dword is None else ('value_dword' if width==32 else 'value_byte')
                if incoming is None:raise Missing((key,'sample',sub))
                if not isinstance(incoming,GuardedCapture) or not isinstance(incoming.sample,sample_type):raise ValueError('Typed reached refresh guarded capture required')
                if incoming.sample.address!=address:raise ValueError('Refresh guarded sample address differs')
                value=getattr(incoming.sample,sub)
                if value is None:raise Missing((key,'sample',sub))
                state['sample']=replace(state.get('sample') or sample_type(address),**{sub:value})
            else:raise ValueError('Own refresh guarded-read budget exhausted')
            if incoming is not None and not isinstance(incoming,GuardedCapture):raise ValueError('Typed refresh normal capture required')
            returned=None if incoming is None else incoming.returned
            if returned is not None and type(returned) is not bool:raise ValueError('Explicit guarded helper normal receipt required')
            if returned is not True:raise Missing((key,'returned'))
            value=p.value_dword if width==32 else p.eax_dword&255
            state['result']=value;return value
        def slot_input():
            if not isinstance(o.slots,Mapping):raise ValueError('Indexed Upgrade refresh slots required')
            value=o.slots.get(self.slot)
            if value is None:return UpgradeRefreshSlot()
            if not isinstance(value,UpgradeRefreshSlot):raise ValueError('Typed reached Upgrade slot required')
            return value
        def write(method,*args):
            try:return getattr(self.sink,method)(*args)
            except (OSError,ValueError,IndexError) as error:
                if self.result.done:return None
                self._out('list_incomplete',done=True,error=str(error));return None
        try:
            if self.row is not None:
                write('validate',self.row)
                if self.result.done:return self.result
            for _ in range(128):
                if self.result.done:return self.result
                if self.phase=='gate':
                    if need('entry',o,'gate_byte','byte')==0:return self._out('gate_closed',True,True)
                    self.phase='clear'
                elif self.phase=='clear':write('clear');self.phase='initial_text'
                elif self.phase=='initial_text':normal('entry',o,'initial_text_returned');self.phase='root'
                elif self.phase=='root':
                    at=need('entry',o,'global_root_dword')
                    guarded('root',at,o.root);self.phase='inventory'
                elif self.phase=='inventory':
                    offset=need('entry',o,'inventory_offset_dword')
                    self.inventory=guarded('inventory',self.reads['root']['result']+offset,o.inventory)
                    self.phase='final_cleanup' if self.inventory==0 else 'record'
                elif self.phase=='record':
                    if self.slot>41:self.phase='final_cleanup';continue
                    s=slot_input();offset=need(self.slot,s,'offset_dword')
                    record=guarded((self.slot,'record'),self.inventory+offset+self.slot*4,s.record)
                    self.phase='next_slot' if record==0 else 'lookup'
                elif self.phase in ('lookup','metadata','base','variant_first'):
                    s=slot_input();record=self.reads[(self.slot,'record')]['result']
                    addresses={'lookup':record+0x60,'metadata':record+0x64,'base':self.lookup,'variant_first':self.metadata}
                    value=guarded((self.slot,self.phase),addresses[self.phase],getattr(s,self.phase))
                    if self.phase=='lookup':self.lookup=value;self.phase='metadata'
                    elif self.phase=='metadata':self.metadata=value;self.phase='base'
                    elif self.phase=='base':self.phase='variant_first'
                    else:
                        self.item_id=(self.reads[(self.slot,'base')]['result']+value%1000)&0xffffffff
                        self.phase='name_init'
                elif self.phase=='name_init':normal(self.slot,slot_input(),'name_init_returned');self.phase='name'
                elif self.phase=='name':
                    s=slot_input()
                    if self.slot not in self.names:
                        data=ItemNameObservation() if s.name is None else s.name
                        if not isinstance(data,ItemNameObservation):raise ValueError('Typed reached item-name inputs required')
                        cached=self.name_fields.setdefault(self.slot,{})
                        def reader(name,count=None):
                            if name in cached:return cached[name]
                            value=getattr(data,name)
                            if value is not None:
                                if name=='captured' and len(value)<count:return value
                                if name=='captured':value=value[:count]
                                cached[name]=value
                            return value
                        plan=plan_item_name(self.item_id,data,provided_lookup=self.lookup,provided_metadata=self.metadata,_observation_reader=reader)
                        if plan.ansi_bytes is None:raise Missing((self.slot,'name',plan.status,plan.reason))
                        self.names[self.slot]=plan
                    normal(self.slot,s,'name_returned');self.phase='unicode'
                elif self.phase=='unicode':
                    s=slot_input()
                    if self.slot not in self.unicode:self.unicode[self.slot]=NpcUnicodeFrame(self.names[self.slot].ansi_bytes)
                    p=self.unicode[self.slot].advance(s.unicode)
                    if not p.complete:raise Missing((self.slot,'unicode',p.needed))
                    self.phase='assignment'
                elif self.phase=='assignment':
                    normal(self.slot,slot_input(),'assignment_returned')
                    self.local_name=self.unicode[self.slot].final.capture.value;self.phase='unicode_cleanup'
                elif self.phase=='unicode_cleanup':normal(self.slot,slot_input(),'unicode_cleanup_returned');self.phase='ansi_cleanup'
                elif self.phase=='ansi_cleanup':normal(self.slot,slot_input(),'ansi_cleanup_returned');self.phase='variant_fresh'
                elif self.phase=='variant_fresh':
                    self.grade=guarded((self.slot,'variant_fresh'),self.metadata,slot_input().variant_fresh)%10;self.phase='kind'
                elif self.phase=='kind':
                    kind=guarded((self.slot,'kind'),self.metadata+0x44,slot_input().kind,8)
                    self.phase='add' if kind==5 else 'next_slot'
                elif self.phase=='add':
                    self.row=write('add_row')
                    if not self.result.done:self.rows_added+=1;self.phase='caption'
                elif self.phase=='caption':
                    normal(self.slot,slot_input(),'caption_returned')
                    write('set_caption',self.row,str(self.slot-14));self.phase='concat'
                elif self.phase=='concat':
                    normal(self.slot,slot_input(),'concat_returned')
                    write('add_subitem',self.row,self.local_name+' (+'+str(self.grade)+')');self.phase='row_cleanup'
                elif self.phase=='row_cleanup':normal(self.slot,slot_input(),'row_cleanup_returned');self.phase='next_slot'
                elif self.phase=='next_slot':self.row=None;self.slot+=1;self.phase='record'
                elif self.phase=='final_cleanup':
                    normal('entry',o,'final_cleanup_returned')
                    return self._out('refreshed',True,True)
                else:raise ValueError('Unknown Upgrade refresh phase')
            return self._out('continuation',needed=('own_chunk',))
        except Missing as error:return self._out('needs_observation',needed=error.args[0])
        finally:self.busy=False
