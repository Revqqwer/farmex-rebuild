"""Actual Git button, text widgets, timer and profile load; synthetic captures."""
import copy
import tempfile
import time
from pathlib import Path
from unittest.mock import patch
from manual_coordinate import BUTTON_PATH, AXIS_FIELDS, ManualCoordinateObservation
from manual_coordinate_runtime import ManualCoordinateCapture


def check_manual_coordinate_ui(app):
    p=app.panel; root=p.canvas.winfo_toplevel()
    old_document=app.values; old_lists=app.lists
    old_values=dict(app.values); old_list_values=copy.deepcopy(app.lists)
    form=p.form.get(); section=p.section.get(); queue=p.flood_session.queue
    phase={'cleanup':False,'wrong':False}; contexts=[]
    def pump(predicate):
        end=time.monotonic()+5
        while not predicate():
            assert time.monotonic()<end, 'Manual coordinate timer did not advance'
            root.update();time.sleep(.005)
    def provider(c):
        contexts.append(c)
        normals={a+'_'+s:True for a in ('x','y') for s in ('construct','get_text','parse','cleanup')}
        normals.update(entry_setup=True,movement=True,x_cleanup=phase['cleanup'])
        bits={a:{'10':0x41200000,'20':0x41a00000,'30':0x41f00000}[text] for a,text in c.texts.items()}
        return ManualCoordinateCapture(c.invocation,c.generation-1 if phase['wrong'] else c.generation,
            ManualCoordinateObservation(texts=c.texts,float_bits=bits,normal_returns=normals))
    try:
        p.form.set('frmMain');p.render()
        p.set_manual_coordinate_provider(None)
        assert p.widgets[BUTTON_PATH].instate(['disabled'])
        for _,_,path in AXIS_FIELDS:p.variables[path].set('10' if path.endswith('txtGoXKord') else '20')
        p.set_manual_coordinate_provider(provider);p.widgets[BUTTON_PATH].invoke()
        pump(lambda:p.manual_coordinate.result.needed==('normal','x_cleanup'))
        assert p.widgets[BUTTON_PATH].instate(['disabled'])
        assert p.manual_coordinate.result.coordinates==(0x41200000,)
        ticket=p.manual_coordinate.invocation;p.widgets[BUTTON_PATH].invoke()
        assert p.manual_coordinate.invocation==ticket
        p.variables[AXIS_FIELDS[0][2]].set('30');p.variables[AXIS_FIELDS[1][2]].set('30')
        # Re-rendering cannot discard accepted X or the scheduled continuation.
        p.render();phase['wrong']=True
        pump(lambda:p.manual_coordinate.error is not None)
        assert 'Stale' in p.manual_coordinate.error
        phase.update(wrong=False,cleanup=True)
        pump(lambda:not p.manual_coordinate.pending)
        assert p.manual_coordinate.result.movement==(0x41200000,0x41f00000)
        assert p.manual_coordinate_after_id is None and p.widgets[BUTTON_PATH].instate(['!disabled'])
        assert not p.manual_coordinate.result.native_execution_verified
        # Start a new pending invocation then load the identical saved document.
        phase['cleanup']=False;p.widgets[BUTTON_PATH].invoke()
        pump(lambda:p.manual_coordinate.result.needed==('normal','x_cleanup'))
        generation=p.manual_coordinate.generation
        with tempfile.TemporaryDirectory() as directory:
            target=Path(directory)/'coordinate.json';app.profiles.save(target,app.values,app.lists)
            with patch('app.filedialog.askopenfilename',return_value=str(target)):app.load()
        assert app.values is not old_document
        assert not p.manual_coordinate.pending and p.manual_coordinate.result is None
        assert p.manual_coordinate_provider is None and p.manual_coordinate_after_id is None
        assert p.advance_manual_coordinate(generation) is None
        assert p.widgets[BUTTON_PATH].instate(['disabled'])
        assert p.flood_session.queue==queue
        print('Manual coordinate UI passed: actual Git/X/Y widgets, reached-only text, cleanup hold, stale capture, disabled duplicate click, rerender, Tk timer and actual profile load; synthetic captures only, no game movement')
    finally:
        p.reset_manual_coordinate()
        app.values=old_document;app.values.clear();app.values.update(old_values)
        app.lists=old_lists;app.lists.clear();app.lists.update(old_list_values)
        p.form.set(form);p.section.set(section);p.bind_document(app.values,app.lists)


if __name__=='__main__':
    import tkinter as tk
    from app import Application
    root=tk.Tk();root.withdraw()
    try:check_manual_coordinate_ui(Application(root))
    finally:root.destroy()
