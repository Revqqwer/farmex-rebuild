"""Five Genie setting getters at004580ac..00458143; no following native effects."""
from protection_settings import ProtectionSettingsFrame,ProtectionSettingsObservation,plan_protection_settings

OPS=(('flag',0xbd0,0xb8),('flag',0xd74,0xb9),('flag',0xbd4,0xba),
     ('flag',0xbe4,0xbb),('flag',0xbe8,0xbc))
NAMES={0xbd0:'chGenieWithBot',0xd74:'chGenieStopWithBot',0xbd4:'chAutoGenieCoupon',
       0xbe4:'chNoRemainGenieTimeTown',0xbe8:'chNoRemainGenieTimeAlarm'}
GENIE_SETTING_FIELDS=tuple((slot,'frmMain/MainTab/SheetKontrol/grpGenie/'+NAMES[slot]) for _,slot,_ in OPS)
GENIE_SETTING_INPUTS=tuple(path for _,path in GENIE_SETTING_FIELDS)
GenieSettingsObservation=ProtectionSettingsObservation


def plan_genie_settings(o,*,context=0x562194,_child=None):
    return plan_protection_settings(o,context=context,_child=_child,_ops=OPS,
                                   _entry='004580ac',_exit=0x458143,_prologue=False)


class GenieSettingsFrame(ProtectionSettingsFrame):
    _planner=staticmethod(plan_genie_settings)
    def __init__(self,*,context=0x562194):super().__init__(context=context)
