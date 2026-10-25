"""Richard004620bc raw DWORD-to-ANSI mapping, taken from disk literals."""
_GROUPS=((b'Moradon',(21,22,23)),(b'Luferson',(1,3,5,6)),(b'EMC',(2,4,7,8)),
         (b'Karus Eslant',(11,13,14)),(b'Human Eslant',(12,15,16)),
         (b'Delos Base',(30,)),(b'Desp. Abbys',(32,)),(b'Hell Abbys',(33,)),
         (b'Ronark Land',(71,)),(b'Ardream',(72,)))
_NAMES={number:name for name,numbers in _GROUPS for number in numbers}
DEFAULT_ANSI=b'Tan\xfdml\xfd De\xf0il'


def zone_name_ansi(raw_zone_id):
    if type(raw_zone_id) is not int or not 0<=raw_zone_id<=0xffffffff:
        raise ValueError('Observed zone DWORD required')
    return _NAMES.get(raw_zone_id,DEFAULT_ANSI)
