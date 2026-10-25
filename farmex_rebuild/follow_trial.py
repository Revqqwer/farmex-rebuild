"""Own UI follow trial: fresh panel snapshot, reached-only JSON observations."""
import json
from dataclasses import replace
from follow_engine import FollowState,FollowObservation,compile_follow_panel,plan_follow_tail
from source_unicode import UnicodeEqualityObservation

SCALARS={
 'earlier caller reached0040e550':'entry_reached','second mode DWORD':'second_mode_dword',
 'party count DWORD':'party_count_dword','leader ID WORD':'leader_id_word',
 'entity pointer DWORD':'pointer_dword','name lookup ID DWORD':'name_id_dword',
 'initialized previous Unicode name':'initialized_previous_name',
 'post-FUCOMPP status WORD':'distance_status_word',
 'manual Y post-FADD/FSTP float bits':'manual_y_after_add_bits'}
RETURNS=('party_count','entity_lookup','coord_x','coord_y','distance','movement',
         'initialize_previous_name','empty_temporary_cleanup','copy_previous_name','name_lookup')

def parse_follow_sample(text,c,state):
    try:raw=json.loads(text)
    except (ValueError,TypeError) as e:raise ValueError('Follow observations must be a JSON object') from e
    if type(raw) is not dict:raise ValueError('Follow observations must be a JSON object')
    o=FollowObservation();seen=set()
    for _ in range(45):
        p=plan_follow_tail(c,state,o)
        if p.complete:return o
        missing=p.missing;field=SCALARS.get(missing);key=None;value=None
        if field:
            key=field
            if field not in raw:return o
            value=raw[field]
        elif missing.endswith(' normal return') and missing[:-14] in RETURNS:
            label=missing[:-14];key=('return',label)
            returns=raw.get('helper_returns',{})
            if type(returns) is not dict:raise ValueError('Follow helper returns must be an object')
            if label not in returns:return o
            value=returns[label]
            if type(value) is not bool:raise ValueError('Follow helper return must be boolean: '+label)
            field='helper_returns';value={**o.helper_returns,label:value}
        elif missing.startswith('empty name') or missing.startswith('previous name'):
            field='empty_equal' if missing.startswith('empty name') else 'previous_equal';key=field
            if field not in raw:return o
            v=raw[field]
            if type(v) is not dict:raise ValueError('Follow comparison must be an object')
            v=dict(v)
            if v.get('use_owned_text_model') is True:
                v.setdefault('left_text',c.nickname)
                v.setdefault('right_text','' if field=='empty_equal' else p.state.previous_name)
            try:value=UnicodeEqualityObservation(**v)
            except TypeError as e:raise ValueError('Unknown follow comparison field') from e
        else:
            for index,label in enumerate(('coord_x','coord_y')):
                if missing in (label+' offset DWORD',label+' post-FSTP float bits'):
                    field='coordinate_offsets' if missing.endswith('offset DWORD') else 'coordinate_bits'
                    key=(field,index);seq=raw.get(field,[])
                    if type(seq) is not list:raise ValueError('Follow coordinate samples must be arrays')
                    if index>=len(seq):return o
                    prefix=list(getattr(o,field))
                    while len(prefix)<=index:prefix.append(None)
                    prefix[index]=seq[index];value=tuple(prefix);break
        if key is None or key in seen:return o
        seen.add(key);o=replace(o,**{field:value})
    raise ValueError('Follow observation parser exceeded its reached-field budget')

def example_follow_sample():
    """Explicit user-loaded synthetic fixture, never a live observation."""
    return json.dumps(dict(entry_reached=True,second_mode_dword=2,party_count_dword=1,leader_id_word=2,
        pointer_dword=4096,name_id_dword=7,initialized_previous_name='',
        empty_equal=dict(helper_returned=True,use_owned_text_model=True),
        previous_equal=dict(helper_returned=True,use_owned_text_model=True),
        coordinate_offsets=[16,32],coordinate_bits=[0x41200000,0x41a00000],
        distance_status_word=0,manual_y_after_add_bits=0x41c00000,
        helper_returns={name:True for name in RETURNS}),ensure_ascii=False)

class FollowTrial:
    def __init__(self,configuration_reader):
        self.configuration_reader=configuration_reader;self.reset()
    def reset(self):
        self.state=FollowState();self.last=None;self.configuration=None
    def step(self,text):
        self.last=None
        if self.configuration_reader is None:raise ValueError('Follow trial needs a panel configuration reader')
        values,_=self.configuration_reader()
        c=compile_follow_panel(values);self.configuration=c
        o=parse_follow_sample(text,c,self.state)
        p=plan_follow_tail(c,self.state,o)
        self.state=p.state;self.last=p
        return p
