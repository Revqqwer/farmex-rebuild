"""Own coordinate click continuation over explicit captured axis data."""
from dataclasses import dataclass
from current_coordinates import CurrentAxisObservation,CurrentCoordinatesFrame

BUTTON_PATH='frmMain/RotaPanel/grpRouteAddCommand/btnRouteAddKord'
OWN_TIMER_PERIOD_MS=100


@dataclass(frozen=True)
class CoordinateClickInput:
    x:object=None
    y:object=None
    def __post_init__(self):
        for value in (self.x,self.y):
            if value is not None and not isinstance(value,CurrentAxisObservation):raise ValueError('Typed current-axis capture required')


@dataclass(frozen=True)
class CoordinateCaptureContext:
    invocation:int
    generation:int
    axis:object
    needed:object


@dataclass(frozen=True)
class CoordinateClickResult:
    complete:bool
    done:bool
    status:str
    row:object=None
    coordinates:object=None
    error:object=None
    native_execution_verified:bool=False
    live_compatibility_verified:bool=False


class CoordinateClickFrame:
    """Add/caption before X/Y; both axes before first/second subitem.

    Sink token is opaque. Optional validate(token) rejects invalidated own rows.
    Bad capture stays pending; sink failure terminates with its completed prefix.
    No game acquisition or native VCL/string cleanup is executed here.
    """
    def __init__(self,sink):
        self.sink=sink;self.row=None;self.axes=CurrentCoordinatesFrame();self.coordinates=None
        self.phase='add';self.busy=False;self.result=CoordinateClickResult(False,False,'queued')
    def _result(self,status,complete=False,done=False,error=None):
        self.result=CoordinateClickResult(complete,done,status,self.row,self.coordinates,error)
        return self.result
    def hold(self,error=None):
        if self.result.done:return self.result
        return self._result('needs_coordinate_capture',error=error)
    def cancel(self,reason):
        if not self.result.done:self._result('cancelled',done=True,error=reason)
        return self.result
    def advance(self,capture=None):
        if self.result.done or self.busy:return self.result
        self.busy=True
        try:
            if self.phase=='add':self.row=self.sink.add_row();self.phase='caption'
            if self.result.done:return self.result
            if self.phase=='caption':self.sink.set_caption(self.row,'Koordinat');self.phase='coordinates'
            if self.result.done:return self.result
            validate=getattr(self.sink,'validate',None)
            if callable(validate):validate(self.row)
            if self.phase=='coordinates':
                if capture is not None and not isinstance(capture,CoordinateClickInput):return self.hold('Typed coordinate click input required')
                capture=CoordinateClickInput() if capture is None else capture
                try:self.coordinates=self.axes.advance(capture.x,capture.y)
                except ValueError as error:return self.hold(str(error))
                if not self.coordinates.complete:return self.hold()
                self.phase='sub1'
            if self.phase=='sub1':self.sink.add_subitem(self.row,self.coordinates.parameters[0]);self.phase='sub2'
            if self.result.done:return self.result
            if self.phase=='sub2':self.sink.add_subitem(self.row,self.coordinates.parameters[1]);self.phase='returned'
            return self._result('row_completed',True,True)
        except (OSError,ValueError,IndexError) as error:return self._result('row_incomplete',done=True,error=str(error))
        finally:self.busy=False
