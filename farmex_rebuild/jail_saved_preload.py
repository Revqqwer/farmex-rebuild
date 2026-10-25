"""Completed own selection -> explicit stable saved-list preload fixture.

Never creates observations for a missing native read or normal return. Supplied
raw vector observations must agree with the caller's declared own fixture.
"""
from dataclasses import dataclass
from jail_selection import JailSelectionPlan
from jail_protection import JailObservation
from jail_preload import JailPreloadFrame,MASK
from name_codec import WindowsNameCodec

@dataclass(frozen=True)
class SavedPreloadPlan:
    complete: bool
    source: object
    captions: tuple=()
    codepage: int=0
    stable_owned_fixture: bool=True
    source_RTL_conversion_verified: bool=False
    native_execution_verified: bool=False
    live_compatibility_verified: bool=False

class SavedWindowPreload:
    def __init__(self,selection,*,vector_begin,codepage,stable_saved_rows=False):
        if not isinstance(selection,JailSelectionPlan) or not selection.complete:
            raise ValueError('Completed typed selection required before preload binding')
        if stable_saved_rows is not True:raise ValueError('Explicit own stable saved-row fixture required')
        if type(vector_begin) is not int or not 0<=vector_begin<=MASK:
            raise ValueError('Explicit raw fixture begin required')
        if type(selection.rows) is not tuple or any(type(v) is not bytes for v in selection.rows):
            raise ValueError('Immutable saved ANSI rows required')
        if selection.rows and vector_begin==0:raise ValueError('Nonempty own fixture needs nonzero begin')
        self.rows=selection.rows;self.begin=vector_begin;self.end=(vector_begin+4*len(self.rows))&MASK
        self.codec=WindowsNameCodec(codepage);self.frame=JailPreloadFrame()
        self.captions=[];self.applied=0;self.last=None;self.final=None

    def _collect(self,p):
        if len(p.ui_intents)<self.applied:raise AssertionError('Preload prefix retracted')
        for intent in p.ui_intents[self.applied:]:
            if intent[0]=='caption_set':
                index=len(self.captions)
                if index>=len(self.rows):raise ValueError('Caption exceeds declared stable rows')
                # The text is our explicit local codec projection, not a native
                # pointer dereference or verification of the source RTL result.
                text=self.codec.decode(self.rows[index])
                self.captions.append((index,intent[1],intent[2],text))
        self.applied=len(p.ui_intents)

    def _result(self,p):
        self._collect(p)
        return SavedPreloadPlan(p.complete,p,tuple(self.captions),self.codec.code_page)

    def advance(self,o):
        if not isinstance(o,JailObservation):raise ValueError('Typed raw preload observations required')
        if self.final is not None:return self.final
        self.last=None
        while True:
            p=self.frame.advance(JailObservation());result=self._result(p)
            if p.complete:self.final=result;self.last=result;return result
            kind,label=p.needed
            if kind=='entry':
                if not o.entry_reached:self.last=result;return result
                incoming=JailObservation(True)
            elif kind=='normal':
                if o.normal_returns.get(label) is not True:self.last=result;return result
                incoming=JailObservation(normal_returns={label:True})
            else:
                if label not in o.values:self.last=result;return result
                value=o.values[label]
                if '.' in label:
                    index_text,suffix=label.split('.',1)
                    index=int(index_text[3:])
                    if suffix in ('count_initial_begin','count_sub_begin','element_begin') and value!=self.begin:
                        raise ValueError('Fresh begin contradicts declared stable fixture')
                    if suffix=='count_end' and value!=self.end:
                        raise ValueError('Fresh end contradicts completed saved rows')
                    if suffix=='element_begin' and index>=len(self.rows):
                        raise ValueError('Element outside completed saved rows')
                incoming=JailObservation(values={label:value})
            p=self.frame.advance(incoming)
            self._collect(p)
