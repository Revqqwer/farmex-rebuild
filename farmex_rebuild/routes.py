"""Offline command interpreter, based on Richard FUN_004f2750.

Special branches delegate to special_routes. Distance is supplied by the adapter:
no unverified game coordinate layout or distance formula is assumed here.
"""
import math
from dataclasses import dataclass, replace
from typing import Optional
from special_routes import (SPECIAL_COMMANDS, SpecialCommand, SpecialRouteSnapshot,
                            SpecialRouteState, special_route_step,source_half_health_threshold)
from npc_route_engine import NpcRouteObservation
from mining_npc_pipeline import replay_mining_npc


def finite_number(value):
    return type(value) in (float, int) and math.isfinite(value)


@dataclass(frozen=True)
class RouteStep:
    command: str
    x: Optional[float] = None
    y: Optional[float] = None
    seconds: Optional[int] = None
    parameter1: Optional[str] = None
    parameter2: Optional[str] = None

    def __post_init__(self):
        if self.command == 'Koordinat':
            if not finite_number(self.x) or not finite_number(self.y) or self.seconds is not None:
                raise ValueError('Koordinat iki sonlu sayı gerektirir')
        elif self.command == 'Bekle':
            if type(self.seconds) is not int or not 0 <= self.seconds <= 2147483:
                raise ValueError('Bekleme saniyesi 0–2147483 arasında tam sayı olmalı')
            if self.x is not None or self.y is not None:
                raise ValueError('Bekle komutu koordinat içeremez')
        elif self.command in SPECIAL_COMMANDS:
            if self.x is not None or self.y is not None or self.seconds is not None:
                raise ValueError('Özel komut metin parametreleri kullanır')
            for name in ('parameter1', 'parameter2'):
                value = getattr(self, name)
                if value is None:
                    object.__setattr__(self, name, '')
                elif type(value) is not str:
                    raise ValueError('Özel rota parametresi metin olmalı')
        else:
            raise ValueError('Henüz uygulanmayan rota komutu: ' + str(self.command))
        if self.command in ('Koordinat', 'Bekle') and (self.parameter1 is not None or self.parameter2 is not None):
            raise ValueError('Koordinat/Bekle metin parametresi içeremez')


@dataclass(frozen=True)
class RouteDecision:
    kind: str
    index: int
    x: Optional[float] = None
    y: Optional[float] = None
    remaining_ms: Optional[int] = None
    calls: tuple = ()
    queue_payloads: tuple = ()
    reason: str = ''
    cache_writes: tuple = ()


