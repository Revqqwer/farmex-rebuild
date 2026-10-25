import unittest
from route_panel_runtime import OwnedRoutePanel


class RoutePanelTests(unittest.TestCase):
    def test_open_reads_each_property_fresh_between_ordered_setters(self):
        panel=OwnedRoutePanel();tabs={'left':271,'top':0,'height':470};events=[]
        def read(field):events.append(('read',field));return tabs[field]
        def write(field,value):
            events.append(('write',field,value))
            if field=='left':tabs['top']=10
            if field=='top':tabs['height']=490
        p=panel.open(read,write)
        self.assertTrue(p.complete)
        self.assertEqual(events,[('read','left'),('write','left',271),('read','top'),
            ('write','top',30),('read','height'),('write','height',470),
            ('write','width',600),('write','visible',True)])
        self.assertTrue(p.visible);self.assertFalse(p.route_editing_verified)

    def test_open_failure_retains_completed_prefix_without_showing(self):
        panel=OwnedRoutePanel();writes=[]
        def write(field,value):
            if field=='height':raise OSError('own setter failed')
            writes.append((field,value))
        p=panel.open(lambda field:1,write)
        self.assertFalse(p.complete);self.assertEqual(dict(p.geometry),{'left':1,'top':21})
        self.assertIsNone(p.visible);self.assertEqual(writes,[('left',1),('top',21)])

    def test_close_unchecks_before_hide_and_retains_prefix_if_hide_fails(self):
        panel=OwnedRoutePanel();panel.visible=True;events=[]
        def uncheck():events.append('unchecked')
        def fail(field,value):events.append((field,value));raise OSError('hide failed')
        p=panel.close(uncheck,fail)
        self.assertFalse(p.complete);self.assertTrue(p.recording_reset);self.assertTrue(p.visible)
        self.assertEqual(events,['unchecked',('visible',False)])
        p=panel.close(uncheck,lambda field,value:events.append((field,value)))
        self.assertTrue(p.complete);self.assertFalse(p.visible)

    def test_int32_add_subtract_wrap_is_preserved_before_own_widget_policy(self):
        panel=OwnedRoutePanel()
        p=panel.open(lambda field:{'left':0xffffffff,'top':0x7fffffff,'height':0x80000000}[field],lambda *_:None)
        self.assertEqual((p.geometry['left'],p.geometry['top'],p.geometry['height']),(-1,-2147483629,2147483628))
        self.assertTrue(p.complete);self.assertFalse(p.native_execution_verified)


if __name__=='__main__':unittest.main()
