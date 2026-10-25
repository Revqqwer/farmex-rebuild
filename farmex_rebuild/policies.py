"""Pure policies; no game reads, actions, messages, or protocol numbers."""
from dataclasses import dataclass


def weight_percent(current, maximum):
    """Richard 00460624; normal nonnegative domain, no x86 overflow emulation."""
    if type(current) is not int or type(maximum) is not int or current < 0:
        raise ValueError('Ağırlık tam sayı olmalı ve mevcut değer negatif olmamalı')
    return 0 if maximum < 1 else current * 100 // maximum


def weight_supply_due(enabled, current, maximum, threshold):
    # Richard 004ed384 weight branch: skip only if percentage < threshold.
    if type(enabled) is not bool or type(threshold) is not int or not 0 <= threshold <= 100:
        raise ValueError('Geçersiz ağırlık politikası')
    return enabled and weight_percent(current, maximum) >= threshold


def stock_supply_due(item_name, quantity):
    """004f38dc: quantity criterion only; inventory identity/filtering separate."""
    if not isinstance(item_name, str) or type(quantity) is not int or quantity < 0:
        raise ValueError('Geçersiz stok')
    return quantity < (11 if item_name == 'Arrow' else 3)


CHANNELS = ('All Chat', 'Party', 'Clan', 'Shout', 'Merchant', 'Noah Knight')


@dataclass(frozen=True)
class MessageRow:
    channel: str
    text: str
    wait_seconds: int

    def __post_init__(self):
        if self.channel not in CHANNELS or not isinstance(self.text, str) or not self.text.strip():
            raise ValueError('Kanal ve mesaj geçerli olmalı')
        if type(self.wait_seconds) is not int or not 0 <= self.wait_seconds <= 2147483:
            raise ValueError('Bekleme saniyesi geçersiz')


class MessageSequence:
    """0045cce8 sequence/timer; 0046f1b8 merchant consumer.

    A returned row means local intent only. No message is transmitted.
    now_ms is an injected monotonic clock in a single clock domain.
    Initial timestamp zero follows 0045cbac; later intervals use decision time.
    """
    def __init__(self):
        self.stop()

    def start(self, rows):
        self.stop()
        rows = tuple(rows)
        if not rows or any(not isinstance(row, MessageRow) for row in rows):
            raise ValueError('En az bir geçerli mesaj satırı gerekli')
        self.rows = rows
        self.active = True

    def stop(self):
        self.active = False
        self.rows = ()
        self.index = 0
        self.last_action = 0
        self.last_tick = None

    def tick(self, now_ms, mode):
        if type(now_ms) is not int or now_ms < 0:
            raise ValueError('Geçersiz saat')
        if self.last_tick is not None and now_ms < self.last_tick:
            raise ValueError('Saat geriye gidemez')
        self.last_tick = now_ms
        if not self.active or mode != 4:
            return None
        row = self.rows[self.index]
        if now_ms - self.last_action < row.wait_seconds * 1000:
            return None
        self.last_action = now_ms
        self.index = (self.index + 1) % len(self.rows)
        return row
