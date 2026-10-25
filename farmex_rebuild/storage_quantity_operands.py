"""004653a8 quantity copy/write operand replay, never native IO."""
from dataclasses import dataclass
from source_coin import SourceCoinObservation,plan_guarded_dword

@dataclass(frozen=True)
class StorageQuantitySamples:
    global_samples:tuple=()
    guarded_samples:tuple=()
    format_span_returned:object=None
    formatted_ansi:object=None
    memset_returned:object=None
    copy_returns:tuple=()
    cleanup_returned:object=None
    source_pointer_dword:object=None
    spilled_read_samples:tuple=()
    def __post_init__(self):
        SourceCoinObservation(self.global_samples,self.guarded_samples)
        for v in (self.format_span_returned,self.memset_returned,self.cleanup_returned):
            if v is not None and type(v) is not bool:raise ValueError('Separate quantity span normal return required')
        if self.formatted_ansi is not None and type(self.formatted_ansi) is not bytes:raise ValueError('Observed quantity ANSI bytes required')
        if type(self.copy_returns) is not tuple or len(self.copy_returns)>3:raise ValueError('At most three ordered copy returns required')
        if any(v is not None and type(v) is not bool for v in self.copy_returns):raise ValueError('Quantity copy normal return required')
        if self.source_pointer_dword is not None and (type(self.source_pointer_dword) is not int or not 0<=self.source_pointer_dword<1<<32):raise ValueError('Raw saved source pointer DWORD required')
        SourceCoinObservation(self.spilled_read_samples,())
        if len(self.spilled_read_samples)>2 or any(v is not None and v>255 for at,v in self.spilled_read_samples):raise ValueError('At most two observed spill-read BYTEs required')

@dataclass(frozen=True)
class StorageQuantityPlan:
    complete:bool
    status:str
    text:str=''
    steps:tuple=()
    guarded_plans:tuple=()
    global_writes:tuple=()
    memory_writes:tuple=()
    missing:str=''
    independently_verified:bool=False
    stack_copy_bytes:bytes=b''
    source_pointer_writes:tuple=()

def plan_storage_quantity(argument,o):
    if type(argument) is not int or not 0<=argument<1<<32 or not isinstance(o,StorageQuantitySamples):
        raise ValueError('Raw quantity DWORD and typed ordered samples required')
    steps=[];guards=[];globals_write=[];writes=[];gp=0;sp=0;text='';stack_copy=b'';pointer_writes=[]
    class Missing(Exception):pass
    def result(ok,status,missing=''):
        return StorageQuantityPlan(ok,status,text,tuple(steps),tuple(guards),tuple(globals_write),tuple(writes),missing,
                                   stack_copy_bytes=stack_copy,source_pointer_writes=tuple(pointer_writes))
    def normal(value,label):
        steps.append(('normal_return',label))
        if value is not True:raise Missing(label)
    def g(address):
        nonlocal gp
        steps.append(('global',address))
        if gp>=len(o.global_samples):raise Missing('quantity global at%08x'%address)
        at,value=o.global_samples[gp];gp+=1
        if at!=address:raise ValueError('Reached quantity global order mismatch')
        if value is None:raise Missing('quantity global value at%08x'%address)
        return value
    def read(address):
        nonlocal sp
        address&=0xffffffff;steps.append(('0045dc44',address));sample=None
        if address:
            sample=o.guarded_samples[sp] if sp<len(o.guarded_samples) else None;sp+=1
        p=plan_guarded_dword(address,sample);guards.append(p)
        if not p.complete:raise Missing(p.missing)
        return p.value_dword
    def store_global(value):
        globals_write.append((0x553d20,value));steps.append(('global_write_plan',0x553d20,value))
    def write(address,data,helper):
        address&=0xffffffff;writes.append((address,data));steps.append((helper,address,len(data)))
    try:
        normal(o.format_span_returned,'quantity format/conversion span')
        if o.formatted_ansi is None:raise Missing('formatted ANSI quantity bytes')
        signed=argument-(1<<32) if argument&0x80000000 else argument
        expected=str(signed).encode('ascii')
        if o.formatted_ansi!=expected:raise ValueError('Observed ANSI quantity differs from normal signed decimal contract')
        text=expected.decode('ascii')
        stack_copy=expected[:9]
        if len(expected)>9:
            if o.source_pointer_dword is None:
                return result(False,'unresolved_stack_buffer_overwrite','initial saved source pointer missing for spill reads')
            # The first nine source bytes come from the normal formatted span.
            # Byte i8 replaces the saved pointer low byte. Subsequent reads
            # use that modified pointer; bytes i9/i10 replace its next bytes.
            scratch=bytearray(12);scratch[8:12]=o.source_pointer_dword.to_bytes(4,'little')
            scratch[:9]=stack_copy
            pointer=int.from_bytes(scratch[8:12],'little')
            pointer_writes.append((8,pointer));steps.append(('saved_source_pointer_plan',8,pointer))
            for index in range(9,len(expected)):
                address=(pointer+index)&0xffffffff
                steps.append(('spill_source_read',index,address))
                position=index-9
                if position>=len(o.spilled_read_samples):raise Missing('spill source BYTE%d at%08x'%(index,address))
                at,value=o.spilled_read_samples[position]
                if at!=address:raise ValueError('Reached spill source BYTE address mismatch')
                if value is None:raise Missing('spill source BYTE%d value at%08x'%(index,address))
                scratch[index]=value;stack_copy=bytes(scratch[:index+1])
                pointer=int.from_bytes(scratch[8:12],'little')
                pointer_writes.append((index,pointer));steps.append(('saved_source_pointer_plan',index,pointer))
        if len(expected)==9:
            # At i8 the source byte is read before the pointer's low byte is
            # overwritten. The loop then ends; memcpy uses LEA buffer, not ptr.
            steps.append(('stack_pointer_final_byte_spill',expected[8]))
        cached=g(0x553d20)
        if cached==0:
            root=read(g(0x553f48));store_global(root)
            offset=g(0x554134)
            # ADD [cache],EAX reads the field again after its previous store.
            store_global((g(0x553d20)+offset)&0xffffffff)
        write(g(0x553d20),b'\0'*14,'memset_plan')
        normal(o.memset_returned,'quantity memset normal return')
        for index,data,offset in ((0,stack_copy,0),(1,bytes((len(expected),)),0x10),(2,b'\0',0x28)):
            write(g(0x553d20)+offset,data,'memcpy_plan')
            receipt=o.copy_returns[index] if index<len(o.copy_returns) else None
            normal(receipt,'quantity memcpy%d normal return'%index)
        normal(o.cleanup_returned,'quantity ANSI cleanup normal return')
        return result(True,'writes_planned')
    except Missing as error:return result(False,'needs_observation',str(error))
