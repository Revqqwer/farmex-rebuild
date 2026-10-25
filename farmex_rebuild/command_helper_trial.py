"""Reached-only JSON adapter for inert command helpers; no native execution."""
from copy import deepcopy
from action_queue import QueueState
from command_helpers import CommandQueueFrame,TownFrame,TownObservation
from motion_genie_helpers import MotionGenieFrame,MotionGenieObservation,GuardedReadReceipt
from bot_switch import BotSwitchFrame,BotSwitchObservation

def _mapping(raw,name):
    v=raw.get(name,{})
    if type(v) is not dict:raise ValueError('Reached helper '+name+' must be an object')
    return v

def _row(raw,name,index):
    rows=raw.get(name,[])
    if type(rows) is not list:raise ValueError('Reached helper '+name+' must be an array')
    return None if index>=len(rows) else rows[index]

def _pair(row):
    if type(row) is not list or len(row)!=2:raise ValueError('Reached address/value array required')
    return tuple(row)

def _normal(raw,name,label):
    rows=_mapping(raw,name)
    if label not in rows:return None
    v=rows[label]
    if type(v) is not bool:raise ValueError('Reached helper normal return must be boolean')
    return v

def _queue(frame,raw):
    p=frame.advance()
    if not p.complete and p.missing=='enqueue connection gate' and 'gate' in raw:
        p=frame.advance(gate=raw['gate'])
    if not p.complete and p.missing=='enqueue GetTickCount' and 'tick' in raw:
        p=frame.advance(tick=raw['tick'])
    return p

def _town(frame,raw):
    for _ in range(32):
        p=frame.advance(TownObservation())
        if p.complete:return p
        if p.missing.endswith(' normal return'):
            label=p.missing[:-14];v=_normal(raw,'helper_returns',label)
            if v is not True:return p
            o=TownObservation(helper_returns={label:True})
        elif p.missing=='Town buffer allocation EAX':
            if 'buffer_address' not in raw:return p
            o=TownObservation(buffer_address=raw['buffer_address'])
        elif p.missing.startswith('Town source global'):
            cached=frame.observation.global_samples;row=_row(raw,'global_samples',len(cached))
            if row is None:return p
            o=TownObservation(global_samples=cached+(_pair(row),))
        else:return p #Includes unresolved null-allocation fault path.
        p=frame.advance(o)
        if p.complete:return p
    raise ValueError('Town JSON adapter exceeded source prefix budget')

def _motion_genie(frame,raw):
    for _ in range(40):
        p=frame.advance(MotionGenieObservation())
        if p.complete:return p
        req=p.request
        if req.kind=='normal':
            v=_normal(raw,'normal_returns',req.label)
            if v is not True:return p
            o=MotionGenieObservation(normal_returns={req.label:True})
        else:
            name={'global':'global_samples','direct':'direct_samples','guarded':'guarded_reads'}[req.kind]
            row=_row(raw,name,req.index)
            if row is None:return p
            cached=getattr(frame.observation,name)
            if req.kind=='guarded':
                if type(row) is not dict:raise ValueError('Reached guarded receipt must be an object')
                v=row.get('normal_returned')
                if v is not None and type(v) is not bool:raise ValueError('Reached guarded normal return must be boolean')
                if v is not True:return p
                if not all(k in row for k in ('address','width','eax')):return p
                value=GuardedReadReceipt(row['address'],row['width'],row['eax'],True)
            else:value=_pair(row)
            o=MotionGenieObservation(**{name:cached+(value,)})
        p=frame.advance(o)
        if p.complete:return p
    raise ValueError('Operand JSON adapter exceeded source prefix budget')

def _switch(frame,raw):
    for _ in range(40):
        p=frame.advance(BotSwitchObservation())
        if p.complete:return p
        kind,label=p.request
        if kind=='normal':
            v=_normal(raw,'normal_returns',label)
            if v is not True:return p
            o=BotSwitchObservation(normal_returns={label:True})
        else:
            values=_mapping(raw,'values')
            if label not in values:return p
            o=BotSwitchObservation(values={label:values[label]})
        p=frame.advance(o)
        if p.complete:return p
    raise ValueError('Switch JSON adapter exceeded source prefix budget')

