"""Source branch and interruption boundaries for the scan control projection."""
import unittest
from dataclasses import replace
from merchant_scan_control import (
    MerchantScanOptions,ScanSettingsObservation,ScanControlState,
    ScanControlObservation,ScanRouteRowObservation,plan_scan_settings,
    plan_scan_settings_callback,plan_scan_start_stop)


def settings(**kw):
    args=dict(combo_index_dword=2,sell_checked_eax=0x123401,
              buy_checked_eax=0x123402,save_checked_eax=0x123403,
              route_checked_eax=0x123404,
              normal_returns=dict.fromkeys(('combo','sell','buy','save','route'),True))
    args.update(kw)
    return ScanSettingsObservation(**args)


def observation(**kw):
    labels=['result_list_clear','enable_b64','enable_b68','enable_b6c',
            'sell_checked','buy_checked','select_buying',
            'status_construct','status_set','status_cleanup']
    labels += ['clear_'+f+'_'+p for f in ('vector_78','vector_58','route_points','result_records')
               for p in ('end','begin','erase')]
    args=dict(entry_reached=True,sell_checked_eax=1,buy_checked_eax=0,
              normal_returns=dict.fromkeys(labels,True))
    args.update(kw)
    return ScanControlObservation(**args)


def route(**kw):
    args=dict(x_unicode='-1',y_unicode='2',x_eax=0xffffffff,y_eax=2,
              size_dword=0,capacity_dword=1,fast_new_end_eax=0x12345678,
              normal_returns=dict.fromkeys(('x_text','x_parse','x_cleanup',
              'y_text','y_parse','y_cleanup','size','capacity','fast_append',
              'grow_end','grow_append'),True))
    args.update(kw)
    return ScanRouteRowObservation(**args)


class ScanSettingsTests(unittest.TestCase):
    def test_signed_combo_and_raw_low_bytes(self):
        for n,expected in ((0,0),(1,1),(0x7fffffff,1),(0x80000000,0),(0xffffffff,0)):
            with self.subTest(n=n):
                p=plan_scan_settings(MerchantScanOptions(),settings(combo_index_dword=n))
                self.assertTrue(p.complete)
                self.assertEqual(p.options,MerchantScanOptions(expected,1,2,3,4))

    def test_each_getter_failure_preserves_only_completed_stores(self):
        old=MerchantScanOptions(8,9,10,11,12)
        fields=('view_mode_dword','sell_byte','buy_byte','save_byte','route_byte')
        for i,label in enumerate(('combo','sell','buy','save','route')):
            o=settings();normals=dict(o.normal_returns);normals[label]=False
            p=plan_scan_settings(old,replace(o,normal_returns=normals))
            self.assertFalse(p.complete)
            for j,name in enumerate(fields):
                self.assertEqual(getattr(p.options,name),(1,1,2,3,4)[j] if j<i else getattr(old,name))

    def test_closed_gate_does_not_inspect_getters(self):
        old=MerchantScanOptions(2,3,4,5,6)
        p=plan_scan_settings_callback(old,0,object())
        self.assertTrue(p.complete);self.assertEqual(p.options,old)
        self.assertFalse(plan_scan_settings_callback(old,None).complete)
        self.assertTrue(plan_scan_settings_callback(old,255,settings()).complete)


