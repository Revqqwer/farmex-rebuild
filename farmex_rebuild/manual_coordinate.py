"""Captured normal path of btnGoKordNormalClick004a8478; no executor."""
from dataclasses import dataclass, field, replace
from types import MappingProxyType

ROOT = 'frmMain/MainTab/SheetGenel/GroupBox11/'
BUTTON_PATH = ROOT + 'btnGoKordNormal'
AXIS_FIELDS = (('x', 0x4f8, ROOT + 'txtGoXKord'),
               ('y', 0x4fc, ROOT + 'txtGoYKord'))


@dataclass(frozen=True)
class ManualCoordinateObservation:
    entry_reached: bool = False
    texts: object = field(default_factory=dict)
    float_bits: object = field(default_factory=dict)
    normal_returns: object = field(default_factory=dict)

    def __post_init__(self):
        if type(self.entry_reached) is not bool:
            raise ValueError('Explicit callback entry receipt required')
        texts, bits, normals = map(dict, (self.texts, self.float_bits, self.normal_returns))
        if any(k not in ('x', 'y') or type(v) is not str for k, v in texts.items()):
            raise ValueError('Captured Unicode getter text required')
        if any(k not in ('x', 'y') or type(v) is not int or not 0 <= v < 1 << 32
               for k, v in bits.items()):
            raise ValueError('Captured post-FSTP binary32 bits required')
        if any(type(v) is not bool for v in normals.values()):
            raise ValueError('Separate normal-return receipts required')
        for name, values in (('texts', texts), ('float_bits', bits), ('normal_returns', normals)):
            object.__setattr__(self, name, MappingProxyType(values))


@dataclass(frozen=True)
class ManualCoordinatePlan:
    complete: bool
    status: str
    steps: tuple = ()
    coordinates: tuple = ()
    movement: object = None
    needed: object = None
    missing: str = ''
    native_execution_verified: bool = False
    live_compatibility_verified: bool = False
    exceptional_paths_verified: bool = False


def plan_manual_coordinate(o):
    if not isinstance(o, ManualCoordinateObservation):
        raise ValueError('Typed manual-coordinate observation required')
    steps, coordinates = [], []
    movement = None

    class Missing(Exception):
        def __init__(self, kind, key):
            self.needed = (kind, key)
            super().__init__(kind + ': ' + key)

    def normal(key, helper, args=()):
        steps.append(('call', helper, args, key))
        if o.normal_returns.get(key) is not True:
            raise Missing('normal', key)

    try:
        if not o.entry_reached:
            raise Missing('entry', '004a8478')
        # Compiler exception-frame setup is a separate opaque normal span.
        normal('entry_setup', '00504bec', (0x537f78,))
        for axis, offset, path in AXIS_FIELDS:
            normal(axis + '_construct', '00404a78')
            steps.append(('form_field', offset, path))
            normal(axis + '_get_text', '00506920', (offset,))
            if axis not in o.texts:
                raise Missing('text', axis)
            text = o.texts[axis]
            steps.append(('getter_text', axis, text))
            normal(axis + '_parse', '00506348', (text,))
            if axis not in o.float_bits:
                raise Missing('float_bits', axis)
            bits = o.float_bits[axis]
            steps.append(('FSTP_binary32', axis, bits))
            coordinates.append(bits)
            # X cleanup precedes construction and text acquisition of Y.
            normal(axis + '_cleanup', '00505c48', (2, axis))
        movement = tuple(coordinates)
        # Physical stack order is Y then X; logical helper arguments are X,Y.
        steps.append(('physical_push_y_x', coordinates[1], coordinates[0]))
        normal('movement', '004646b4', movement)
        steps.append(('normal_epilogue', 0x4a8530, 0x4a855c))
        return ManualCoordinatePlan(True, 'normal_path_returned', tuple(steps),
                                    tuple(coordinates), movement)
    except Missing as error:
        return ManualCoordinatePlan(False, 'needs_observation', tuple(steps),
                                    tuple(coordinates), movement, error.needed, str(error))


class ManualCoordinateFrame:
    """One invocation; freeze only consumed captures and accepted returns."""
    def __init__(self):
        self.observation = ManualCoordinateObservation()
        self.final = None

    def advance(self, o):
        if not isinstance(o, ManualCoordinateObservation):
            raise ValueError('Typed manual-coordinate observation required')
        if self.final is not None:
            return self.final
        for _ in range(32):
            p = plan_manual_coordinate(self.observation)
            if p.complete:
                self.final = p
                return p
            kind, key = p.needed
            if kind == 'entry':
                if not o.entry_reached:
                    return p
                self.observation = replace(self.observation, entry_reached=True)
            else:
                attr = {'normal': 'normal_returns', 'text': 'texts',
                        'float_bits': 'float_bits'}[kind]
                supplied = getattr(o, attr)
                if key not in supplied or (kind == 'normal' and supplied[key] is not True):
                    return p
                accepted = {**getattr(self.observation, attr), key: supplied[key]}
                self.observation = replace(self.observation, **{attr: accepted})
        raise ValueError('Own manual-coordinate observation budget exceeded')
