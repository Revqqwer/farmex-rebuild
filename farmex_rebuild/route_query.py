"""0046cfcc ordered0..3000 query caller, observed fields/float flags/helpers."""
from dataclasses import dataclass,field
from source_coin import GuardedDwordSample,GuardedByteSample,plan_guarded_dword,plan_guarded_byte
from game_text import TextReadRequest,replay_text_copy
from source_name_filter import NameFilterPlan
from source_unicode import utf16_key

def _raw(v,bits=32):
    if v is not None and (type(v) is not int or not 0<=v<1<<bits):raise ValueError('Raw route-query integer required')

@dataclass(frozen=True)
class QueryNameCapture:
    readable:object=None
    copied_bytes:object=None
    codec:object=None
    def __post_init__(self):
        if self.readable is not None and type(self.readable) is not bool:raise ValueError('Explicit name readable observation required')
        if self.copied_bytes is not None and type(self.copied_bytes) is not bytes:raise ValueError('Exact captured name bytes required')
        if self.codec is not None and type(self.codec) is not str:raise ValueError('Explicit own conversion codec required')

@dataclass(frozen=True)
class RouteQueryCandidate:
    index:int
    pointer_dword:object=None
    global_samples:tuple=()
    dword_samples:tuple=()
    byte_samples:tuple=()
    x_read_returned:object=None
    y_read_returned:object=None
    x_float_bits:object=None
    y_float_bits:object=None
    metric_ftol_dword:object=None
    context39_byte:object=None
    name_span_returned:object=None
    name_text:object=None
    name_capture:object=None
    reference_4626b0_dword:object=None
    reference_462690_samples:tuple=()
    context8_byte:object=None
    selected_radius_ah:object=None
    anti_radius_ah:object=None
    primary_name_al:object=None
    secondary_name_al:object=None
    primary_name_execution:object=None
    secondary_name_execution:object=None
    primary_name_returned:object=None
    secondary_name_returned:object=None
    def __post_init__(self):
        if type(self.index) is not int or not 0<=self.index<=3000:raise ValueError('Source query index0..3000 required')
        if any(type(v) is not tuple for v in (self.global_samples,self.dword_samples,self.byte_samples,self.reference_462690_samples)):
            raise ValueError('Ordered immutable query samples required')
        for row in self.global_samples:
            if type(row) is not tuple or len(row)!=2 or row[0] is None:raise ValueError('Global address/value required')
            _raw(row[0]);_raw(row[1])
        if any(not isinstance(v,GuardedDwordSample) for v in self.dword_samples):raise ValueError('Typed guarded DWORD samples required')
        if any(not isinstance(v,GuardedByteSample) for v in self.byte_samples):raise ValueError('Typed guarded BYTE samples required')
        for v in self.reference_462690_samples:_raw(v)
        for name in ('pointer_dword','x_float_bits','y_float_bits','metric_ftol_dword','reference_4626b0_dword'):_raw(getattr(self,name))
        for name in ('context39_byte','context8_byte','selected_radius_ah','anti_radius_ah','primary_name_al','secondary_name_al'):_raw(getattr(self,name),8)
        for v in (self.x_read_returned,self.y_read_returned,self.name_span_returned):
            if v is not None and type(v) is not bool:raise ValueError('Separate query helper normal return required')
        if self.name_text is not None and type(self.name_text) is not str:raise ValueError('Captured Unicode name required')
        if self.name_capture is not None and not isinstance(self.name_capture,QueryNameCapture):raise ValueError('Typed captured-name input required')
        for v in (self.primary_name_execution,self.secondary_name_execution):
            if v is not None and not isinstance(v,NameFilterPlan):raise ValueError('Typed name filter plan required')
        for v in (self.primary_name_returned,self.secondary_name_returned):
            if v is not None and type(v) is not bool:raise ValueError('Explicit bound filter return required')

