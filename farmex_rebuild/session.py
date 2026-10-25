"""Independent lifecycle boundary: simulation cannot claim live acceptance."""
from dataclasses import dataclass, field
from enum import Enum
from game_provider import Observation


class Source(Enum):
    SIMULATION = 'simulation'
    LIVE = 'live'


@dataclass(frozen=True)
class Snapshot:
    session_id: str
    source: Source
    timestamp_ms: int
    fields: dict = field(default_factory=dict)
    verified: bool = False

    def __post_init__(self):
        if not isinstance(self.session_id, str) or not self.session_id or not isinstance(self.source, Source):
            raise ValueError('Geçersiz oturum kaynağı')
        if type(self.timestamp_ms) is not int or self.timestamp_ms < 0 or not isinstance(self.fields, dict):
            raise ValueError('Geçersiz gözlem')
        if type(self.verified) is not bool:
            raise ValueError('Geçersiz doğrulama durumu')


class Session:
    def __init__(self, session_id, source=Source.SIMULATION, stale_ms=1000):
        if not isinstance(session_id, str) or not session_id or not isinstance(source, Source):
            raise ValueError('Oturum kimliği/kaynağı geçersiz')
        if type(stale_ms) is not int or stale_ms <= 0:
            raise ValueError('Gözlem süresi pozitif tam sayı olmalı')
        self.session_id, self.source, self.stale_ms = session_id, source, stale_ms
        self.snapshot = None
        self.active = False
        self.target_id = None
        self.pending = {}
        self.next_id = 1

    def accept_snapshot(self, snapshot):
        if not isinstance(snapshot, Snapshot) or snapshot.session_id != self.session_id or snapshot.source != self.source:
            raise ValueError('Gözlem oturumla eşleşmiyor')
        if self.snapshot is not None and snapshot.timestamp_ms < self.snapshot.timestamp_ms:
            raise ValueError('Gözlem saati geriye gidemez')
        self.snapshot = snapshot

    def start(self, now_ms, required_fields=()):
        if type(now_ms) is not int or now_ms < 0:
            raise ValueError('Geçersiz saat')
        if self.snapshot is None or not 0 <= now_ms - self.snapshot.timestamp_ms <= self.stale_ms:
            return 'needs_fresh_snapshot'
        if any(self.snapshot.fields.get(key) is None for key in required_fields):
            return 'needs_fields'
        if self.source == Source.LIVE and not self.snapshot.verified:
            return 'needs_verification'
        self.active = True
        return 'started'

    def stop(self):
        self.active = False
        self.target_id = None
        self.pending.clear()

    def disconnect(self):
        self.stop()
        self.snapshot = None

    def issue(self, intent, now_ms):
        if not self.active:
            return {'status': 'inactive'}
        if self.snapshot is None or not 0 <= now_ms - self.snapshot.timestamp_ms <= self.stale_ms:
            self.stop()
            return {'status': 'stale'}
        if self.source == Source.LIVE:
            return {'status': 'unavailable', 'reason': 'Live transport is not bound'}
        key = self.next_id
        self.next_id += 1
        self.pending[key] = intent
        return {'status': 'simulated', 'action_id': key, 'acknowledged': False}


def observation_snapshot(observation, session_id):
    if not isinstance(observation, Observation) or observation.status not in ('candidate', 'candidate_unverified', 'verified'):
        return None
    return Snapshot(session_id, Source.LIVE, observation.timestamp_ms, dict(observation.fields),
                    observation.independently_verified)
