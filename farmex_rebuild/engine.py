"""Independent rules derived from the recorded Richard static analysis."""
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class PotionRule:
    enabled: bool = False
    threshold: int = 50
    selected_id: Optional[int] = None
    fallback_id: Optional[int] = None

    def __post_init__(self):
        if type(self.enabled) is not bool:
            raise ValueError('enabled must be boolean')
        if type(self.threshold) is not int or not 0 <= self.threshold <= 100:
            raise ValueError('threshold must be an integer from 0 to 100')
        for value in (self.selected_id, self.fallback_id):
            if value is not None and (type(value) is not int or value <= 0):
                raise ValueError('item identifiers must be positive integers')


@dataclass(frozen=True)
class Vitals:
    hp: int
    hp_max: int
    mp: int
    mp_max: int

    def __post_init__(self):
        for current, maximum in ((self.hp, self.hp_max), (self.mp, self.mp_max)):
            if type(current) is not int or type(maximum) is not int:
                raise ValueError('vitals must be integers')
            if maximum <= 0 or not 0 <= current <= maximum:
                raise ValueError('invalid vitals')


@dataclass(frozen=True)
class PotionDecision:
    resource: str
    item_id: int


def choose_potion(vitals, mp_rule, hp_rule, available_items):
    """MP precedes HP; local decision only, never a server acknowledgement.

    Evidence: Richard FUN_0040e7ac, scheduler FUN_0040f204.
    Adapter inventory and send-failure behaviour remain to be validated live.
    """
    for resource, current, maximum, rule in (
        ('MP', vitals.mp, vitals.mp_max, mp_rule),
        ('HP', vitals.hp, vitals.hp_max, hp_rule),
    ):
        if rule.enabled and current <= maximum * rule.threshold // 100:
            for item_id in (rule.selected_id, rule.fallback_id):
                if item_id is not None and item_id in available_items:
                    return PotionDecision(resource, item_id)
    return None


def next_check_ms(local_action):
    return 3000 if local_action else 50
