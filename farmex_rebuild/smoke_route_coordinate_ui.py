"""Actual coordinate button/after/FIFO with explicit synthetic captures only."""
import copy,time
from route_coordinate_click import BUTTON_PATH,CoordinateClickInput
from current_coordinates import CurrentAxisObservation,GuardedFloatSample
from source_coin import GuardedDwordSample
from route_panel_runtime import OPEN_PATH
from panel_ui import SOURCE_ROUTE_LIST,SOURCE_ROUTE_CLEAR,SOURCE_ROUTE_DELETE


def axis(eax,*,second=False):
    root_address=0x200 if second else 0x100;root=0x2000 if second else 0x1000;offset=8 if second else 4
    return CurrentAxisObservation(root_address,GuardedDwordSample(root_address,1,root),True,offset,
        GuardedFloatSample(root+offset,1,0x3fc00000),True,True,eax&0xffffffff,True)


def check_source_route_coordinate_ui(app):
    p=app.panel;values=dict(app.values);lists=copy.deepcopy(app.lists);form=p.form.get();section=p.section.get()
    geometry=dict(p.route_panel.geometry);visible=p.route_panel.visible;last=p.route_panel.last;update=p.route_panel_update
    provider=p.source_coordinate_provider;result=p.source_coordinate_result;queue=p.flood_session.queue
    def pump(predicate):
        deadline=time.monotonic()+3
        while not predicate() and time.monotonic()<deadline:app.root.update();time.sleep(.01)
        assert predicate(),'own coordinate UI timeout'
    def main():
        p.form.set('frmMain');p.render();p.section.set('Koruma');p.select_sections();p.widgets[OPEN_PATH].invoke()
    def empty():
        p.widgets[SOURCE_ROUTE_CLEAR].invoke();assert not p.lists[SOURCE_ROUTE_LIST]
    try:
        main();p.set_source_coordinate_provider(None);empty()
        assert p.widgets[BUTTON_PATH].instate(['disabled'])
        p.widgets[BUTTON_PATH].invoke();assert not p.lists[SOURCE_ROUTE_LIST]
        ready=[False];seen=[]
        def capture(context):
            seen.append(context)
            if not ready[0]:return None
            return CoordinateClickInput(x=axis(11)) if context.axis=='x' else CoordinateClickInput(y=axis(-1,second=True))
        p.set_source_coordinate_provider(capture);assert p.widgets[BUTTON_PATH].instate(['!disabled'])
        p.widgets[BUTTON_PATH].invoke()
        assert p.lists[SOURCE_ROUTE_LIST]==[dict(caption='Koordinat',subitems=[],checked=False)]
        assert not p.source_coordinate_result.done and len(p.source_coordinate_pending)==1
        p.render();assert len(p.lists[SOURCE_ROUTE_LIST])==1
        p.form.set('frmBlackList');p.render();ready[0]=True
        pump(lambda:p.source_coordinate_result is not None and p.source_coordinate_result.complete)
        assert p.lists[SOURCE_ROUTE_LIST]==[dict(caption='Koordinat',subitems=['11','-1'],checked=False)]
        main();assert tuple(p.widgets[SOURCE_ROUTE_LIST].item('0','values'))==('Koordinat','11','-1')
        assert any(ctx.axis=='y' for ctx in seen) and not p.source_coordinate_pending
        # Reentrant click queues a distinct invocation without recursion.
        empty();trigger=[False]
        def reentrant(context):
            if not trigger[0]:trigger[0]=True;p.widgets[BUTTON_PATH].invoke()
            return CoordinateClickInput(axis(context.invocation),axis(context.invocation+1000,second=True))
        p.set_source_coordinate_provider(reentrant);p.widgets[BUTTON_PATH].invoke()
        pump(lambda:not p.source_coordinate_pending)
        assert len(p.lists[SOURCE_ROUTE_LIST])==2
        first,second=p.lists[SOURCE_ROUTE_LIST]
        assert int(second['subitems'][0])==int(first['subitems'][0])+1
        # Deleting another row reindexes the table but keeps the target identity.
        empty();p.lists[SOURCE_ROUTE_LIST]=[dict(caption='old',subitems=['x','y'],checked=False)];p.render()
        ready[0]=False;p.set_source_coordinate_provider(capture);p.widgets[BUTTON_PATH].invoke()
        token=p.lists[SOURCE_ROUTE_LIST][1];p.widgets[SOURCE_ROUTE_LIST].selection_set('0');p.widgets[SOURCE_ROUTE_DELETE].invoke()
        assert p.lists[SOURCE_ROUTE_LIST][0] is token
        ready[0]=True;pump(lambda:not p.source_coordinate_pending)
        assert p.lists[SOURCE_ROUTE_LIST]==[dict(caption='Koordinat',subitems=['11','-1'],checked=False)]
        # A removed target must never redirect writes into a replacement row.
        empty();ready[0]=False;p.set_source_coordinate_provider(capture);p.widgets[BUTTON_PATH].invoke()
        calls=len(seen);empty();p.lists[SOURCE_ROUTE_LIST]=[dict(caption='replacement',subitems=['a','b'],checked=False)];p.render()
        ready[0]=True;pump(lambda:not p.source_coordinate_pending)
        assert not p.source_coordinate_result.complete and p.source_coordinate_result.done and len(seen)==calls
        assert p.lists[SOURCE_ROUTE_LIST]==[dict(caption='replacement',subitems=['a','b'],checked=False)]
        # Profile change during a provider callback invalidates all old work.
        empty();generation=p.source_coordinate_generation
        def changed_profile(context):
            new_lists=copy.deepcopy(p.lists);new_lists[SOURCE_ROUTE_LIST]=[dict(caption='new profile',subitems=['a','b'],checked=False)]
            p.bind_document(dict(p.values),new_lists)
            return CoordinateClickInput(axis(99),axis(100,second=True))
        p.set_source_coordinate_provider(changed_profile);p.widgets[BUTTON_PATH].invoke()
        assert p.source_coordinate_result is None and not p.source_coordinate_pending and p.source_coordinate_provider is None
        assert p.widgets[BUTTON_PATH].instate(['disabled']) and p.lists[SOURCE_ROUTE_LIST][0]['caption']=='new profile'
        before=copy.deepcopy(p.lists);assert p.advance_source_coordinate(generation) is None and p.lists==before
        # Provider replacement plus a reentrant new click schedules the new generation.
        main();empty();switched=[False]
        def new_provider(context):return CoordinateClickInput(axis(21),axis(22,second=True))
        def old_provider(context):
            if not switched[0]:
                switched[0]=True;p.set_source_coordinate_provider(new_provider);p.widgets[BUTTON_PATH].invoke()
            return CoordinateClickInput(axis(999),axis(998,second=True))
        p.set_source_coordinate_provider(old_provider);p.widgets[BUTTON_PATH].invoke()
        pump(lambda:not p.source_coordinate_pending)
        assert p.lists[SOURCE_ROUTE_LIST]==[dict(caption='Koordinat',subitems=[],checked=False),
            dict(caption='Koordinat',subitems=['21','22'],checked=False)]
        assert p.source_coordinate_after_id is None and p.flood_session.queue==queue
        print('Source coordinate-click UI passed: actual conditional button/after callbacks, missing capture no fake zero, X/Y holds, rerender/hidden form, FIFO/reentrant clicks, stable row through reindex, deleted target, profile/provider generation and stale timer; synthetic captured axes only, no game IO')
    finally:
        p.reset_source_coordinates('test_restore')
        p.route_panel.geometry=geometry;p.route_panel.visible=visible;p.route_panel.last=last;p.route_panel_update=update
        app.values.clear();app.values.update(values);app.lists.clear();app.lists.update(lists)
        p.form.set(form);p.section.set(section);p.bind_document(app.values,app.lists)
        p.set_source_coordinate_provider(provider);p.source_coordinate_result=result