@dataclass(frozen=True)
class RouteQueryObservation:
    reference_462650_dword:object=None
    string_init_returned:object=None
    candidates:tuple=()
    final_cleanup_returned:object=None
    def __post_init__(self):
        _raw(self.reference_462650_dword)
        if type(self.candidates) is not tuple or any(not isinstance(v,RouteQueryCandidate) for v in self.candidates):raise ValueError('Ordered typed candidate prefix required')
        for v in (self.string_init_returned,self.final_cleanup_returned):
            if v is not None and type(v) is not bool:raise ValueError('Explicit string lifetime normal returns required')

@dataclass(frozen=True)
class RouteQueryPlan:
    complete:bool
    status:str
    anti_radius_dword:object=None
    enemy_radius_dword:object=None
    output_bytes:tuple=(0,0,0)
    visited:int=0
    steps:tuple=()
    writes:tuple=()
    guarded_plans:tuple=()
    name_plans:tuple=()
    missing:str=''
    native_execution_verified:bool=False
    def __post_init__(self):
        if type(self.output_bytes) is not tuple or len(self.output_bytes)!=3 or any(type(v) is not int or v not in (0,1) for v in self.output_bytes):
            raise ValueError('Three monotonic source query BYTE0/1 outputs required')

def plan_route_query(anti_radius,enemy_radius,o):
    _raw(anti_radius);_raw(enemy_radius)
    if not isinstance(o,RouteQueryObservation):raise ValueError('Typed route-query observations required')
    outputs=[0,0,0];steps=[('initialize_output_bytes',0,0,0)];writes=[];guards=[];names=[];visited=0
    class Missing(Exception):pass
    def need(v,label):
        if v is None:raise Missing(label)
        return v
    def normal(v,label):
        steps.append(('normal_return',label))
        if v is not True:raise Missing(label)
    def result(complete,status,missing=''):
        return RouteQueryPlan(complete,status,anti_radius,enemy_radius,tuple(outputs),visited,
            tuple(steps),tuple(writes),tuple(guards),tuple(names),missing)
    def set_output(slot,index):
        outputs[slot]=1;writes.append((index,slot,1))
    try:
        steps.append(('00462650',));cached=need(o.reference_462650_dword,'cached00462650 EAX DWORD')
        normal(o.string_init_returned,'00404a78 string initialization')
        for index in range(3001):
            if index>=len(o.candidates):raise Missing('candidate lookup index%d'%index)
            row=o.candidates[index]
            if row.index!=index:raise ValueError('Query candidate index/order mismatch')
            steps.append(('00464a10',index));pointer=need(row.pointer_dword,'candidate pointer%d'%index);visited+=1
            if pointer==0:continue
            gp=0;dp=0;bp=0
            def g(address):
                nonlocal gp
                steps.append(('global_read',index,address))
                if gp>=len(row.global_samples):raise Missing('candidate%d global sample%d at%08x'%(index,gp,address))
                at,value=row.global_samples[gp];gp+=1
                if at!=address:raise ValueError('Query candidate global read order mismatch')
                return need(value,'candidate%d global value at%08x'%(index,address))
            def dword(address):
                nonlocal dp
                address&=0xffffffff;sample=None
                if address:
                    sample=row.dword_samples[dp] if dp<len(row.dword_samples) else None;dp+=1
                p=plan_guarded_dword(address,sample);guards.append((index,p));steps.append(('0045dc44',index,address))
                if not p.complete:raise Missing('candidate%d: '%index+p.missing)
                return p.value_dword
            def byte(address):
                nonlocal bp
                address&=0xffffffff;sample=None
                if address:
                    sample=row.byte_samples[bp] if bp<len(row.byte_samples) else None;bp+=1
                p=plan_guarded_byte(address,sample);guards.append((index,p));steps.append(('0045dbdc',index,address))
                if not p.complete:raise Missing('candidate%d: '%index+p.missing)
                return p.eax_dword&255
            length=dword(pointer+g(0x553fec))&0xffff
            word4040=dword(pointer+g(0x554040))&0xffff
            word3fdc=dword(pointer+g(0x553fdc))&0xffff
            steps.append(('0045ddb8',index,(pointer+g(0x554008))&0xffffffff))
            normal(row.x_read_returned,'candidate%d x getter/FSTP'%index);x=need(row.x_float_bits,'candidate x float bits')
            steps.append(('0045ddb8',index,(pointer+g(0x554010))&0xffffffff))
            normal(row.y_read_returned,'candidate%d y getter/FSTP'%index);y=need(row.y_float_bits,'candidate y float bits')
            steps.append(('00460548/__ftol/FILD/FSTP',index,y,x))
            distance=need(row.metric_ftol_dword,'candidate metric __ftol low DWORD')
            if need(row.context39_byte,'context BYTE39'):
                if byte(pointer+g(0x554034))==4:continue
                if byte(pointer+g(0x554034))==5:continue
            name_address=(pointer+g(0x553fe8))&0xffffffff
            if length>=16:name_address=dword(name_address)
            request=TextReadRequest(name_address,length,length>=16)
            steps.append(('name_request',index,request))
            normal(row.name_span_returned,'candidate%d name copy/conversion/assignment/cleanup'%index)
            name=row.name_text;copy=None
            if row.name_capture is not None:
                if name is not None:raise ValueError('Bound name capture conflicts with raw Unicode name')
                c=row.name_capture;copy=replay_text_copy(length,c.readable,c.copied_bytes,codec=c.codec)
                names.append((index,request,copy))
                if copy.status!='complete':raise Missing('candidate name copy: '+copy.status)
                name=copy.text
            else:names.append((index,request,None))
            # Both words were truncated before these comparisons; cached/ref
            # helper DWORDs are NOT truncated to their low WORD.
            if word4040==cached:continue
            steps.append(('004626b0',index));reference=row.reference_4626b0_dword
            if row.reference_462690_samples:
                if reference is not None:raise ValueError('Bound mapped reference conflicts with raw004626b0 EAX')
                values=row.reference_462690_samples;first=need(values[0],'first00462690 EAX')
                steps.append(('00462690',index,0))
                if first==1:reference=2
                else:
                    steps.append(('00462690',index,1))
                    if len(values)<2:raise Missing('fresh second00462690 EAX')
                    reference=1 if need(values[1],'second00462690 EAX')==2 else 0
            reference=need(reference,'004626b0 EAX DWORD')
            def radius(value,ah,label):
                value=need(value,label+' DWORD');status=need(ah,label+' fresh comparison AH')
                steps.append(('radius_vs_metric_float',index,label,value,distance,status))
                return status&5==0
            def name_filter(kind,address):
                steps.append((address,index,name))
                bound=getattr(row,kind+'_name_execution');raw=getattr(row,kind+'_name_al')
                if bound is None:return need(raw,address+' normal-return AL')
                if raw is not None:raise ValueError('Bound name filter conflicts with raw AL')
                if bound.kind!=kind:raise ValueError('Wrong bound name filter kind')
                text=need(name,'query Unicode name for bound filter')
                if bound.input_text is None or utf16_key(bound.input_text)!=utf16_key(text):raise ValueError('Bound name filter input mismatch')
                if not bound.complete:raise Missing('bound name filter: '+bound.missing)
                normal(getattr(row,kind+'_name_returned'),address+' independent bound normal return')
                return need(bound.al,'bound name filter AL')
            def primary():return name_filter('primary','0046c1a0')
            def secondary():return name_filter('secondary','0046c2ac')
            if word3fdc!=reference:
                if not radius(anti_radius,row.anti_radius_ah,'anti radius'):continue
                if primary()==0:set_output(0,index)
                if secondary():set_output(2,index)
            else:
                chosen=anti_radius if need(row.context8_byte,'context BYTE8') else enemy_radius
                if not radius(chosen,row.selected_radius_ah,'selected radius'):continue
                if primary()==0:
                    if radius(anti_radius,row.anti_radius_ah,'anti radius'):set_output(0,index)
                    set_output(1,index)
                if secondary():set_output(2,index)
        normal(o.final_cleanup_returned,'0046d2ed..0046d2f8 final Unicode cleanup')
        return result(True,'query_scan_modeled')
    except Missing as e:return result(False,'needs_observation',str(e))
