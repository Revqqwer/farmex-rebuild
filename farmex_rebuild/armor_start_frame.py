"""Incremental Armor callback -> shared runner; no game/native/modal calls."""
from dataclasses import dataclass,field
from collections.abc import Mapping
from armor_start import ArmorStartObservation,armor_item_id
from npc_lookup import select_npc
from operation_engine import UpgradeRunner

BUTTON_PATH='frmMain/MainTab/SheetUpgrade/GroupBox23/btnUpgradeArmorAl'


@dataclass(frozen=True)
class ArmorStartFrameObservation:
    gate_byte:object=None
    source:object=None
    combo_returns:object=field(default_factory=dict)
    item_mapping_returned:object=None
    message_cleanup_returns:object=field(default_factory=dict)


@dataclass(frozen=True)
class ArmorStartFrameResult:
    complete:bool
    done:bool
    status:str
    needed:object=None
    error:object=None
    native_execution_verified:bool=False
    live_compatibility_verified:bool=False


class ArmorStartFrame:
    method='armor'
    def __init__(self,runner,combo_reader):
        if not isinstance(runner,UpgradeRunner) or not runner.source_clock or runner.source_pending is not None:
            raise ValueError('Idle shared source-clock runner required')
        if not callable(combo_reader):raise ValueError('Own fresh combo reader required')
        self.runner=runner;self.combo_reader=combo_reader;self.phase='gate';self.cache={}
        self.busy=False;self.message=None;self.result=ArmorStartFrameResult(False,False,'queued')
    def _out(self,status,complete=False,done=False,needed=None,error=None):
        self.result=ArmorStartFrameResult(complete,done,status,needed,error);return self.result
    def cancel(self,reason):
        if not self.result.done:self._out('cancelled',done=True,error=reason)
        return self.result
    def hold(self,error):
        if not self.result.done:self._out('needs_observation',needed=self.result.needed,error=str(error))
        return self.result
    def _write(self,offset,value):
        r=self.runner;fields=dict(getattr(r,'armor_source_fields',{}))
        fields.update({0x10:r.state,0x60:r.armor_attempts});fields[offset]=value
        r.armor_source_fields=fields
        if offset==0x10:r.state=value
        elif offset==0x60:r.armor_attempts=value
    def advance(self,o=None):
        if self.result.done or self.busy:return self.result
        o=ArmorStartFrameObservation() if o is None else o
        if not isinstance(o,ArmorStartFrameObservation):raise ValueError('Typed Armor callback observation required')
        source=o.source if o.source is not None else ArmorStartObservation()
        if not isinstance(source,ArmorStartObservation):raise ValueError('Typed Armor helper observation required')
        self.busy=True
        class Missing(Exception):pass
        def need(name):
            if name not in self.cache:
                value=getattr(source,name)
                if value is None:raise Missing((name,))
                self.cache[name]=value
            return self.cache[name]
        def normal(value,label):
            if label in self.cache:return
            if value is not None and type(value) is not bool:raise ValueError('Explicit normal return required')
            if value is not True:raise Missing(label)
            self.cache[label]=True
        def combo(which):
            if which not in self.cache:
                value=self.combo_reader()
                if type(value) is not int or not -0x80000000<=value<0x80000000:raise ValueError('Own signed ItemIndex required')
                self.cache[which]=value&0xffffffff
            if not isinstance(o.combo_returns,Mapping):raise ValueError('Indexed combo normal returns required')
            normal(o.combo_returns.get(which),('combo_return',which))
            return self.cache[which]
        def message(reason):self.message=reason;self.phase='message'
        try:
            for _ in range(48):
                self._out('advancing',needed=(self.phase,))
                if self.phase=='gate':
                    gate=o.gate_byte
                    if gate is None:raise Missing(('gate_byte',))
                    if type(gate) is not int or not 0<=gate<=255:raise ValueError('Raw561f55 BYTE required')
                    if gate==0:return self._out('gate_closed',True,True)
                    self.phase='filter'
                elif self.phase=='filter':normal(source.filter_ready_returned,('filter_construct',));self.phase='npc'
                elif self.phase=='npc':
                    npc=source.npc_id_dword
                    if source.lookup_candidates is not None:
                        if npc is not None:raise ValueError('Raw NPC and selector observations conflict')
                        lookup=select_npc(source.lookup_candidates,b'Armor Merchant',traversal_complete=source.traversal_complete)
                        if lookup.status!='complete':raise Missing(('npc_selector',lookup.missing))
                        npc=lookup.candidate_id
                    if npc is None:raise Missing(('npc_id_dword',))
                    self._write(0x4c,npc)
                    if npc==0:message('npc_missing')
                    else:self.phase='pointer'
                elif self.phase=='pointer':
                    pointer=need('npc_pointer_dword');self._write(0x48,pointer)
                    if pointer==0:return self._out('npc_pointer_zero',True,True)
                    self.phase='x'
                elif self.phase=='x':need('x_offset_dword');self._write(0x50,need('x_ftol_dword'));self.phase='y'
                elif self.phase=='y':need('y_offset_dword');self._write(0x54,need('y_ftol_dword'));self.phase='distance'
                elif self.phase=='distance':
                    distance=need('distance_ftol_dword');distance=distance if distance<0x80000000 else distance-0x100000000
                    if distance>=10:message('too_far')
                    else:self.phase='first_combo'
                elif self.phase=='first_combo':combo('first');self.phase='mapping'
                elif self.phase=='mapping':
                    normal(o.item_mapping_returned,('item_mapping_returned',))
                    item=armor_item_id(self.cache['first']);self._write(0x58,item)
                    if item==0:message('item_missing')
                    else:self.phase='second_combo'
                elif self.phase=='second_combo':self._write(0x5c,combo('second'));self.phase='bag'
                elif self.phase=='bag':
                    if need('bag_flag_byte')!=0:message('bag_full')
                    else:self.phase='arm'
                elif self.phase=='arm':
                    self._write(0x60,0);self._write(0x10,2)
                    self.runner.reason=''
                    return self._out('armor_armed',True,True)
                elif self.phase=='message':
                    normal(source.message_returns.get(self.message),('message',self.message));self.phase='message_cleanup0'
                elif self.phase in ('message_cleanup0','message_cleanup1'):
                    index=0 if self.phase=='message_cleanup0' else 1
                    if not isinstance(o.message_cleanup_returns,Mapping):raise ValueError('Separate message cleanup returns required')
                    normal(o.message_cleanup_returns.get((self.message,index)),('message_cleanup',self.message,index))
                    if index==1:return self._out(self.message,True,True)
                    self.phase='message_cleanup1'
                else:raise ValueError('Unknown Armor start phase')
            return self._out('continuation',needed=('own_chunk',))
        except Missing as error:return self._out('needs_observation',needed=error.args[0])
        finally:self.busy=False
