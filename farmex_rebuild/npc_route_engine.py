"""Richard004f11a0 phases1..11: local raw-state replay, no game IO.

Comparison results are supplied observations of00505d20, not guessed text
semantics. Source subengines and ANSI-to-Unicode conversion remain explicit
helper observations; raw memory is never inferred from pointer arguments.
"""
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Mapping, Tuple
from game_text import npc_text_request, replay_text_copy
from npc_lookup import select_npc
from enchant_engine import enchant_step
from zone_names import zone_name_ansi
from repair_engine import repair_step
from npc_sell_engine import NpcSaleState,npc_sale_step
from npc_sell_packets import NpcSellRecord
from npc_buy_packets import NpcBuyRecord
from npc_buy_engine import NpcBuyState,npc_buy_step


@dataclass(frozen=True)
class NpcRouteFrame:
    phase: int
    fields: Mapping[int, int] = field(default_factory=dict)
    globals: Mapping[int, int] = field(default_factory=dict)
    texts: Mapping[int, str] = field(default_factory=dict)
    sale_batch: Tuple[NpcSellRecord,...] = ()
    buy_batch: Tuple[NpcBuyRecord,...] = ()

    def __post_init__(self):
        if type(self.phase) is not int or not 0 <= self.phase <= 0xffffffff:
            raise ValueError('phase must be DWORD')
        for mapping in (self.fields, self.globals):
            if any(type(k) is not int or type(v) is not int for k,v in mapping.items()):
                raise ValueError('raw fields must be integer mappings')
        object.__setattr__(self,'fields',MappingProxyType(dict(self.fields)))
        object.__setattr__(self,'globals',MappingProxyType(dict(self.globals)))
        if any(type(k) is not int or type(v) is not str for k,v in self.texts.items()):
            raise ValueError('Text fields must be integer/string mappings')
        object.__setattr__(self,'texts',MappingProxyType(dict(self.texts)))
        if any(not isinstance(row,NpcSellRecord) for row in self.sale_batch):raise ValueError('Typed sale records required')
        object.__setattr__(self,'sale_batch',tuple(self.sale_batch))
        if any(not isinstance(row,NpcBuyRecord) for row in self.buy_batch):raise ValueError('Typed purchase records required')
        object.__setattr__(self,'buy_batch',tuple(self.buy_batch))


@dataclass(frozen=True)
class NpcRouteResult:
    status: str
    frame: NpcRouteFrame
    returned_true: bool = False
    calls: Tuple[str, ...] = ()
    missing: str = ''
    text_request: object = None
    queue_payloads: Tuple[bytes,...] = ()
    cache_writes: Tuple[Tuple[int,int],...] = ()


@dataclass(frozen=True)
class NpcRouteObservation:
    frame: NpcRouteFrame
    matches: Mapping[str, bool]
    helpers: Mapping[str, int] = field(default_factory=dict)
    inn_in_moradon: object = None
    inn_distance: object = None
    observed_text: object = None
    text_readable: object = None
    copied_bytes: object = None
    codec: object = None
    lookup_candidates: object = None
    lookup_traversal_complete: object = None
    enchant_observation: object = None
    raw_zone_id: object = None
    repair_observation: object = None
    sale_observation: object = None
    buy_observation: object = None

    def step(self):
        return npc_route_step(self.frame,self.matches,self.helpers,
                              inn_in_moradon=self.inn_in_moradon,
                              inn_distance=self.inn_distance,observed_text=self.observed_text,
                              text_readable=self.text_readable,copied_bytes=self.copied_bytes,codec=self.codec,
                              lookup_candidates=self.lookup_candidates,
                              lookup_traversal_complete=self.lookup_traversal_complete,
                              enchant_observation=self.enchant_observation,raw_zone_id=self.raw_zone_id,
                              repair_observation=self.repair_observation,sale_observation=self.sale_observation,
                              buy_observation=self.buy_observation)


class _Unknown(Exception):
    pass


