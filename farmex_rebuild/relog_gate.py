"""00412874 relog comparison/installation gate; normal inert control only."""
from relog_controller import RelogControllerFrame
from relog_selection import RelogControllerSelectionsFrame,RelogControllerSelectionsObservation


class RelogGateFrame(RelogControllerFrame):
    def _run(self):
        yield ('entry','00412874')
        yield from self._call('prologue','source_frame_setup_span')
        if (yield from self._byte('sleep_enabled',0x553e3c)):
            delay=yield from self._read('sleep_delay',0x553e40)
            yield from self._call('sleep','SleepEx',(0,delay))
        slot=yield from self._read('header_slot',0x553f64)
        root=yield from self._guard('header_root',slot);self.locals['root']=root
        base=yield from self._field('header_base',root,0x5541e4);self.locals['base']=base
        for label,offset in (('first',0x5541ec),('middle',0x5541f0),('last',0x5541f4)):
            self.locals[label]=yield from self._field(label+'_object',base,offset)
        initial=yield from self._field('initial_state',self.locals['first'],0x5541fc,'0045dbdc')
        self.locals['initial_al']=initial&255
        # Source makes every header/byte call above before this zero test.
        if base:
            yield from self._body(root)
        slot=yield from self._read('original_slot',0x553f64)
        root=yield from self._read('original_root',slot)
        offset=yield from self._read('original_offset',0x5541e4)
        obj=yield from self._read('original_object',root+offset)
        target=yield from self._read('original_target',0x554224)
        yield from self._call('original','captured_original_callback',
                              (('EAX',target),('ECX',obj),('stack_args',())))
        self.return_eax=yield from self._value('original_eax')
        yield from self._call('epilogue','source_frame_restore_return_span')

    def _phase(self,label,root):
        return (yield from self._field(label,root,0x5541e8,'0045dbdc'))&255

    def _body(self,root):
        if not (yield from self._byte('install_attempted',0x553c84)):
            yield from self._call('install_probe','004e2bc8',('source_local_dword',))
            if not (yield from self._value('install_probe_eax'))&255:
                raw=yield from self._value('install_probe_local')
                signed=raw if raw<1<<31 else raw-(1<<32)
                if signed>90:
                    slot=yield from self._read('install_root_slot',0x553e80)
                    base=yield from self._guard('install_root',slot)
                    context=yield from self._field('install_context',base,0x5540d4)
                    table=yield from self._guard('install_table',context)
                    offset=yield from self._read('install_slot_offset',0x554204)
                    self.stores.append((0x554218,4,(table+offset)&0xffffffff))
                    fresh=yield from self._read('install_slot_fresh',0x554218)
                    yield from self._call('install_replace','0046b8fc',(0x46f520,fresh,0x554228))
            self.stores.append((0x553c84,1,1))
        slot=yield from self._read('actor_slot',0x553e7c)
        actor=yield from self._guard('actor_root',slot)
        state=yield from self._field('actor_state',actor,0x553fec,'0045dbdc')
        if state&255:
            if not (yield from self._byte('actor_once_done',0x553c85)):
                yield from self._call('actor_once','004f95d0')
                self.stores.append((0x553c85,1,1));return
        if self.locals['initial_al']!=1:return
        enabled=yield from self._enabled('gate',0x50b2d9)
        if not enabled:
            if (yield from self._phase('idle_phase_first',root))==1:
                yield from self._call('gate_advance','00412858');return
            if (yield from self._phase('idle_phase_second',root))==2:
                yield from self._call('gate_advance','00412858')
            return
        if (yield from self._phase('active_phase',root))==5:
            slot=yield from self._read('candidate_slot_first',0x553f6c)
            current=yield from self._guard('candidate_first',slot)
            saved=yield from self._read('saved_first',0x50b2d4)
            if current==saved:
                yield from self._call('gate_select','00412828',(self.locals['first'],));return
            slot=yield from self._read('candidate_slot_second',0x553f6c)
            current=yield from self._guard('candidate_second',slot)
            saved=yield from self._read('saved_second',0x50b2d4)
            if current<saved:
                yield from self._call('gate_select','00412828',(self.locals['last'],));return
        for label,wanted in (('active_fallback_first',1),('active_fallback_second',2),('active_fallback_third',4)):
            if (yield from self._phase(label,root))==wanted:
                yield from self._call('gate_advance','00412858');return


GATE_LABELS={'gate_select':'ui_select','gate_advance':'ui_advance'}


class RelogGateSelectionsObservation(RelogControllerSelectionsObservation):
    _allowed_labels=GATE_LABELS


class RelogGateSelectionsFrame(RelogControllerSelectionsFrame):
    _parent_type=RelogGateFrame
    _labels=GATE_LABELS
    _max_calls=1

    def advance(self,o):
        if not isinstance(o,RelogGateSelectionsObservation):
            raise ValueError('Typed relog gate selector observations required')
        return super().advance(o)
