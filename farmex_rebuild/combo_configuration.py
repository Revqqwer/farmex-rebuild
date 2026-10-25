"""0040a39c shared config BYTE producers; local panel compilation, no game IO.

561f34+dd=562011 W, +de=562012 S, +c8=561ffc run-to-target,
+98=561fcc R Attack.
Both W/S checkboxes are independent. Source click refresh is gated by561f55;
this compiler reads the local profile, not the original running global state.
"""
from dataclasses import dataclass
from collections.abc import Mapping

COMBO_PANEL_INPUTS=tuple('frmMain/MainTab/SheetBot/GroupBox7/'+name for name in
                       ('chUseWCombo','chUseSCombo','chrunmob','chratak'))

@dataclass(frozen=True)
class ComboPanelConfiguration:
    w_combo: bool
    s_combo: bool
    run_to_target: bool
    r_attack: bool = False

    def __post_init__(self):
        if any(type(v) is not bool for v in (self.w_combo,self.s_combo,self.run_to_target,self.r_attack)):
            raise ValueError('Boolean combo panel fields required')

    @property
    def w_byte(self):return int(self.w_combo)

    @property
    def s_byte(self):return int(self.s_combo)

    @property
    def run_byte(self):return int(self.run_to_target)

def compile_combo_panel(values):
    if not isinstance(values,Mapping):raise ValueError('Panel mapping required')
    if any(path not in values for path in COMBO_PANEL_INPUTS):raise ValueError('Missing combo panel field')
    return ComboPanelConfiguration(*(values[path] for path in COMBO_PANEL_INPUTS))
