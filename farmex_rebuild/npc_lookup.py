"""Richard00465960 selector from observed iterator rows, not a process scan.

Distance is the signed DWORD result of source __ftol. Names are ANSI bytes
after the source copy/C-string conversion. Iterator order/completion is explicit.
"""
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class NpcCandidate:
    distance_integer: Optional[int] = None
    object_id: Optional[int] = None
    ansi_name: Optional[bytes] = None

    def __post_init__(self):
        if self.distance_integer is not None and (type(self.distance_integer) is not int
                or not -0x80000000 <= self.distance_integer <= 0x7fffffff):
            raise ValueError('Observed signed __ftol result required')
        if self.object_id is not None and (type(self.object_id) is not int
                or not 0 <= self.object_id <= 0xffffffff):
            raise ValueError('Observed DWORD NPC ID required')
        if self.ansi_name is not None and type(self.ansi_name) is not bytes:
            raise ValueError('Observed ANSI name bytes required')


@dataclass(frozen=True)
class NpcLookupResult:
    status: str
    candidate_id: int = 0
    distance_integer: int = 80
    visited: int = 0
    missing: str = ''


def select_npc(candidates, filter_bytes, *, traversal_complete=None):
    rows=tuple(candidates)
    if type(filter_bytes) is not bytes or b'\0' in filter_bytes:
        raise ValueError('Native string filter bytes without embedded NUL required')
    if traversal_complete is not None and type(traversal_complete) is not bool:
        raise ValueError('Observed iterator completion required')
    if any(not isinstance(row,NpcCandidate) for row in rows):
        raise ValueError('Typed iterator rows required')
    selected,best,visited=0,80,0
    for row in rows:
        visited+=1
        if row.distance_integer is None:
            return NpcLookupResult('needs_observation',selected,best,visited,'distance __ftol')
        if row.distance_integer>=best:continue
        # Source reads ID before constructing/searching the name.
        if row.object_id is None:
            return NpcLookupResult('needs_observation',selected,best,visited,'NPC ID')
        if row.ansi_name is None:
            return NpcLookupResult('needs_observation',selected,best,visited,'ANSI name')
        name=row.ansi_name.split(b'\0',1)[0]
        if filter_bytes in name:
            selected,best=row.object_id,row.distance_integer
    if traversal_complete is not True:
        return NpcLookupResult('needs_observation',selected,best,visited,'native iterator completion')
    return NpcLookupResult('complete',selected,best,visited)