class ScanControlTests(unittest.TestCase):
    def old(self,**kw):
        args=dict(active_byte=9,busy_byte_0f=7,route_index_dword=11,
                  vector_78=(1,),vector_58=(2,),route_points=((3,4),),
                  result_records=(5,),status_text='old')
        args.update(kw);return ScanControlState(**args)

    def test_start_clears_vectors_not_pending_flag(self):
        p=plan_scan_start_stop(self.old(),255,0,observation())
        self.assertTrue(p.complete)
        self.assertEqual((p.state.vector_78,p.state.vector_58,p.state.route_points,p.state.result_records),((),(),(),()))
        self.assertEqual((p.state.active_byte,p.state.busy_byte_0f,p.state.route_index_dword),(1,7,0))
        self.assertEqual(p.state.button_enabled,(0,1,0))
        self.assertEqual(p.state.status_text,'Taraniyor...')
        self.assertFalse(p.native_execution_verified)

    def test_entry_required_before_any_change(self):
        old=self.old();p=plan_scan_start_stop(old,1,0)
        self.assertEqual(p.state,old);self.assertEqual(p.needed,('entry','004be6f0'))

    def test_start_partial_clear_does_not_roll_back(self):
        o=observation();n=dict(o.normal_returns);n['clear_route_points_begin']=False
        p=plan_scan_start_stop(self.old(),1,0,replace(o,normal_returns=n))
        self.assertEqual(p.state.vector_78,());self.assertEqual(p.state.vector_58,())
        self.assertEqual(p.state.route_points,((3,4),))
        self.assertEqual(p.state.route_index_dword,11)
        self.assertEqual(p.state.active_byte,9)

    def test_buying_requires_sell_low_byte_zero_and_buy_exact_one(self):
        for sell,buy,forced in ((0x100,0x101,1),(0,2,None),(1,1,None),(0,0,None)):
            with self.subTest(sell=sell,buy=buy):
                p=plan_scan_start_stop(self.old(),1,0,observation(sell_checked_eax=sell,buy_checked_eax=buy))
                self.assertTrue(p.complete);self.assertEqual(p.forced_combo_index,forced)

    def test_failed_combo_setter_keeps_cached_mode(self):
        o=observation(sell_checked_eax=0,buy_checked_eax=1)
        n=dict(o.normal_returns);n['select_buying']=False
        p=plan_scan_start_stop(self.old(options=MerchantScanOptions(6)),1,0,replace(o,normal_returns=n))
        self.assertFalse(p.complete);self.assertEqual(p.state.options.view_mode_dword,6)

    def test_stop_preserves_vectors_and_index(self):
        for completed,text in ((0,'Hazır'),(255,'Tarama Tamamlandi !')):
            old=self.old();p=plan_scan_start_stop(old,0,completed,observation())
            self.assertTrue(p.complete)
            self.assertEqual(p.state,replace(old,active_byte=0,busy_byte_0f=0,button_enabled=(1,0,1),status_text=text))

    def test_stop_flags_precede_button_failure(self):
        o=observation();n=dict(o.normal_returns);n['enable_b64']=False
        old=self.old(button_enabled=(0,1,0))
        p=plan_scan_start_stop(old,0,0,replace(o,normal_returns=n))
        self.assertEqual(p.state,replace(old,active_byte=0,busy_byte_0f=0))

    def run_rows(self,rows,counts):
        o=observation(rows=rows,row_counts=counts)
        n=dict(o.normal_returns);n.update({'row_count:'+str(i):True for i in range(len(counts))})
        return plan_scan_start_stop(self.old(options=MerchantScanOptions(route_byte=1)),1,0,replace(o,normal_returns=n))

    def test_route_fast_and_grow_with_fresh_counts(self):
        p=self.run_rows((route(),route(size_dword=1,capacity_dword=1,x_eax=7)),(2,2,2))
        self.assertTrue(p.complete);self.assertEqual(p.state.route_points,((0xffffffff,2),(7,2)))
        self.assertIn(('route_normal',1,'grow_end'),p.steps)
        self.assertIn(('route_end_store',0x12345678),p.steps)

    def test_empty_or_negative_count_finishes_start(self):
        for count in (0,0xffffffff,0x80000000):
            p=self.run_rows((),(count,));self.assertTrue(p.complete)
            self.assertEqual(p.state.route_points,());self.assertEqual(p.state.active_byte,1)

    def test_missing_fast_end_does_not_commit_logical_point(self):
        p=self.run_rows((route(fast_new_end_eax=None),),(1,))
        self.assertFalse(p.complete);self.assertEqual(p.state.route_points,())
        self.assertEqual(p.state.active_byte,9)
        self.assertIn(('route_copy_pending_end',0,0xffffffff,2),p.steps)

    def test_growth_iterator_return_required_before_append(self):
        r=route(size_dword=0xffffffff,capacity_dword=1)
        n=dict(r.normal_returns);n['grow_end']=False
        p=self.run_rows((replace(r,normal_returns=n),),(1,))
        self.assertEqual(p.needed,('route_normal',(0,'grow_end')))
        self.assertNotIn(('route_normal',0,'grow_append'),p.steps)

    def test_parse_failure_keeps_prior_point_and_old_active(self):
        r=route();n=dict(r.normal_returns);n['y_parse']=False
        p=self.run_rows((route(),replace(r,normal_returns=n)),(2,2))
        self.assertFalse(p.complete);self.assertEqual(p.state.route_points,((0xffffffff,2),))
        self.assertEqual(p.state.active_byte,9)

    def test_status_cleanup_failure_preserves_set_text(self):
        o=observation();n=dict(o.normal_returns);n['status_cleanup']=False
        p=plan_scan_start_stop(self.old(),1,0,replace(o,normal_returns=n))
        self.assertFalse(p.complete);self.assertEqual(p.state.active_byte,1)
        self.assertEqual(p.state.status_text,'Taraniyor...')


if __name__=='__main__':unittest.main()
