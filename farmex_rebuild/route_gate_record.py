"""Captured four-branch gate recording from004e3144; no game/network IO.

Parser, lookup, name and formatter normal spans remain explicit observations.
The sink is an owned route list, not native VCL. Other dispatcher branches and
the parent callback return are outside this data continuation's certificate.
"""
from dataclasses import dataclass
from route_npc_click import NpcValueCapture


@dataclass(frozen=True)
class GateRecordObservation:
    recording_byte:object=None
    zone_first:object=None
    zone_second:object=None
    clock:object=None
    reader_returned:object=None
    actor:object=None
    name_setup_returned:object=None
    name_storage:object=None
    name_ansi:object=None
    comparison_returned:object=None
    format_returned:object=None


@dataclass(frozen=True)
class GateRecordResult:
    complete:bool
    done:bool
    status:str
    needed:object=None
    row:object=None
    writes:tuple=()
    name_read_count:object=None
    error:object=None
    native_execution_verified:bool=False
    live_compatibility_verified:bool=False


class GateRecordFrame:
    def __init__(self,packet,sink):
        if type(packet) is not bytes:raise ValueError('Immutable captured packet bytes required')
        self.packet=packet;self.sink=sink;self.cache={};self.writes=[]
        self.row=None;self.phase='opcode';self.opcode=None;self.parameter=None
        self.caption=None;self.first=None;self.name_read_count=None;self.busy=False
        self.result=GateRecordResult(False,False,'queued')

    def _out(self,status,complete=False,done=False,needed=None,error=None):
        self.result=GateRecordResult(complete,done,status,needed,self.row,tuple(self.writes),self.name_read_count,error)
        return self.result

    def cancel(self,reason):
        if not self.result.done:self._out('cancelled',done=True,error=reason)
        return self.result

    def hold(self,error):
        if not self.result.done:self._out('needs_observation',needed=self.result.needed,error=str(error))
        return self.result

    def advance(self,o=None):
        if self.result.done or self.busy:return self.result
        o=GateRecordObservation() if o is None else o
        if not isinstance(o,GateRecordObservation):raise ValueError('Typed gate-record observations required')
        self.busy=True
        class Missing(Exception):pass
        def raw(value,bits):
            if type(value) is not int or not 0<=value<(1<<bits):raise ValueError('Raw gate-record integer required')
            return value
        def scalar(field,bits):
            if field not in self.cache:
                value=getattr(o,field)
                if value is None:raise Missing(field)
                self.cache[field]=raw(value,bits)
            return self.cache[field]
        def normal(field):
            if self.cache.get(field) is True:return
            value=getattr(o,field)
            if value is not None and type(value) is not bool:raise ValueError('Explicit gate-record normal receipt required')
            if value is not True:raise Missing(field)
            self.cache[field]=True
        def captured(field,kind):
            state=self.cache.setdefault(field,{})
            value=getattr(o,field)
            if value is not None and not isinstance(value,NpcValueCapture):raise ValueError('Typed gate helper capture required')
            if 'value' not in state:
                data=None if value is None else value.value
                if data is None:raise Missing(field+'.value')
                if kind=='dword':raw(data,32)
                elif type(data) is not kind:raise ValueError('Gate helper capture type differs')
                state['value']=data
            if state.get('returned') is not True:
                returned=None if value is None else value.returned
                if returned is not None and type(returned) is not bool:raise ValueError('Explicit helper normal receipt required')
                if returned is not True:raise Missing(field+'.returned')
                state['returned']=True
            return state['value']
        def read(at,count):
            if len(self.packet)<at+count:raise Missing('packet_bytes[%d:%d]'%(at,at+count))
            return int.from_bytes(self.packet[at:at+count],'little')
        try:
            if self.row is not None:
                validate=getattr(self.sink,'validate',None)
                if callable(validate):validate(self.row)
            for _ in range(24):
                if self.phase=='opcode':
                    self.opcode=read(0,1)
                    if self.opcode not in (0x20,0x33,0x4b,0x55):
                        return self._out('outside_record_scope',done=True)
                    if self.opcode==0x20 and read(1,1)!=1:return self._out('subtype_ignored',True,True)
                    self.phase='clock' if self.opcode==0x4b else 'recording'
                elif self.phase=='clock':
                    tick=captured('clock','dword')
                    self.writes.extend(((0x561f74,32,tick),(0x561f78,32,0)))
                    self.phase='recording'
                elif self.phase=='recording':
                    if not scalar('recording_byte',8):return self._out('recording_disabled',True,True)
                    self.phase='zone_first' if self.opcode in (0x20,0x55) else 'parse'
                elif self.phase=='zone_first':
                    self.phase='parse' if captured('zone_first','dword')==32 else 'zone_second'
                elif self.phase=='zone_second':
                    if captured('zone_second','dword')!=33:return self._out('zone_rejected',True,True)
                    self.phase='parse'
                elif self.phase=='parse':
                    normal('reader_returned')
                    self.parameter=read(2,2) if self.opcode==0x20 else read(1,1 if self.opcode==0x55 else 4)
                    if self.opcode==0x20:
                        if self.parameter==0:return self._out('zero_npc_id',True,True)
                        self.phase='actor'
                    else:
                        self.caption={0x33:'Gate Open',0x4b:'Gate',0x55:'Delos Gate'}[self.opcode]
                        self.phase='add'
                elif self.phase=='actor':
                    if captured('actor','dword')==0:return self._out('lookup_empty',True,True)
                    self.phase='name_setup'
                elif self.phase=='name_setup':normal('name_setup_returned');self.phase='name_storage'
                elif self.phase=='name_storage':
                    storage=captured('name_storage','dword')
                    signed=storage if storage<0x80000000 else storage-(1<<32)
                    self.name_read_count=storage if signed>=16 else 50
                    self.phase='name'
                elif self.phase=='name':
                    captured('name_ansi',bytes)
                    if self.cache['name_storage']['value']!=15:return self._out('storage_rejected',True,True)
                    self.phase='name_compare'
                elif self.phase=='name_compare':
                    normal('comparison_returned')
                    if self.cache['name_ansi']['value']!=b'[Teleport Gate]':return self._out('name_rejected',True,True)
                    self.caption='Delos Gate Open';self.first='-';self.phase='add'
                elif self.phase=='add':self.row=self.sink.add_row();self.phase='caption'
                elif self.phase=='caption':
                    self.sink.set_caption(self.row,self.caption)
                    self.phase='sub1' if self.opcode==0x20 else 'format'
                elif self.phase=='format':
                    normal('format_returned');self.first=str(self.parameter);self.phase='sub1'
                elif self.phase=='sub1':self.sink.add_subitem(self.row,self.first);self.phase='sub2'
                elif self.phase=='sub2':
                    self.sink.add_subitem(self.row,'-');return self._out('row_completed',True,True)
                else:raise ValueError('Unknown own gate-record phase')
            raise ValueError('Own gate-record phase budget exhausted')
        except Missing as error:return self._out('needs_observation',needed=str(error))
        except (OSError,ValueError,IndexError) as error:return self._out('incomplete',done=True,error=str(error))
        finally:self.busy=False
