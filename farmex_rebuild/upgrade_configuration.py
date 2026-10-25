"""Upgrade UI snapshot bridge for source 4f7604/4f7adc (current relocated bodies).

Decimal parsing is a local policy, not a complete Delphi parser or fallback
emulation. Captured Unicode combo text is kept separate from its ItemIndex,
ANSI conversion and runtime inventory scroll index. No game I/O occurs here.
"""
import re
from dataclasses import dataclass
from collections.abc import Mapping
from types import MappingProxyType
from operation_engine import UpgradeRow, UpgradeRunner

BASE = 'frmMain/MainTab/SheetUpgrade/'
GROUP = BASE+'GroupBox44/'
SCROLL_PATH = GROUP+'cmbUpgradeScroll'
WAIT_PATH = GROUP+'txtUpgradeWait'
ANVIL_PATH = GROUP+'txtUpgradeAnvilID'
LIST_PATH = BASE+'grpUpgradeItems/LwUpgradeItems'
UPGRADE_PANEL_INPUTS = (SCROLL_PATH, WAIT_PATH, ANVIL_PATH, LIST_PATH)


def _decimal(text, bits, label):
    if type(text) is not str or not re.fullmatch(r'[+-]?[0-9]+', text.strip()):
        raise ValueError('Decimal upgrade text required: '+label)
    value = int(text.strip())
    if not -(1 << (bits-1)) <= value < 1 << (bits-1):
        raise ValueError('Upgrade value outside signed%d parsing policy: '%bits+label)
    return value & 0xffffffff


@dataclass(frozen=True)
class UpgradePanelConfiguration:
    fields: Mapping
    rows: tuple
    scroll_text: object
    missing: tuple
    ansi_conversion_verified: bool = False
    independently_verified: bool = False
    raw_start_rows: tuple = ()
    rows_deferred: bool = False


def compile_upgrade_panel(values, lists, *, scroll_text=None, defer_rows=False):
    if not isinstance(values, Mapping) or not isinstance(lists, Mapping):
        raise ValueError('Upgrade panel mappings required')
    if scroll_text is not None and type(scroll_text) is not str:
        raise ValueError('Explicit Unicode combo Text required')
    if type(defer_rows) is not bool:
        raise ValueError('Explicit deferred row policy required')
    # The helper returns signed64 in EDX:EAX; the caller stores EAX only.
    fields = {8: _decimal(values.get(ANVIL_PATH), 64, ANVIL_PATH),
              4: _decimal(values.get(WAIT_PATH), 64, WAIT_PATH)}
    entries = lists.get(LIST_PATH)
    if type(entries) is not list:
        raise ValueError('Upgrade ListView rows required')
    selected = []
    captured = []
    for row in entries:
        if not isinstance(row, Mapping) or type(row.get('checked')) is not bool:
            raise ValueError('Typed upgrade checked row required')
        captured.append(MappingProxyType(dict(row)))
        # Source does not convert the captions of unchecked rows.
        if row['checked'] and not defer_rows:
            selected.append(UpgradeRow(_decimal(row.get('caption'), 32, LIST_PATH), True))
    missing = (SCROLL_PATH+': GetText',) if scroll_text is None else ()
    return UpgradePanelConfiguration(MappingProxyType(fields), tuple(selected), scroll_text, missing,
                                     raw_start_rows=tuple(captured), rows_deferred=defer_rows)


def upgrade_runner_from_panel(configuration):
    if not isinstance(configuration, UpgradePanelConfiguration):
        raise ValueError('Compiled upgrade configuration required')
    if configuration.missing:
        raise ValueError('Upgrade combo Text unavailable')
    interval = configuration.fields[4]
    return UpgradeRunner(interval_ms=interval, anvil_id=configuration.fields[8], source_clock=True)


def selected_upgrade_scroll_text(values, catalog):
    """Only resolve an actual local selection; -1 needs separately observed Text.

    This is a UI helper. It does not equate a combo index with inventory slots.
    """
    index = values.get(SCROLL_PATH)
    if type(index) is not int:
        raise ValueError('Upgrade combo ItemIndex required')
    nodes = [n for n in catalog if n['path'] == SCROLL_PATH]
    if len(nodes) != 1:
        raise ValueError('Upgrade combo catalog identity required')
    items = nodes[0]['properties'].get('Items.Strings', [])
    if index == -1:
        return None
    if not 0 <= index < len(items):
        raise ValueError('Upgrade combo index outside local catalog')
    return items[index]
