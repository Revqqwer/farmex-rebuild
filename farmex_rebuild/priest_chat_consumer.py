"""4cee18 normal-path Priest consumer; native/FPU/helper effects unverified."""
from chat_skill_consumers import ChatConsumerObservation,ChatConsumerPlan
from generic_chat_skill import generic_binding_gap
from direct_chat_packets import DirectChatArgs,direct_binding_gap

def _signed(v):return v-(1<<32) if v&0x80000000 else v
class _Missing(Exception):
    def __init__(self,kind,label):self.needed=(kind,label);super().__init__('bound generic: '+label if kind=='bound' else 'bound direct: '+label if kind=='direct' else label+(' normal return' if kind=='normal' else ' value'))

def plan_priest_chat_consumer(context_dword,o):
    if type(context_dword) is not int or not 0<=context_dword<=0xffffffff or not isinstance(o,ChatConsumerObservation):
        raise ValueError('Typed Priest actor context/observations required')
    steps=[];stores=[];bound=None;direct_bound=None
    def result(low=None,error=None):
        return ChatConsumerPlan('Priest',error is None,low,tuple(stores),tuple(steps),'' if error is None else str(error),None if error is None else error.needed,generic_execution=bound,actor_context_dword=context_dword,direct_execution=direct_bound)
    def value(label):
        steps.append(('source_value',label))
        if label not in o.values:raise _Missing('value',label)
        return o.values[label]
    def call(label,address,pushes=()):
        steps.append(('opaque_helper',address,pushes,label))
        if o.normal_returns.get(label) is not True:raise _Missing('normal',label)
    def store(address,width,v):
        address &=0xffffffff;stores.append((address,width,v));steps.append(('store_plan',address,width,v))
    def clear_false():store(0x5693a0,1,0);return result(0)
    def state(prefix,slot):
        root_slot=value(prefix+'_root_slot');steps.append(('source_global',0x553e7c,root_slot))
        call(prefix+'_root','0045dc44',(root_slot,));root=value(prefix+'_root_eax')
        offset=value(prefix+'_offset');steps.append(('source_global',slot,offset))
        call(prefix+'_state','0045dc44',((root+offset)&0xffffffff,))
        return value(prefix+'_state_eax')
    def target_cleanup():
        call('target_probe','00462630');steps.append(('TEST_EAX_EAX_CF',0,'source_JC_not_taken'))
        if state('target',0x55403c):
            steps.append(('push_literal_before_target_helper',0));call('fresh_target_id','00462630')
            call('target_action','00465ef8',(0,value('fresh_target_eax')))
    def lock(delay):
        store(0x561f80,4,delay);call('post_delay_tick','GetTickCount')
        store(0x561f84,4,value('post_delay_tick'));store(0x561f7e,1,1)
    def choose_skill(field,label,helper):
        raw=value(field)
        if _signed(raw)>0:return raw
        call(label,helper,(context_dword,));return value(label+'_eax')
    def party_select():
        call('party_lookup','004cb898',(value('lookup_sender_dword'),0x569584))
        index=value('party_index_eax')
        if _signed(index)<0:return False
        target_cleanup();call('select_index','00464650',(index,));return True
    def in_range(allow_null):
        call('object_lookup','00464a10',(value('object_sender_dword'),));obj=value('object_eax')
        if obj==0:return allow_null
        xoff=value('target_x_offset');steps.append(('source_global',0x554008,xoff))
        call('target_x','0045ddb8',((obj+xoff)&0xffffffff,));x=value('target_x_f32_bits')
        yoff=value('target_y_offset');steps.append(('source_global',0x554010,yoff))
        call('target_y','0045ddb8',((obj+yoff)&0xffffffff,));y=value('target_y_f32_bits')
        call('distance','00460548',(y,x));call('distance_integer_convert','source_ftol_import')
        return _signed(value('distance_integer_eax'))<=28
    try:
        if value('pending_byte')==0:return result(0)
        if value('lock_byte')!=0:return result(0)
        # Both fields/resolvers precede every reached request-kind comparison.
        buff=choose_skill('context_fc_dword','buff_resolver','004ce71c')
        ac=choose_skill('context_104_dword','ac_resolver','004ce840')
        kind=None
        for candidate in range(1,7):
            if value('kind_%d_dword'%candidate)==candidate:kind=candidate;break
        if kind is None:return result(0)
        if kind==1:
            call('priest_gate','004645e4')
            if _signed(value('priest_gate_eax'))<2:return clear_false()
        elif kind==3:
            call('und_gate','00462e08')
            if _signed(value('und_gate_eax'))<54:return clear_false()
            call('priest_gate','004645e4')
            if _signed(value('priest_gate_eax'))<2:return clear_false()
        elif kind in (4,5,6):
            call('kind_gate','00462670' if kind==4 else '00462ddc')
            if _signed(value('kind_gate_eax'))<{4:4,5:25,6:35}[kind]:return clear_false()
        if kind in (1,3) and not party_select():return clear_false()
        if not in_range(kind in (1,3)):return clear_false()
        if kind not in (1,3):target_cleanup()
        skill={1:buff,2:ac,3:0x28e,4:4,5:0x20d,6:0x217}[kind]
        if value('alternate_byte')!=0:
            sender=value('generic_sender_dword');bound=o.generic_execution
            gap=generic_binding_gap(bound,skill,sender)
            if gap is not None:raise _Missing('bound',gap)
            call('generic_skill','004655e8',(sender,skill))
            eax=value('generic_skill_eax')
            if bound is not None and eax!=bound.returned_eax:raise ValueError('Priest EAX differs from bound generic raw return')
            if eax==0:return result(0)
            lock(2000);store(0x5693a0,1,0)
            if kind in (2,4,5,6):
                call('stamp_lookup','004cb898',(value('stamp_sender_dword'),0x569584))
                index=value('stamp_index_eax')
                if _signed(index)>=0:
                    call('party_stamp_tick','GetTickCount')
                    # Source has no upper index bound here; own store remains inert.
                    store(0x56970c+index*4,4,value('party_stamp_tick'))
            return result(1)
        if state('movement',0x554020):call('stop_movement','00464714')
        lock(1500);store(0x5693a0,1,0) #Before direct helper, unlike Mage/Rogue.
        if kind in (1,2,3,5,6):
            word=value('direct_sender_word');sender=value('direct_sender_push_dword')
            if sender&0xffff!=word:raise ValueError('Priest full EDX push differs from fresh sender WORD')
        else:sender=value('direct_sender_dword')
        helper='004d3568' if kind in (1,2,3) else {4:'004d36ac',5:'004d3674',6:'004d3690'}[kind]
        args=DirectChatArgs(helper,context_dword,sender,skill if kind in (1,2,3) else None)
        direct_bound=o.direct_execution;gap=direct_binding_gap(direct_bound,args)
        if gap is not None:raise _Missing('direct',gap)
        call('direct_skill',helper,args.push_order)
        return result(1)
    except _Missing as error:return result(error=error)
