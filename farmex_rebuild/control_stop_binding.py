"""Completed own settings snapshot -> existing zone TP / client Town plans."""
from dataclasses import replace
from control_settings import control_configuration_from_settings
from incoming_tp_dispatch import IncomingTPDispatchFrame
from teleport_protection import TPObservation
from town_request import TownRequestDispatchFrame
from jail_protection import JailObservation

class ControlStopSnapshotFrame:
 """Explicit stable own fixture; native fresh reads can differ after production."""
 def __init__(self,kind,packet,settings,*,context=0x562194):
  if kind not in ('zone','town'):raise ValueError('Known control stop branch required')
  self.configuration=control_configuration_from_settings(settings,context=context)
  self.kind=kind
  self.key='area_change_stop_byte' if kind=='zone' else 'town_request_stop_byte'
  self.value=self.configuration.fields[0xbd if kind=='zone' else 0xbe]
  self.dispatch=IncomingTPDispatchFrame(packet) if kind=='zone' else TownRequestDispatchFrame(packet)
 def advance(self,o,*,dispatcher_setup_returned=None):
  expected=TPObservation if self.kind=='zone' else JailObservation
  if not isinstance(o,expected):raise ValueError('Typed selected control-stop observations required')
  # Let source control flow reach the fresh flag read before binding it. Earlier
  # returns and cached reads never consume or reject an unrelated later capture.
  values={k:v for k,v in o.values.items() if k!=self.key}
  incoming=replace(o,values=values)
  p=self.dispatch.advance(incoming,dispatcher_setup_returned=dispatcher_setup_returned)
  if p.child is not None and not p.child.complete and p.child.needed==('value',self.key):
   if self.key in o.values and o.values[self.key]!=self.value:
    raise ValueError('Reached control flag conflicts with explicit own settings snapshot')
   p=self.dispatch.advance(replace(incoming,values={**values,self.key:self.value}),
                           dispatcher_setup_returned=dispatcher_setup_returned)
  return p
