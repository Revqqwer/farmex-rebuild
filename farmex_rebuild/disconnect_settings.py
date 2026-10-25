"""00457d02..004580ac DC settings span within004576ec; inert projections only."""
from protection_settings import (ProtectionSettingsFrame,ProtectionSettingsObservation,
                                 plan_protection_settings)

# Source order. constant9a is unconditional and has no checkbox read.
OPS=(('flag',0x828,0x8a),('flag',0x82c,0x8b),('flag',0x838,0x8c),
     ('index',0x83c,0x90),('number',0x834,0x94,30),('flag',0x840,0x98),
     ('flag',0x844,0x99),('constant',None,0x9a,1),('string',0x84c,0x9c),
     ('flag',0x850,0xa0),('string',0x854,0xa4),('index',0xeb8,0xa8),
     ('flag',0x858,0xac),('string',0x85c,0xb0),('string',0x860,0xb4))

FIELD_NAMES={0x828:'chDCControl',0x82c:'dcDCControlAlarm',0x838:'chDCControlProc',
 0x83c:'cmbDCControlProcIndex',0x834:'txtDCAutoLoginWaitSeconds',0x840:'chDCControlStartBot',
 0x844:'chRelogAfterReturnSlot',0x84c:'cmbRelogAfterReturnRouteName',0x850:'chRelogAfterSendChat',
 0x854:'txtRelogAfterChatText',0xeb8:'cmbRelogAfterSendChat',0x858:'chRelogAfterSendPM',
 0x85c:'txtRelogAfterPMNick',0x860:'txtRelogAfterPMText'}
DC_SETTING_FIELDS=tuple((op[1],'frmMain/MainTab/SheetKontrol/GroupBox32/'+FIELD_NAMES[op[1]])
                       for op in OPS if op[0]!='constant')
DC_SETTING_INPUTS=tuple(path for _,path in DC_SETTING_FIELDS)

# Same typed scalar/text/ANSI/RTL observation structure; no actual config values.
DisconnectSettingsObservation=ProtectionSettingsObservation


def plan_disconnect_settings(o,*,context=0x562194,_child=None):
    return plan_protection_settings(o,context=context,_child=_child,_ops=OPS,
                                   _entry='00457d02',_exit=0x4580ac,_prologue=False)


class DisconnectSettingsFrame(ProtectionSettingsFrame):
    _planner=staticmethod(plan_disconnect_settings)
    def __init__(self,*,context=0x562194):super().__init__(context=context)