class RouteRunner:
    def __init__(self):
        self.stop()

    def stop(self, reason='Durduruldu'):
        self.active = False
        self.steps = ()
        self.index = -1
        self.processing = False
        self.wait_started = None
        self.last_tick = None
        self.reason = reason
        self.special_state = SpecialRouteState()
        self.npc_result = None
        self.npc_profile_result = None

    def start(self, steps):
        self.stop()
        steps = tuple(steps)
        if not steps or any(not isinstance(step, RouteStep) for step in steps):
            raise ValueError('Rota en az bir geçerli komut içermeli')
        self.steps = steps
        self.active = True
        self.reason = ''

    def tick(self, now_ms, distance=None, movement_blocked=False, special_observation=None,
             npc_observation=None,*,npc_profile_configuration=None,npc_runtime_mode=None):
        if npc_profile_configuration is not None and npc_observation is None:raise ValueError('NPC profile binding requires a typed source observation')
        if npc_runtime_mode is not None and npc_profile_configuration is None:raise ValueError('Runtime mode requires an explicit profile binding')
        if type(now_ms) is not int or now_ms < 0:
            raise ValueError('Zaman negatif olmayan tam sayı olmalı')
        if self.last_tick is not None and now_ms < self.last_tick:
            raise ValueError('Simülasyon saati geriye gidemez')
        if distance is not None and (not finite_number(distance) or distance < 0):
            raise ValueError('Mesafe negatif olmayan sonlu sayı olmalı')
        if not self.active:
            return RouteDecision('inactive', self.index)
        self.last_tick = now_ms
        # Original interpreter selects a command on one call, executes later.
        if not self.processing:
            if self.index == len(self.steps) - 1:
                self.active = False
                self.reason = 'Tamamlandı'
                return RouteDecision('finished', self.index)
            self.index += 1
            self.processing = True
            self.wait_started = None
            self.special_state = SpecialRouteState()
            self.npc_result = None
            return RouteDecision('selected', self.index)
        step = self.steps[self.index]
        if step.command == 'Koordinat':
            if movement_blocked:
                return RouteDecision('blocked', self.index)
            if distance is None:
                return RouteDecision('needs_distance', self.index)
            if distance <= 2.0:
                self.processing = False
                return RouteDecision('step_complete', self.index)
            return RouteDecision('move', self.index, step.x, step.y)
        if step.command in SPECIAL_COMMANDS:
            number = None
            randomize = step.command == 'Change Camp' and step.parameter1 == 'Randomize'
            observation = special_observation if special_observation is not None else SpecialRouteSnapshot(now_ms & 0xffffffff)
            if not isinstance(observation, SpecialRouteSnapshot) or observation.now_ms != (now_ms & 0xffffffff):
                raise ValueError('Özel rota gözlemi aynı saat örneğini kullanmalı')
            parse_needed=step.command in ('Gate Open', 'Gate', 'Delos Gate', 'Change Camp') and not randomize
            if step.command in ('Gate Open','Gate','Delos Gate'):
                parse_needed=parse_needed and not self.special_state.started and observation.actor_raw_byte_554020==0
            if step.command=='Change Camp':
                parse_needed=(parse_needed and not self.special_state.started and observation.hp_4611a0 is not None
                    and observation.max_hp_4611c0 is not None and observation.hp_4611a0>=source_half_health_threshold(observation.max_hp_4611c0))
            if parse_needed:
                # Our saved route format uses strict decimal signed32 inputs.
                import re
                text = step.parameter1.strip()
                if not re.fullmatch(r'[+-]?[0-9]+', text):
                    raise ValueError('Özel rota için ondalık tamsayı parametresi gerekli')
                number = int(text)
            command = SpecialCommand(step.command, number, randomize)
            npc_calls=()
            npc_packets=()
            npc_writes=()
            if npc_observation is not None:
                if step.command != 'NPC' or not self.special_state.started:
                    raise ValueError('NPC iç gözlemi yalnız başlamış NPC adımına verilir')
                if not isinstance(npc_observation,NpcRouteObservation):
                    raise ValueError('NPC iç gözlemi türü geçersiz')
                if observation.npc_helper_return_4f11a0 is not None:
                    raise ValueError('NPC iç modeli ile ayrı helper sonucu birlikte verilemez')
                #004f370f copies this route's parameter1 into source field608 each call.
                frame=replace(npc_observation.frame,
                              texts={**npc_observation.frame.texts,0x608:step.parameter1})
                source_observation=replace(npc_observation,frame=frame)
                if npc_profile_configuration is not None:
                    self.npc_profile_result=replay_mining_npc(npc_profile_configuration,source_observation,npc_runtime_mode)
                    self.npc_result=self.npc_profile_result.result
                    phase=self.npc_profile_result.frame.phase
                else:
                    self.npc_profile_result=None
                    self.npc_result=source_observation.step();phase=self.npc_result.frame.phase
                self.special_state=replace(self.special_state,auxiliary_phase=phase)
                npc_calls=self.npc_result.calls
                npc_packets=self.npc_result.queue_payloads
                npc_writes=self.npc_result.cache_writes
                if self.npc_result.status=='needs_observation':
                    return RouteDecision('needs_observation',self.index,calls=npc_calls,
                                         queue_payloads=npc_packets,cache_writes=npc_writes,reason=self.npc_result.missing)
                observation=replace(observation,npc_helper_return_4f11a0=self.npc_result.returned_true)
            result = special_route_step(command, observation, self.special_state)
            self.special_state = result.state
            if result.status == 'step_complete':
                self.processing = False
            return RouteDecision(result.status, self.index, calls=npc_calls+result.calls,
                                 queue_payloads=npc_packets+result.queue_payloads,cache_writes=npc_writes,reason=result.reason)
        if self.wait_started is None:
            self.wait_started = now_ms
            return RouteDecision('waiting', self.index, remaining_ms=step.seconds * 1000)
        remaining = max(0, step.seconds * 1000 - (now_ms - self.wait_started))
        if remaining:
            return RouteDecision('waiting', self.index, remaining_ms=remaining)
        self.processing = False
        self.wait_started = None
        return RouteDecision('step_complete', self.index)


def route_to_data(steps):
    steps = tuple(steps)
    if not steps or any(not isinstance(step, RouteStep) for step in steps):
        raise ValueError('Rota boş veya geçersiz')
    return {'version': 2 if any(s.command in SPECIAL_COMMANDS for s in steps) else 1, 'steps': [
        {'command': s.command, 'x': s.x, 'y': s.y} if s.command == 'Koordinat'
        else {'command': s.command, 'seconds': s.seconds} if s.command == 'Bekle'
        else {'command': s.command, 'parameter1': s.parameter1, 'parameter2': s.parameter2} for s in steps
    ]}


def route_from_data(data):
    if not isinstance(data, dict) or set(data) != {'version', 'steps'}:
        raise ValueError('Geçersiz rota dosyası')
    if type(data['version']) is not int or data['version'] not in (1, 2):
        raise ValueError('Desteklenmeyen rota sürümü')
    if not isinstance(data['steps'], list) or not data['steps']:
        raise ValueError('Rota boş veya geçersiz')
    result = []
    for row in data['steps']:
        if not isinstance(row, dict):
            raise ValueError('Geçersiz rota kaydı')
        if data['version'] == 1 and row.get('command') in SPECIAL_COMMANDS:
            raise ValueError('Özel rota komutları sürüm2 gerektirir')
        expected = {'command', 'x', 'y'} if row.get('command') == 'Koordinat' else {'command', 'seconds'}
        if data['version'] == 2 and row.get('command') in SPECIAL_COMMANDS:
            expected = {'command', 'parameter1', 'parameter2'}
        if set(row) != expected:
            raise ValueError('Rota alanları geçersiz')
        result.append(RouteStep(**row))
    return result
