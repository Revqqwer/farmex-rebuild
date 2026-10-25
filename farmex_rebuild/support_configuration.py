"""Bridge confirmed class object offsets into existing local support settings.

This does not provide party objects, lookup IDs, game stats, timers or actions.
Settings retain the existing independent model's validation policy.
"""
from class_configuration import ClassConfiguration
from combat_engine import PriestSettings,MinorSettings,MageSettings,KurianSettings

def support_settings_from_config(config):
    if not isinstance(config,ClassConfiguration):raise ValueError('Compiled class configuration required')
    def value(mapping,offset):
        if offset not in mapping:raise ValueError('Missing source field +%x'%offset)
        return mapping[offset]
    flag=lambda o:value(config.flags,o)
    parameter=lambda o:value(config.parameters,o)
    if config.job=='priest':
        return PriestSettings(flag(0xc0),parameter(0xc4),parameter(0xc8),
                              flag(0xcc),parameter(0xd0),parameter(0xd4),flag(0x12d))
    if config.job=='rogue':return MinorSettings(flag(0),parameter(4),parameter(8))
    if config.job=='mage':return MageSettings(flag(3),parameter(4),flag(8),value(config.texts,12))
    if config.job=='kurian':return KurianSettings(flag(0xdb),parameter(0xdc))
    raise ValueError('No source support-settings bridge for this class')