class CommandHelpersTrial:
    """One captured command invocation, with one ordered shared own queue."""
    def __init__(self):self.frames={};self.queue=QueueState();self.queue_committed=set()
    def advance(self,action,raw):
        if type(raw) is not dict:raise ValueError('Reached command helper sample must be an object')
        key=action.key
        if key not in self.frames:
            if key in ('disconnect','stand'):frame=CommandQueueFrame(key,self.queue)
            elif key=='town':frame=TownFrame()
            elif key in ('return_center','genie_start','genie_stop'):frame=MotionGenieFrame(action.helper,action.push_order)
            elif key in ('bot_start','bot_stop'):frame=BotSwitchFrame(action.push_order[1],action.push_order[0])
            else:raise ValueError('Known command helper required')
            self.frames[key]=(action.helper,action.push_order,frame)
        helper,pushes,frame=self.frames[key]
        if helper!=action.helper or pushes!=action.push_order:raise ValueError('Command helper invocation operands changed')
        if key in ('disconnect','stand'):
            p=_queue(frame,raw)
            if p.complete and key not in self.queue_committed:
                self.queue=frame.queue;self.queue_committed.add(key)
            return p
        if key=='town':return _town(frame,raw)
        if key in ('bot_start','bot_stop'):return _switch(frame,raw)
        return _motion_genie(frame,raw)

def synthetic_command_helpers():
    """Invented operands and positive receipts, never populated from a game."""
    def guarded(address,width,eax):return dict(address=address,width=width,eax=eax,normal_returned=True)
    genie=dict(global_samples=[[0x553e80,0x2000],[0x554178,0x10],[0x55417c,0x14],
                              [0x554180,0x18],[0x553e80,0x3000],[0x554178,0x20],[0x554200,0x30]],
               guarded_reads=[guarded(0x2000,4,0x4000),guarded(0x4010,4,0x5000),
                              guarded(0x5014,4,0xaaaa),guarded(0x5018,4,0xbbbb)],
               direct_samples=[[0x3000,0x6000],[0x6020,0x7000],[0x7000,0x8000],[0x8030,0x9000]],
               normal_returns={'indirect_target':True})
    town_labels=('town_string_construct','text_string_lifetime','allocate_record','strlen','zero_record',
                 'copy_text','copy_length','copy_type','patch_root','patch_buffer','patch_target',
                 'thread_helper','free_record','text_cleanup','text_helper','town_cleanup')
    return dict(disconnect=dict(gate=1,tick=100),stand=dict(gate=1,tick=101),
        return_center=dict(global_samples=[[0x553e7c,0x2000],[0x554014,0x10],[0x554018,0x14],[0x55401c,0x18],[0x554020,0x20]],
            guarded_reads=[guarded(0x2000,4,0x1000),guarded(0x1020,1,2)],
            normal_returns=dict(write_moving=True,write_x=True,write_y=True)),
        genie_start=genie,genie_stop=deepcopy(genie),
        bot_start=dict(values=dict(base_started_byte=1,mode_for_zero=5,mode_for_two=5,mode_for_four=5,mode_for_five=5),
            normal_returns=dict(switch_frame_setup=True,base_frame_setup=True,activation_helper=True)),
        bot_stop=dict(values=dict(stop_mode_for_two=5,stop_genie_state_eax=0),
            normal_returns=dict(switch_frame_setup=True,base_frame_setup=True,stop_caption_span=True,
                stop_notification_span=True,activation_helper=True,stop_genie_state=True,stop_movement=True)),
        town=dict(buffer_address=0x1000,global_samples=[[0x553e80,0x2000],[0x553eec,0x3000]],
            helper_returns={name:True for name in town_labels}))
