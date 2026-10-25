"""Owned button invocation over actual panel text and explicit helper captures."""
from dataclasses import dataclass, replace
from types import MappingProxyType
from manual_coordinate import ManualCoordinateFrame, ManualCoordinateObservation, AXIS_FIELDS

OWN_TIMER_PERIOD_MS = 100


@dataclass(frozen=True)
class ManualCoordinateContext:
    invocation: int
    generation: int
    needed: object
    texts: object

    def __post_init__(self):
        object.__setattr__(self, 'texts', MappingProxyType(dict(self.texts)))


@dataclass(frozen=True)
class ManualCoordinateCapture:
    invocation: int
    generation: int
    observation: ManualCoordinateObservation


class OwnedManualCoordinate:
    """Single pending click; source synchronous execution is not emulated.

    Text is read only when its getter output is demanded. Callback setup,
    getters, parses, cleanup and movement remain explicit captured receipts.
    A provider gets one call per tick; profile/provider changes cancel the old
    invocation. Generation and invocation tokens are local freshness policy.
    """
    def __init__(self, reader):
        self.reader = reader
        self.generation = 0
        self.invocation = 0
        self.frame = None
        self.result = None
        self.pending = False
        self.error = None
        self.busy = False

    def reset(self):
        self.generation += 1
        self.frame = self.result = None
        self.pending = False
        self.error = None

    def start(self):
        if self.pending or self.busy:
            return self.result
        self.invocation += 1
        self.frame = ManualCoordinateFrame()
        self.pending = True
        self.error = None
        self.result = self.frame.advance(ManualCoordinateObservation(entry_reached=True))
        return self.result

    def _read_texts(self):
        while not self.result.complete and self.result.needed[0] == 'text':
            axis = self.result.needed[1]
            path = next(path for name, _, path in AXIS_FIELDS if name == axis)
            value = self.reader()[path]
            if type(value) is not str:
                raise ValueError('Actual coordinate panel Text must be Unicode')
            self.result = self.frame.advance(ManualCoordinateObservation(texts={axis: value}))

    def tick(self, provider):
        if not self.pending or self.busy:
            return self.result
        frame, generation, invocation = self.frame, self.generation, self.invocation
        self.busy = True
        try:
            self._read_texts()
            context = ManualCoordinateContext(invocation, generation, self.result.needed,
                                               frame.observation.texts)
            capture = provider(context)
            if generation != self.generation or frame is not self.frame:
                return self.result
            if capture is None:
                return self.result
            if not isinstance(capture, ManualCoordinateCapture):
                raise ValueError('Typed coordinate capture required')
            if (capture.invocation, capture.generation) != (invocation, generation):
                raise ValueError('Stale coordinate capture token')
            o = capture.observation
            if not isinstance(o, ManualCoordinateObservation):
                raise ValueError('Typed coordinate helper observation required')
            # Provider may attest known text for parse results, never replace
            # panel getter outputs or supply a future axis before acquisition.
            for axis, text in o.texts.items():
                if axis not in frame.observation.texts or frame.observation.texts[axis] != text:
                    raise ValueError('Coordinate capture text differs from acquired panel Text')
            for axis in o.float_bits:
                if axis not in o.texts:
                    raise ValueError('Coordinate float capture must bind its acquired Text')
            self.result = frame.advance(replace(o, entry_reached=False, texts={}))
            self._read_texts()
            self.pending = not self.result.complete
            self.error = None
            return self.result
        except (ValueError, OSError, KeyError) as error:
            if generation == self.generation and frame is self.frame:
                self.error = str(error)
            return self.result
        finally:
            self.busy = False
