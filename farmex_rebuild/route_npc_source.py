"""Own source-capture composition for the actual NPC button; no game IO."""
from dataclasses import dataclass,replace
from route_npc_click import NpcClickFrame,NpcClickInput
from target_id_frames import TargetIdFrame
from route_npc_name import RouteNpcNameFrame
from npc_actor_lookup import NpcLookupObservation,NpcLookupFrame
from npc_unicode import NpcUnicodeObservation,NpcUnicodeFrame


@dataclass(frozen=True)
class NpcSourceInput:
    target_gate:object=None
    target_lookup:object=None
    actor:object=None
    name:object=None
    target_classify:object=None
    trade_text:object=None


class NpcSourceFrame:
    """Per invocation lower target/name children, or legacy ready captures.

    Lower mode cannot bypass pending child receipts with ready-made fields.
    The only ready-capture exception is the own UI's reached dialog return.
    Dynamic actor lookup and late Unicode conversion optionally use typed
    lower observations; neither executes native helpers or acquires game data.
    """
    def __init__(self,sink):
        self.core=NpcClickFrame(sink);self.result=self.core.result;self.mode=None;self.busy=False
        self.targets={name:TargetIdFrame() for name in ('target_gate','target_lookup','target_classify')}
        self.name=None;self.lookup=None;self.unicode=None
    @property
    def phase(self):return self.core.phase
    def cancel(self,reason):self.result=self.core.cancel(reason);return self.result
    def hold(self,error):
        if self.result.done:return self.result
        needed=self.result.needed;self.result=replace(self.core.hold(error),needed=needed)
        return self.result
    def _pending(self,phase,plan):
        self.result=replace(self.core.result,needed=(phase,plan.needed))
        return self.result
    def advance(self,incoming=None):
        if self.result.done or self.busy:return self.result
        self.busy=True
        try:
            if isinstance(incoming,NpcClickInput):
                dialog_only=self.phase=='dialog_text' and all(
                    value is None for name,value in vars(incoming).items() if name!='dialog_text')
                if self.mode=='source' and not dialog_only:
                    return self.hold('Ready-made input cannot bypass pending source captures')
                if self.mode is None:self.mode='ready'
                self.result=self.core.advance(incoming);return self.result
            if incoming is not None and not isinstance(incoming,NpcSourceInput):
                return self.hold('Typed NPC source input required')
            if isinstance(incoming,NpcSourceInput):
                if self.mode=='ready':return self.hold('Capture mode cannot change within an invocation')
                self.mode='source'
            if self.mode!='source':self.result=self.core.advance();return self.result
            incoming=NpcSourceInput() if incoming is None else incoming
            for _ in range(12):
                result=self.core.advance();self.result=result
                if result.done:return result
                phase=self.phase
                if phase in self.targets:
                    p=self.targets[phase].advance(getattr(incoming,phase))
                    if not p.complete:return self._pending(phase,p)
                    capture=NpcClickInput(**{phase:p.capture})
                elif phase=='name_bytes':
                    if self.name is None:self.name=RouteNpcNameFrame(self.core.cache['actor']['value'])
                    p=self.name.advance(incoming.name)
                    if not p.complete:return self._pending(phase,p)
                    capture=NpcClickInput(name_bytes=p.capture)
                elif phase=='actor':
                    value=incoming.actor
                    if isinstance(value,NpcLookupObservation) or self.lookup is not None:
                        if value is not None and not isinstance(value,NpcLookupObservation):
                            return self.hold('Ready actor cannot bypass pending lookup observations')
                        if self.lookup is None:self.lookup=NpcLookupFrame(self.core.cache['target_lookup']['value'])
                        p=self.lookup.advance(value)
                        if not p.complete:return self._pending(phase,p)
                        capture=NpcClickInput(actor=p.capture)
                    else:
                        if value is None:return result
                        capture=NpcClickInput(actor=value)
                elif phase=='trade_text':
                    value=getattr(incoming,phase)
                    if isinstance(value,NpcUnicodeObservation) or self.unicode is not None:
                        if value is not None and not isinstance(value,NpcUnicodeObservation):
                            return self.hold('Ready text cannot bypass pending Unicode observations')
                        if self.unicode is None:self.unicode=NpcUnicodeFrame(self.core.cache['name_bytes']['value'])
                        p=self.unicode.advance(value)
                        if not p.complete:return self._pending(phase,p)
                        capture=NpcClickInput(trade_text=p.capture)
                    else:
                        if value is None:return result
                        capture=NpcClickInput(trade_text=value)
                else:return result # Own dialog is supplied separately by the UI.
                result=self.core.advance(capture);self.result=result
                if result.done:return result
                # A scalar value without its normal receipt stays at this stage.
                if self.phase==phase:return result
            raise ValueError('Own NPC source composition budget exhausted')
        except (ValueError,OSError) as error:return self.hold(error)
        finally:self.busy=False
