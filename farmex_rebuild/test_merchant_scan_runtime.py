import unittest
from dataclasses import replace
from merchant_scan_runtime import OwnedMerchantScan


class OwnedScanTests(unittest.TestCase):
    def fixture(self,route=True):
        s=OwnedMerchantScan();s.configure(0,True,False,False,route)
        events=[]
        callbacks=(lambda:events.append(('clear',)),lambda i,v:events.append(('button',i,v)),
                   lambda v:events.append(('mode',v)),lambda v:events.append(('status',v)))
        return s,events,callbacks

    def test_real_owned_effect_order_and_route_integer_rules(self):
        s,e,c=self.fixture()
        p=s.start(False,True,lambda:(('$FFFFFFFF','+2'),(' 0x10','-3')),*c)
        self.assertTrue(p.complete);self.assertEqual(p.status,'waiting_for_runtime_data')
        self.assertEqual(p.state.route_points,((0xffffffff,2),(16,0xfffffffd)))
        self.assertEqual(e,[('clear',),('button',0,False),('button',1,True),('button',2,False),('mode',1),('status','Taraniyor...')])
        self.assertFalse(p.native_execution_verified);self.assertFalse(p.live_compatibility_verified)

    def test_disabled_route_does_not_read_rows(self):
        s,e,c=self.fixture(False)
        p=s.start(True,False,lambda:(_ for _ in ()).throw(AssertionError('not reached')),*c)
        self.assertTrue(p.complete);self.assertEqual(p.state.route_points,())

    def test_parse_failure_keeps_prefix_and_does_not_activate(self):
        s,e,c=self.fixture()
        p=s.start(True,False,lambda:(('1','2'),('3','bad')),*c)
        self.assertFalse(p.complete);self.assertEqual((p.failed_row,p.failed_coordinate),(1,'y'))
        self.assertEqual(p.state.route_points,((1,2),));self.assertEqual(p.state.active_byte,0)
        self.assertFalse(any(event[0]=='status' for event in e))
        self.assertEqual(p.state.button_enabled,(0,1,0))

    def test_success_preserves_busy_and_stop_preserves_data(self):
        s,e,c=self.fixture();s.state=replace(s.state,busy_byte_0f=9)
        p=s.start(True,False,lambda:(('4','5'),),*c)
        self.assertEqual(p.state.busy_byte_0f,9)
        old=s.state;s.stop(c[1],c[3])
        self.assertEqual(s.state.route_points,old.route_points)
        self.assertEqual((s.state.active_byte,s.state.busy_byte_0f),(0,0))
        self.assertEqual(s.state.status_text,'Hazır')

    def test_clear_failure_precedes_buttons_and_keeps_own_clears(self):
        s,e,c=self.fixture();s.state=replace(s.state,route_points=((1,2),),result_records=(3,))
        def fail():raise RuntimeError('own table failure')
        with self.assertRaisesRegex(RuntimeError,'own table'):
            s.start(True,False,lambda:(),fail,*c[1:])
        self.assertEqual(s.state.route_points,());self.assertEqual(s.state.result_records,())
        self.assertEqual(e,[])

    def test_mode_failure_does_not_store_cached_mode(self):
        s,e,c=self.fixture()
        def fail(index):raise RuntimeError('mode')
        with self.assertRaises(RuntimeError):s.start(False,True,lambda:(),c[0],c[1],fail,c[3])
        self.assertEqual(s.state.options.view_mode_dword,0)
        self.assertEqual(s.state.active_byte,0)

    def test_settings_refresh_keeps_runtime_data(self):
        s,e,c=self.fixture();s.start(True,False,lambda:(('1','2'),),*c)
        before=s.state;s.configure(-1,False,True,True,False)
        self.assertEqual(s.state.route_points,before.route_points)
        self.assertEqual(s.state.active_byte,1);self.assertEqual(s.state.options.view_mode_dword,0)
        self.assertEqual((s.state.options.sell_byte,s.state.options.buy_byte,s.state.options.save_byte,s.state.options.route_byte),(0,1,1,0))

    def test_cell_movement_interrupt_keeps_label_and_route(self):
        s,e,c=self.fixture();s.start(True,False,lambda:(('4','5'),),*c)
        before=s.state;e.clear();p=s.interrupt_for_movement(c[1])
        self.assertEqual(p.state.active_byte,0);self.assertEqual(p.state.busy_byte_0f,0)
        self.assertEqual(p.state.status_text,before.status_text)
        self.assertEqual(p.state.route_points,before.route_points)
        self.assertEqual(e,[('button',0,True),('button',1,False),('button',2,True)])


if __name__=='__main__':unittest.main()
