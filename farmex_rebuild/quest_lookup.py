"""004d642c reached-only scan; normal helper effects require explicit receipts.

No game reads, Unicode guessing or native helpers are executed. The pinned
ordinary return is FFFFFFFF, but it is withheld until the scan and cleanup end.
"""
from dataclasses import dataclass,field,replace
from collections.abc import Mapping
from quest_name_compare import QuestNameCompareFrame,QuestNameCompareObservation,AnsiCompareSample
from quest_read_string import QuestReadStringFrame,QuestReadStringObservation


def dword(value):
    if type(value) is not int or not 0<=value<=0xffffffff:
        raise ValueError('Raw DWORD required')
    return value


def signed(value):
    return value if value<0x80000000 else value-0x100000000


@dataclass(frozen=True)
class QuestLookupObservation:
    # Tokens are (iteration ordinal, role); -1 is the argument lifetime.
    values:object=field(default_factory=dict)
    normal_returns:object=field(default_factory=dict)
    name_compares:object=field(default_factory=dict)
    name_reads:object=field(default_factory=dict)
    use_read_name_operands:bool=False


@dataclass(frozen=True)
class QuestLookupPlan:
    complete:bool
    status:str
    index_dword:int
    iteration:int
    needed:object=None
    eax:object=None
    calls:tuple=()
    reads:tuple=()
    mode_comparisons:tuple=()
    native_execution_verified:bool=False
    live_compatibility_verified:bool=False
    name_compare_plans:tuple=()
    name_read_plans:tuple=()
    owned_name_values:tuple=()


