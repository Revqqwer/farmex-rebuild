"""Selected Take/Give continuation; captured helpers and an inert owned queue."""
from dataclasses import dataclass,field
from collections.abc import Mapping
import math,struct
from quest_collection import QuestCollection,dword
from quest_record import QuestRecord
from quest_row import QuestRow
from rtl_integer32 import parse_rtl_integer32
from action_queue import QueueState,enqueue
from quest_lookup import QuestLookupFrame,QuestLookupObservation


@dataclass(frozen=True)
class QuestActionObservation:
    values:object=field(default_factory=dict)
    normal_returns:object=field(default_factory=dict)
    enqueue_gates:object=field(default_factory=dict)
    enqueue_ticks:object=field(default_factory=dict)
    enqueue_prefix_returns:object=field(default_factory=dict)
    lookup:object=None


@dataclass(frozen=True)
class QuestActionPlan:
    complete:bool
    status:str
    method:str
    record_index:object=None
    needed:object=None
    queue:object=None
    calls:tuple=()
    reads:tuple=()
    queue_calls:tuple=()
    native_execution_verified:bool=False
    delivery_verified:bool=False
    live_compatibility_verified:bool=False
    lookup_plan:object=None


class QuestActionFrame:
    def __init__(self,method,collection,main_rows,selected_index,*,use_owned_scalar_model=False,
                 use_owned_cstring_model=False,use_owned_float_model=False):
        if method not in ('take','give'):raise ValueError('Selected take or give required')
        if not isinstance(collection,QuestCollection) or type(main_rows) is not tuple or any(not isinstance(r,QuestRow) for r in main_rows):raise ValueError('Typed collection and immutable visible rows required')
        if type(selected_index) is not int or not -0x80000000<=selected_index<=0x7fffffff:raise ValueError('Signed selected row required')
        if any(type(v) is not bool for v in (use_owned_scalar_model,use_owned_cstring_model,use_owned_float_model)):raise ValueError('Explicit own model switches required')
        self.method=method;self.collection=collection;self.main_rows=main_rows;self.selected=selected_index
        self.owned_scalar=use_owned_scalar_model;self.owned_string=use_owned_cstring_model;self.owned_float=use_owned_float_model
        self.phase='selection';self.cache={};self.normal=set();self.called=set();self.calls=[];self.reads=[]
        self.queue=QueueState();self.queue_calls=[];self.queue_applied=set();self.buffer=b'';self.payloads={}
        self.exit_reason='locally_prepared';self.final=None
        self.lookup_mode=None;self.lookup_frame=None;self.lookup_result=None

    def out(self,status,needed=None,complete=False):
        p=QuestActionPlan(complete,status,self.method,self.cache.get('record_index'),needed,self.queue,
                          tuple(self.calls),tuple(self.reads),tuple(self.queue_calls),lookup_plan=self.lookup_result)
        if complete:self.final=p
        return p

    def advance(self,observation=None):
        if self.final is not None:return self.final
        o=QuestActionObservation() if observation is None else observation
        if not isinstance(o,QuestActionObservation) or any(not isinstance(v,Mapping) for v in (o.values,o.normal_returns,o.enqueue_gates,o.enqueue_ticks,o.enqueue_prefix_returns)):
            raise ValueError('Typed sparse Quest action observations required')
        class Missing(Exception):pass
        def request(label,helper,args=()):
            if label not in self.called:self.calls.append((helper,label,args));self.called.add(label)
        def normal(label,helper,args=()):
            request(label,helper,args)
            if label in self.normal:return
            receipt=o.normal_returns.get(label)
            if receipt is not None and type(receipt) is not bool:raise ValueError('Normalized normal-return receipt required')
            if receipt is not True:raise Missing(('normal',label))
            self.normal.add(label)
        def value(label):
            if label not in self.cache:
                if label not in o.values:raise Missing(('value',label))
                self.cache[label]=dword(o.values[label])
            return self.cache[label]
        def record_field(label,attribute,offset):
            if label not in self.cache:
                index=self.cache['record_index']
                if type(self.collection.records) is not tuple or index>=len(self.collection.records):raise Missing(('owned_record',index))
                r=self.collection.records[index]
                if not isinstance(r,QuestRecord):raise ValueError('Typed Quest record required')
                self.cache[label]=getattr(r,attribute);self.reads.append((index,offset,label,self.cache[label]))
            return self.cache[label]
        def cstring(role,raw):
            if type(raw) is not bytes:raise ValueError('Immutable record ANSI bytes required')
            key=role+'_cpp_bytes'
            if key not in self.cache:
                result=o.values.get(key)
                if result is None:
                    if not self.owned_string:raise Missing(('value',key))
                    result=raw.split(b'\0',1)[0]
                if type(result) is not bytes:raise ValueError('Immutable captured C++ string bytes required')
                self.cache[key]=result
            return self.cache[key]
        def returned_value(label,helper,args=()):
            normal(label,helper,args);return value(label)
        def branch(label,owned_result):
            if label not in self.cache:
                result=owned_result if self.owned_float else o.values.get(label)
                if result is None:raise Missing(('value',label))
                if type(result) is not bool:raise ValueError('Normalized captured FPU branch result required')
                self.cache[label]=result
            return self.cache[label]
        def queue_call(index,payload,delay):
            label=('enqueue',index);request(label,'004c7710',(payload,len(payload),delay))
            if index not in self.queue_applied:
                gate_key=('enqueue_gate',index)
                if gate_key not in self.cache:
                    if index not in o.enqueue_gates:raise Missing(('enqueue_gate',index))
                    self.cache[gate_key]=dword(o.enqueue_gates[index])
                gate=self.cache[gate_key]
                tick=None
                if gate:
                    tick_key=('enqueue_tick',index)
                    if tick_key not in self.cache:
                        if index not in o.enqueue_ticks:raise Missing(('enqueue_tick',index))
                        self.cache[tick_key]=dword(o.enqueue_ticks[index])
                    tick=self.cache[tick_key]
                    prefix=o.enqueue_prefix_returns.get(index)
                    if prefix is not None and type(prefix) is not bool:raise ValueError('Explicit enqueue append-span receipt required')
                    if prefix is not True:raise Missing(('enqueue_append_span',index))
                p=enqueue(self.queue,payload,len(payload),delay,gate,tick)
                if p.state is None:raise Missing(('enqueue',index,p.missing or p.status))
                self.queue=p.state;self.queue_applied.add(index);self.queue_calls.append((index,payload,delay,gate,tick,p.status))
            # Known queue prefix precedes the outer helper's normal return.
            normal(label,'004c7710',(payload,len(payload),delay))
        def write_buffer(label,data,helper):
            request(label,helper,(data,))
            if len(self.buffer)+len(data)>512:return False
            normal(label,helper,(data,));self.buffer+=data;return True
        def finish(reason):self.exit_reason=reason;self.phase='epilogue'
        try:
            while True:
                if self.phase=='selection':
                    normal('selection','QuestList.GetItemIndex')
                    if self.selected<0:finish('no_selection')
                    else:self.phase='caption'
                elif self.phase=='caption':
                    normal('caption','0045f7f4',(self.selected,))
                    if self.selected>=len(self.main_rows):return self.out('unresolved_visible_row',('visible_row',self.selected))
                    self.cache['caption']=self.main_rows[self.selected].caption;self.phase='caption_parse'
                elif self.phase=='caption_parse':
                    normal('caption_parse','0050638e')
                    if 'record_index' not in self.cache:
                        raw=o.values.get('record_index')
                        if raw is None:
                            if not self.owned_scalar:raise Missing(('value','record_index'))
                            parsed=parse_rtl_integer32(self.cache['caption'])
                            if not parsed.accepted:return self.out('needs_native_StrToInt_exception_path',('caption',parsed.code))
                            raw=parsed.dword
                        self.cache['record_index']=dword(raw)
                    self.phase='caption_cleanup'
                elif self.phase=='caption_cleanup':normal('caption_cleanup','00505c64');self.phase='npc_cpp'
                elif self.phase=='npc_cpp':
                    raw=record_field('npc_input','npc_bytes',0x18)
                    normal('npc_cpp','00403808/0040382c/00403860/004038e4 span')
                    cstring('npc',raw);self.phase='npc_lookup'
                elif self.phase=='npc_lookup':
                    npc=returned_value('npc_id','00465960',(self.cache['npc_cpp_bytes'],))
                    if npc==0:finish('npc_not_found')
                    else:self.phase='npc_pointer'
                elif self.phase=='npc_pointer':
                    pointer=returned_value('npc_pointer','00464a10',(self.cache['npc_id'],))
                    if pointer==0:finish('npc_pointer_missing')
                    else:self.phase='coord_a'
                elif self.phase in ('coord_a','coord_b'):
                    role=self.phase;offset=value(role+'_offset')
                    if (role,'logged') not in self.cache:
                        self.reads.append((None,0x554008 if role=='coord_a' else 0x554010,role+'_offset',offset));self.cache[(role,'logged')]=True
                    normal(role,'0045ddb8/FSTP32',((self.cache['npc_pointer']+offset)&0xffffffff,))
                    value(role+'_bits');self.phase='coord_b' if role=='coord_a' else 'distance'
                elif self.phase=='distance':
                    returned_value('distance_bits','00460548/FSTP32',(self.cache['coord_a_bits'],self.cache['coord_b_bits']))
                    self.phase='distance_lower'
                elif self.phase=='distance_lower':
                    distance=struct.unpack('<f',struct.pack('<I',self.cache['distance_bits']))[0]
                    if branch('distance_lower_reject',math.isnan(distance) or distance<0):finish('out_of_range')
                    else:self.phase='distance_upper'
                elif self.phase=='distance_upper':
                    distance=struct.unpack('<f',struct.pack('<I',self.cache['distance_bits']))[0]
                    if branch('distance_upper_reject',math.isnan(distance) or distance>10):finish('out_of_range')
                    else:self.phase='target'
                elif self.phase=='target':
                    target=returned_value('current_target','00462630')
                    self.phase='prepare' if target==self.cache['npc_id'] else 'retarget'
                elif self.phase=='retarget':normal('retarget','0046493c',(self.cache['npc_pointer'],));self.phase='prepare'
                elif self.phase=='prepare':normal('prepare','0046fb38',(0x5690e0,self.cache['npc_id']));self.phase='data20'
                elif self.phase=='data20':
                    pointer=dword(record_field('data_pointer20','data_pointer_dword',4))
                    returned_value('data20','0045dc44',((pointer+0x20)&0xffffffff,));self.phase='status'
                elif self.phase=='status':
                    normal('status','004d5244',('owned_quest_context',self.cache['data20']))
                    if self.method=='give' and value('status_eax')&255!=3:finish('give_status_not3')
                    else:self.phase='data1c'
                elif self.phase=='data1c':
                    pointer=dword(record_field('data_pointer1c','data_pointer_dword',4))
                    normal('data1c_unused','0045dc44',((pointer+0x1c)&0xffffffff,));self.phase='lookup'
                elif self.phase=='lookup':
                    upper=dword(record_field('lookup_upper','source_index',0))
                    lower=(dword(record_field('lookup_lower_source','source_index',0))-4)&0xffffffff
                    display=record_field('lookup_display','display_bytes',0x14)
                    if type(display) is not bytes:raise ValueError('Immutable lookup display ANSI bytes required')
                    args=('owned_quest_context',display,4 if self.method=='take' else 3,lower,upper)
                    request('lookup_eax','004d642c',args)
                    if self.lookup_mode is None:
                        if o.lookup is not None:
                            if not isinstance(o.lookup,QuestLookupObservation):raise ValueError('Typed nested lookup observations required')
                            self.lookup_frame=QuestLookupFrame(display,args[2],lower,upper);self.lookup_mode='composed'
                        elif 'lookup_eax' in o.values:self.lookup_mode='captured'
                        else:raise Missing(('lookup_input',))
                    if self.lookup_mode=='composed':
                        self.lookup_result=self.lookup_frame.advance(o.lookup)
                        if not self.lookup_result.complete:
                            child=self.lookup_frame
                            raise Missing(('lookup',child.phase,child.index,child.iteration,self.lookup_result.needed))
                        # Inner completion cannot fabricate the caller boundary.
                        normal('lookup_eax','004d642c',args)
                        self.cache['lookup_eax']=self.lookup_result.eax
                    else:returned_value('lookup_eax','004d642c',args)
                    self.payloads[0]=b'\x64\x07'+(self.cache['lookup_eax']&0xffff).to_bytes(2,'little')+b'\0\0';self.phase='first_copy'
                elif self.phase=='first_copy':normal('first_copy','00507946',(2,));self.phase='queue0'
                elif self.phase=='queue0':
                    queue_call(0,self.payloads[0],500 if self.method=='take' else 1000);self.phase='script_cpp'
                elif self.phase=='script_cpp':
                    raw=record_field('script_input','script_bytes',8)
                    normal('script_cpp','00403808/0040382c/00403860/004038e4 span')
                    cstring('script',raw);self.phase='opcode'
                elif self.phase in ('opcode','zero','length','script_copy','terminal'):
                    phase=self.phase
                    if phase=='opcode':data=b'\x55';next_phase='zero'
                    elif phase=='zero':data=b'\0';next_phase='length'
                    elif phase=='length':data=bytes((len(self.cache['script_cpp_bytes'])&255,));next_phase='script_copy'
                    elif phase=='script_copy':
                        data=self.cache['script_cpp_bytes'];next_phase='queue1' if self.method=='take' else 'terminal'
                    else:data=b'\xff' if self.method=='take' else b'\x02';next_phase='queue2' if self.method=='take' else 'queue1'
                    if not write_buffer(phase,data,'004d4f1c' if phase=='script_copy' else '004d4e73'):
                        return self.out('unresolved_source_stack_overflow',('buffer',phase,len(self.buffer)+len(data)))
                    self.phase=next_phase
                elif self.phase=='queue1':
                    queue_call(1,self.buffer,1000 if self.method=='take' else 2000)
                    self.phase='terminal' if self.method=='take' else 'script_cleanup'
                elif self.phase=='queue2':queue_call(2,self.buffer,1500);self.phase='script_cleanup'
                elif self.phase=='script_cleanup':normal('script_cleanup','00403860',(0,1));self.phase='epilogue'
                elif self.phase=='epilogue':
                    normal('epilogue','004d5a8c normal return' if self.method=='take' else '004d6040 normal return')
                    return self.out(self.exit_reason,complete=True)
                else:raise ValueError('Unknown selected Quest action phase')
        except Missing as error:return self.out('needs_observation',error.args[0])