def npc_route_step(frame, matches, helpers=None, *, inn_in_moradon=None,
                   inn_distance=None, observed_text=None, text_readable=None,
                   copied_bytes=None, codec=None, lookup_candidates=None,
                   lookup_traversal_complete=None, enchant_observation=None,raw_zone_id=None,
                   repair_observation=None,sale_observation=None,buy_observation=None):
    if not isinstance(frame,NpcRouteFrame):
        raise ValueError('Typed source frame required')
    helpers={} if helpers is None else helpers
    fields,globals,texts=dict(frame.fields),dict(frame.globals),dict(frame.texts)
    phase=frame.phase
    calls=[]
    request=None
    nested_packets=[]
    nested_writes=[]
    sale_batch=list(frame.sale_batch)
    buy_batch=list(frame.buy_batch)
    if raw_zone_id is not None:
        zone_name_ansi(raw_zone_id)
        if inn_in_moradon is not None:raise ValueError('Choose observed Moradon comparison or raw zone ID, not both')
        inn_in_moradon=zone_name_ansi(raw_zone_id)==b'Moradon'

    def raw(mapping,key,label):
        if key not in mapping or mapping[key] is None:
            raise _Unknown(label)
        value=mapping[key]
        if type(value) is not int:
            raise ValueError('Raw source integer required: '+label)
        return value

    def f(offset):return raw(fields,offset,'field+%x'%offset)
    def g(address):return raw(globals,address,'global%08x'%address)
    def helper(address):
        calls.append(address)
        if address=='004efa84' and buy_observation is not None:
            if address in helpers:raise ValueError('Purchase observation conflicts with separate helper return')
            nested=npc_buy_step(NpcBuyState(fields,tuple(buy_batch)),buy_observation)
            fields.update(nested.state.fields);buy_batch[:]=nested.state.batch
            calls.extend(nested.calls);nested_packets.extend(nested.queue_payloads);nested_writes.extend(nested.cache_writes)
            if nested.status.startswith('unresolved') or nested.status=='needs_observation':
                raise _Unknown('purchase:'+nested.status+':'+nested.missing)
            return nested.returned_phase
        if address=='004eebf4' and sale_observation is not None:
            if address in helpers:raise ValueError('Sale observation conflicts with separate helper return')
            nested=npc_sale_step(NpcSaleState(fields,globals,tuple(sale_batch)),sale_observation)
            fields.update(nested.state.fields);globals.update(nested.state.globals);sale_batch[:]=nested.state.batch
            calls.extend(nested.calls);nested_packets.extend(nested.queue_payloads);nested_writes.extend(nested.cache_writes)
            if nested.status=='needs_observation':raise _Unknown('sale:'+nested.missing)
            return nested.returned_phase
        if address=='004edf34' and repair_observation is not None:
            if address in helpers:raise ValueError('Repair observation conflicts with separate helper return')
            nested=repair_step(fields,globals,repair_observation)
            fields.update(nested.fields);globals.update(nested.globals);calls.extend(nested.calls)
            nested_packets.extend(nested.queue_payloads)
            if nested.status=='needs_observation':raise _Unknown('repair:'+nested.missing)
            return nested.returned_phase
        if address=='004f035c' and enchant_observation is not None:
            if address in helpers:raise ValueError('Enchant observations conflict with separate helper result')
            nested=enchant_step(fields,enchant_observation)
            fields.update(nested.fields);calls.extend(nested.calls);nested_packets.extend(nested.queue_payloads)
            if nested.status=='needs_observation':raise _Unknown('enchant:'+nested.missing)
            return nested.returned_phase
        if address.startswith('00465960:') and lookup_candidates is not None:
            if address in helpers:raise ValueError('NPC lookup observations conflict with separate helper result')
            lookup=select_npc(lookup_candidates,address.split(':',1)[1].encode('ascii'),
                              traversal_complete=lookup_traversal_complete)
            if lookup.status!='complete':raise _Unknown('npc_lookup:'+lookup.missing)
            return lookup.candidate_id
        return raw(helpers,address,address+' return')
    def any_kind(kinds):
        for kind in kinds:
            value=matches.get(kind)
            if value is None:raise _Unknown('00505d20:'+kind)
            if type(value) is not bool:raise ValueError('Comparison observation must be boolean')
            if value:return True
        return False
    def signed(value):
        value &= 0xffffffff
        return value-0x100000000 if value&0x80000000 else value

    try:
        if phase==1:
            globals.update({0x5690cc:0,0x5690d8:0})
            filters={'Potion':'otion','Sundries':'undries','Armor':'rmor',
                     'Weapon':'eapon','DC Sundries':'DC Sund',
                     'Royal National Enchanter':'Royal National Enchanter'}
            for kind in ('Potion','Sundries','Inn Hostess','Armor','Weapon','DC Sundries','Royal National Enchanter'):
                if not any_kind((kind,)):continue
                if kind=='Inn Hostess':
                    if inn_in_moradon is None:raise _Unknown('Moradon comparison00505118')
                    if type(inn_in_moradon) is not bool:raise ValueError('Moradon observation must be boolean')
                    distant=False
                    if inn_in_moradon:
                        calls.append('00460548:409,555')
                        if inn_distance is None:raise _Unknown('00460548 distance')
                        import math
                        if type(inn_distance) not in (float,int) or not math.isfinite(inn_distance) or inn_distance<0:
                            raise ValueError('Finite nonnegative observed distance required')
                        distant=inn_distance>30
                    name='Kronil' if distant else 'Inn'
                else:name=filters[kind]
                fields[0x604]=helper('00465960:'+name)&0xffffffff
                break
            if (f(0x604)&0xffffffff)!=0:phase=2
        elif phase==2:
            # Lookup input604 is explicit even though helper observations are keyed by address.
            f(0x604)
            fields[0x60c]=helper('00464a10')&0xffffffff
            if fields[0x60c]!=0:
                g(0x553fec)
                raw_length=helper('0045dc44:raw_field_fec')&0xffffffff
                offset=g(0x553fe8)&0xffffffff
                indirect=None
                if signed(raw_length)>=16:indirect=helper('0045dc44:raw_field_fe8')&0xffffffff
                request=npc_text_request(fields[0x60c],offset,raw_length,indirect)
                calls.extend(('00404148','0045dca8','00403d84','00505c6c:field610'))
                if observed_text is not None and (text_readable is not None or copied_bytes is not None):
                    raise ValueError('Converted text and raw copy observations are mutually exclusive')
                if observed_text is None:
                    converted=replay_text_copy(request.byte_count,text_readable,copied_bytes,codec=codec)
                    if converted.status!='complete':raise _Unknown('game_text:'+converted.status)
                    observed_text=converted.text
                if type(observed_text) is not str:raise ValueError('Observed converted text required')
                texts[0x610]=observed_text
                phase=3
        elif phase==3:
            if not any_kind(('Sundries','Armor','Weapon')):phase=4
            elif g(0x561f58)==2 and g(0x56fad2)!=0:phase=4
            elif f(0x63c)==0:
                fields.update({0x640:0,0x63c:1});globals[0x561faa]=1
            else:
                fields[0x640]=helper('004edf34')
                if fields[0x640]==0x2a:
                    fields.update({0x640:0,0x63c:0});phase=4;globals[0x561faa]=0
        elif phase==4:
            if not any_kind(('Sundries','Armor','Weapon','Potion','DC Sundries')):phase=5
            elif f(0x650)==0:fields.update({0x654:13,0x650:1})
            elif helper('004fe384')==0:
                fields[0x654]=helper('004eebf4')
                if fields[0x654]==43:fields.update({0x654:13,0x650:0});phase=5
        elif phase in (5,8):
            kinds=('Sundries','Armor','Weapon','Potion','DC Sundries') if phase==5 else ('Inn Hostess',)
            next_phase=6 if phase==5 else 9
            retry_phase=4 if phase==5 else 7
            if not any_kind(kinds):phase=next_phase
            elif f(0x556)==0 and g(0x56fae4)==0:phase=next_phase
            elif phase==8 and helper('0046fe90')!=0:pass
            elif f(0x688)==0:
                fields[0x688]=1
                globals.update({0x5690bc:2,0x5690c0:0,0x5690c1:1 if phase==5 else 0,
                                0x5690c8:g(0x5690cc),0x5690b8:1})
            elif g(0x5690b8)==0:
                if signed(g(0x5690cc))<=47:fields[0x688]=0;phase=retry_phase
                elif g(0x5690d8)==0:
                    fields[0x688]=0;phase=retry_phase;globals[0x5690d8]=1
                else:fields[0x688]=0;phase=next_phase
        elif phase==6:
            if not any_kind(('Sundries','Armor','Weapon','Potion','DC Sundries')):phase=7
            elif g(0x561f58)==2:phase=7
            elif f(0x689)==0:
                start=f(0x18)
                if start==0:count=0
                else:
                    difference=signed(f(0x1c)-start)
                    count=abs(difference)//36 * (-1 if difference<0 else 1)
                fields[0x68c]=count
                if count==0:phase=7
                else:fields.update({0x689:1,0x690:0xffffffff})
            elif helper('004fe384')==0:
                fields[0x690]=helper('004efa84')
                if signed(fields[0x690])>signed(f(0x68c)):
                    fields.update({0x690:0xffffffff,0x689:0});phase=7
        elif phase==7:
            if not any_kind(('Inn Hostess',)):phase=8
            elif helper('004fe384')==0:
                if f(0x6d8)==0:
                    fields[0x6d8]=1
                    globals.update({0x5690e4:1,0x5690e8:0,0x5690ec:0,0x5690f0:0,0x5690e0:1})
                elif g(0x5690e0)==0:fields[0x6d8]=0;phase=8
        elif phase==9:
            if not any_kind(('Royal National Enchanter',)):phase=10
            elif f(0x6c0)==0:fields.update({0x6c4:0,0x6c0:1})
            else:
                fields[0x6c4]=helper('004f035c')
                if fields[0x6c4]==8:fields.update({0x6c4:0,0x6c0:0});phase=10
        if phase==10:
            return NpcRouteResult('complete',NpcRouteFrame(11,fields,globals,texts,tuple(sale_batch),tuple(buy_batch)),True,tuple(calls),text_request=request,
                                  queue_payloads=tuple(nested_packets),cache_writes=tuple(nested_writes))
        return NpcRouteResult('pending',NpcRouteFrame(phase,fields,globals,texts,tuple(sale_batch),tuple(buy_batch)),calls=tuple(calls),text_request=request,
                              queue_payloads=tuple(nested_packets),cache_writes=tuple(nested_writes))
    except _Unknown as exc:
        return NpcRouteResult('needs_observation',NpcRouteFrame(phase,fields,globals,texts,tuple(sale_batch),tuple(buy_batch)),
                              calls=tuple(calls),missing=str(exc),text_request=request,queue_payloads=tuple(nested_packets),cache_writes=tuple(nested_writes))