class QuestLookupFrame:
    def __init__(self,display_name,mode,lower,upper):
        if type(display_name) is not bytes:raise ValueError('Immutable own name snapshot required')
        self.name=display_name;self.mode=dword(mode);self.index=dword(lower);self.upper=dword(upper)
        self.iteration=0;self.phase='entry';self.cache={};self.normal=set();self.called=set()
        self.calls=[];self.reads=[];self.comparisons=[];self.final=None
        self.name_compare_modes={};self.name_compare_frames={};self.name_compare_results={}
        self.name_operand_bridge_policies={}
        self.name_read_modes={};self.name_read_frames={};self.name_read_results={};self.name_values={}

    def out(self,status,needed=None,complete=False):
        result=QuestLookupPlan(complete,status,self.index,self.iteration,needed,
            0xffffffff if complete else None,tuple(self.calls),tuple(self.reads),tuple(self.comparisons),
            name_compare_plans=tuple(sorted(self.name_compare_results.items())),
            name_read_plans=tuple(sorted(self.name_read_results.items())),
            owned_name_values=tuple(sorted(self.name_values.items())))
        if complete:self.final=result
        return result

    def advance(self,observation=None,*,step_budget=256):
        if self.final is not None:return self.final
        o=QuestLookupObservation() if observation is None else observation
        if not isinstance(o,QuestLookupObservation) or any(not isinstance(v,Mapping) for v in (o.values,o.normal_returns,o.name_compares,o.name_reads)):
            raise ValueError('Typed sparse lookup observations required')
        if type(step_budget) is not int or not 1<=step_budget<=100000:
            raise ValueError('Bounded own continuation budget required')
        class Missing(Exception):pass
        def key(label):
            return (-1 if label in ('entry','argument_copy','argument_cleanup') else self.iteration,label)
        def request(label,helper,args=()):
            token=key(label)
            if token not in self.called:
                self.called.add(token);self.calls.append((helper,args,token))
        def normal(label,helper,args=()):
            token=key(label);request(label,helper,args)
            if token not in self.normal:
                receipt=o.normal_returns.get(token)
                if receipt is not None and type(receipt) is not bool:raise ValueError('Explicit normal-return boolean required')
                if receipt is not True:raise Missing(('normal',token))
                self.normal.add(token)
        def value(label,helper,args=(),address=None,width=32):
            token=key(label)
            normal(label,helper,args)
            if token not in self.cache:
                if token not in o.values:raise Missing(('value',token))
                raw=dword(o.values[token]);self.cache[token]=raw
                if address is not None:self.reads.append((address,width,token,raw if width==32 else raw&255))
            return self.cache[token]
        def cached(label):return self.cache[key(label)]
        def read(label,base,offset,width=32):
            address=(base+offset)&0xffffffff
            raw=value(label,'0045dc44' if width==32 else '0045dbdc',(address,),address,width)
            return raw if width==32 else raw&255
        try:
            for _ in range(step_budget):
                phase=self.phase
                if phase=='entry':
                    normal('entry','source prologue and SEH setup span');self.phase='argument_copy'
                elif phase=='argument_copy':
                    normal('argument_copy','managed argument copy span',(self.name,));self.phase='range'
                elif phase=='range':
                    self.phase='argument_cleanup' if signed(self.index)>signed(self.upper) else 'record'
                elif phase=='record':
                    pointer=value('record','004d51c4',('owned_quest_context',self.index))
                    self.phase='metadata_key' if pointer else 'increment'
                elif phase=='metadata_key':
                    read('metadata_key',cached('record'),0x50);self.phase='metadata'
                elif phase=='metadata':
                    pointer=value('metadata','004d51f0',('owned_quest_context',cached('metadata_key')))
                    self.phase='name_init' if pointer else 'increment'
                elif phase=='name_init':
                    normal('name_init','004040bc',('owned_name', 'literal_0054a099'));self.phase='storage'
                elif phase=='storage':
                    storage=read('storage',cached('metadata'),0x20)
                    if signed(storage)>=16:self.phase='name_pointer'
                    else:
                        self.cache[key('copy_address')]=(cached('metadata')+0x10)&0xffffffff
                        self.cache[key('copy_count')]=15;self.phase='temp_init'
                elif phase=='name_pointer':
                    self.cache[key('copy_address')]=read('name_pointer',cached('metadata'),0x10)
                    self.cache[key('copy_count')]=cached('storage');self.phase='temp_init'
                elif phase=='temp_init':
                    normal('temp_init','00404148',('owned_indirect_temp' if signed(cached('storage'))>=16 else 'owned_inline_temp',))
                    self.phase='name_read'
                elif phase=='name_read':
                    ordinal=self.iteration;args=('owned_name_temp',cached('copy_address'),cached('copy_count'))
                    request('name_read','0045dca8',args)
                    if ordinal not in self.name_read_modes:
                        if ordinal in o.name_reads:
                            if not isinstance(o.name_reads[ordinal],QuestReadStringObservation):raise ValueError('Typed nested read-string capture required')
                            self.name_read_modes[ordinal]='composed'
                            self.name_read_frames[ordinal]=QuestReadStringFrame(args[1],args[2])
                        elif key('name_read') in o.normal_returns:self.name_read_modes[ordinal]='captured'
                        else:raise Missing(('name_read_input',ordinal))
                    if self.name_read_modes[ordinal]=='composed':
                        child=self.name_read_frames[ordinal]
                        result=child.advance(o.name_reads.get(ordinal));self.name_read_results[ordinal]=result
                        if not result.complete:raise Missing(('name_read',ordinal,child.phase,result.needed or result.status))
                        normal('name_read','0045dca8',args)
                        self.cache[key('name_temp_ansi')]=result.destination_ansi
                    else:normal('name_read','0045dca8',args)
                    self.phase='name_assign'
                elif phase=='name_assign':
                    normal('name_assign','managed name assignment span',('owned_name','owned_name_temp'))
                    if key('name_temp_ansi') in self.cache:self.name_values[self.iteration]=cached('name_temp_ansi')
                    self.phase='temp_cleanup'
                elif phase=='temp_cleanup':
                    normal('temp_cleanup','004040f8',('owned_name_temp',2));self.phase='name_compare'
                elif phase=='name_compare':
                    ordinal=self.iteration;args=('owned_name',self.name)
                    request('name_compare','managed ANSI name equality span',args)
                    if ordinal not in self.name_compare_modes:
                        if ordinal in o.name_compares:
                            if not isinstance(o.name_compares[ordinal],QuestNameCompareObservation):raise ValueError('Typed nested ANSI comparison required')
                            self.name_compare_modes[ordinal]='composed'
                            self.name_compare_frames[ordinal]=QuestNameCompareFrame()
                        elif key('name_compare') in o.values:self.name_compare_modes[ordinal]='captured'
                        else:raise Missing(('name_compare_input',ordinal))
                    if self.name_compare_modes[ordinal]=='composed':
                        child=self.name_compare_frames[ordinal]
                        sample=o.name_compares.get(ordinal)
                        if ordinal not in self.name_operand_bridge_policies:
                            if type(o.use_read_name_operands) is not bool:raise ValueError('Explicit owned read-name bridge policy required')
                            self.name_operand_bridge_policies[ordinal]=o.use_read_name_operands
                        if self.name_operand_bridge_policies[ordinal] and isinstance(sample,QuestNameCompareObservation):
                            fields={}
                            for role in ('greater','less'):
                                operand=getattr(sample,role)
                                if isinstance(operand,AnsiCompareSample) and operand.use_owned_bytes:
                                    left=operand.left_bytes
                                    if left is None:
                                        if ordinal not in self.name_values:raise Missing(('owned_name_bytes',ordinal))
                                        left=self.name_values[ordinal]
                                    right=operand.right_bytes if operand.right_bytes is not None else self.name
                                    fields[role]=replace(operand,left_bytes=left,right_bytes=right)
                            sample=replace(sample,**fields)
                        result=child.advance(sample)
                        self.name_compare_results[ordinal]=result
                        if not result.complete:raise Missing(('name_compare',ordinal,child.phase,result.needed))
                        normal('name_compare','managed ANSI name equality span',args)
                        self.cache[key('name_compare')]=result.eax
                        equal=result.eax
                    else:equal=value('name_compare','managed ANSI name equality span',args)&255
                    self.phase='nation_gate' if equal else 'name_cleanup'
                elif phase=='nation_gate':
                    self.phase='class_gate' if read('nation_gate',cached('record'),0x19,8)==3 else 'nation_value'
                elif phase=='nation_value':
                    read('nation_value',cached('record'),0x19,8);self.phase='nation_current'
                elif phase=='nation_current':
                    current=value('nation_current','00462690')
                    self.phase='class_gate' if cached('nation_value')&255==current else 'name_cleanup'
                elif phase=='class_gate':
                    self.phase='mode' if read('class_gate',cached('record'),0x18,8)==5 else 'class_value'
                elif phase=='class_value':
                    read('class_value',cached('record'),0x18,8);self.phase='class_current'
                elif phase=='class_current':
                    current=value('class_current','004d4f60',('owned_quest_context',))&255
                    self.phase='mode' if cached('class_value')&255==current else 'name_cleanup'
                elif phase=='mode':
                    mode=read('mode',cached('record'),0x24,8)
                    self.comparisons.append((self.iteration,self.index,mode,self.mode,mode==self.mode))
                    # No source success branch follows this CMP.
                    self.phase='name_cleanup'
                elif phase=='name_cleanup':
                    normal('name_cleanup','004040f8',('owned_name',2));self.phase='increment'
                elif phase=='increment':
                    self.index=(self.index+1)&0xffffffff;self.iteration+=1;self.phase='range'
                elif phase=='argument_cleanup':
                    normal('argument_cleanup','004040f8',('owned_argument',2))
                    return self.out('normal_return',complete=True)
                else:raise AssertionError('Unknown lookup phase')
            return self.out('yielded')
        except Missing as error:
            return self.out('needs_observation',error.args[0])
