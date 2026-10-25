"""Reached common-settings Pet prefix; owned state only, no pet/game action."""
from protection_settings import (ProtectionSettingsFrame,ProtectionSettingsObservation,
                                 plan_protection_settings)

ROOT='frmMain/MainTab/SheetBot/GroupBox18/'
PET_SETTING_FIELDS=((0xf18,ROOT+'chAutoPetCall'),(0xf28,ROOT+'rdPetAtackMode'),
 (0xf24,ROOT+'rdPetGuardMode'),(0xf20,ROOT+'rdPetLootMode'),
 (0xf14,ROOT+'chPetAutoFood'),(0xf1c,ROOT+'txtPetAutoFood'))
PET_SETTING_INPUTS=tuple(path for _,path in PET_SETTING_FIELDS)
OPS=(('flag',0xf18,0x1a8),('enum',((0xf28,1),(0xf24,2),(0xf20,3)),0x1ac),
     ('flag',0xf14,0x1b0),('number',0xf1c,0x1b4,10))
PetSettingsObservation=ProtectionSettingsObservation

def plan_pet_settings(o,*,context=0x561f34,_child=None):
    return plan_protection_settings(o,context=context,_child=_child,_ops=OPS,
                                   _entry='0040a3ac',_exit=0x40a4b0,_prologue=False)

class PetSettingsFrame(ProtectionSettingsFrame):
    _planner=staticmethod(plan_pet_settings)
    def __init__(self,*,context=0x561f34):super().__init__(context=context)
