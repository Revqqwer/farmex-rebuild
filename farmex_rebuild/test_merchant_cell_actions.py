import unittest
from dataclasses import replace
from merchant_cell_actions import MerchantCellState as S,MerchantCellObservation as O,plan_merchant_cell_click as run


COMMON={'selected_index':True,'cursor_pos':True,'form_left':True}
PM={**COMMON,**{k:True for k in ('pm_caption','pm_conversion','private_chat','pm_ansi_cleanup','pm_unicode_cleanup')}}
MOVE={**COMMON,**{k:True for k in ('enable_b64','enable_b68','enable_b6c','x_text','x_float','x_cleanup','y_text','y_float','y_cleanup','movement')}}


def clicked(relative,**kw):
    fields=dict(selected_index_dword=2,cursor_x_dword=relative+110,form_left_dword=100,list_left_dword=10,
                caption_unicode='Seller',caption_ansi=b'Seller',x_unicode='825',y_unicode='520',
                x_float32_bits=0x444e4000,y_float32_bits=0x44020000,normal_returns=MOVE if relative>=780 else PM)
    fields.update(kw);return O(**fields)


class MerchantCellActionTests(unittest.TestCase):
    def test_signed_negative_selection_exits_before_cursor(self):
        for selected in (0xffffffff,0x80000000):
            p=run(S(3,4),O(selected_index_dword=selected,normal_returns={'selected_index':True}))
            self.assertTrue(p.complete)
            self.assertEqual(p.status,'no_selected_row')
            self.assertEqual(p.state,S(3,4))
            self.assertFalse(any(s[0]=='normal' and s[1]=='cursor_pos' for s in p.steps))

    def test_both_inclusive_action_windows_and_gaps(self):
        for value,action in ((734,None),(735,'private_chat'),(775,'private_chat'),(776,None),
                             (779,None),(780,'move_to_seller'),(820,'move_to_seller'),(821,None)):
            p=run(S(1,1),clicked(value))
            self.assertTrue(p.complete,(value,p.needed))
            self.assertEqual(p.action,action)

    def test_cursor_arithmetic_wraps_before_signed_comparison(self):
        p=run(S(),clicked(735,form_left_dword=0xfffffff0,list_left_dword=0x20,cursor_x_dword=751))
        self.assertEqual((p.relative_x_dword,p.action),(735,'private_chat'))
        p=run(S(),clicked(735,form_left_dword=0,list_left_dword=0,cursor_x_dword=0xffffffff))
        self.assertEqual(p.status,'outside_action_windows')

    def test_cursor_BOOL_is_ignored_but_missing_local_x_is_not_zero(self):
        p=run(S(),clicked(735,cursor_result_dword=0))
        self.assertTrue(p.complete)
        p=run(S(),clicked(735,cursor_result_dword=0,cursor_x_dword=None))
        self.assertEqual(p.needed,('value','cursor_x_dword'))
        self.assertTrue(any(s[0]=='normal' and s[1]=='form_left' for s in p.steps))

    def test_PM_passes_separate_ANSI_capture_and_does_not_change_scan_state(self):
        p=run(S(7,8),clicked(735,caption_unicode='different display',caption_ansi=b'\xfdSeller'))
        self.assertTrue(p.complete)
        self.assertEqual((p.private_chat_context,p.private_chat_target),(0x561ef8,b'\xfdSeller'))
        self.assertEqual(p.state,S(7,8))
        self.assertEqual(p.movement_push_order,())
        self.assertFalse(p.native_execution_verified or p.delivery_verified or p.live_compatibility_verified)

    def test_PM_missing_conversion_does_not_encode_visible_caption(self):
        p=run(S(),clicked(735,caption_ansi=None))
        self.assertFalse(p.complete)
        self.assertEqual(p.needed,('value','caption_ansi'))
        self.assertFalse(any(s[0]=='normal' and s[1]=='private_chat' for s in p.steps))

    def test_PM_empty_target_remains_explicit_not_missing(self):
        p=run(S(),clicked(735,caption_unicode='',caption_ansi=b''))
        self.assertTrue(p.complete)
        self.assertEqual((p.private_chat_target,p.private_chat_context),(b'',0x561ef8))

    def test_PM_helper_and_cleanup_returns_remain_separate(self):
        p=run(S(),clicked(735,normal_returns={**PM,'pm_ansi_cleanup':False}))
        self.assertFalse(p.complete)
        self.assertEqual(p.needed,('normal','pm_ansi_cleanup'))
        self.assertEqual(p.private_chat_target,b'Seller')
        self.assertFalse(any(s[0]=='normal' and s[1]=='pm_unicode_cleanup' for s in p.steps))

    def test_move_resets_both_flags_before_first_UI_call(self):
        p=run(S(7,8),clicked(780,normal_returns=COMMON))
        self.assertFalse(p.complete)
        self.assertEqual(p.state,S(0,0))
        self.assertEqual(p.needed,('normal','enable_b64'))
        self.assertEqual([(e.form_field_offset,e.enabled_byte,e.normal_return_observed) for e in p.ui_enables],[(0xb64,1,False)])
        self.assertFalse(any(s[0]=='normal' and s[1]=='x_text' for s in p.steps))

    def test_move_UI_order_and_float_bit_push_order(self):
        p=run(S(1,1),clicked(780))
        self.assertTrue(p.complete)
        self.assertEqual([(e.form_field_offset,e.enabled_byte) for e in p.ui_enables],[(0xb64,1),(0xb68,0),(0xb6c,1)])
        self.assertEqual(p.movement_push_order,(0x44020000,0x444e4000))
        self.assertEqual(p.private_chat_target,None)
        self.assertEqual([s[3] for s in p.steps if s[:2] in (('normal','x_text'),('normal','y_text'))],[(2,5),(2,6)])

    def test_move_float_failure_keeps_flags_and_skips_second_coordinate(self):
        p=run(S(9,8),clicked(780,normal_returns={**MOVE,'x_float':False}))
        self.assertEqual(p.state,S(0,0))
        self.assertEqual(p.needed,('normal','x_float'))
        self.assertFalse(any(s[0]=='normal' and s[1]=='y_text' for s in p.steps))

    def test_no_python_float_rounding_or_finiteness_guard_is_invented(self):
        p=run(S(),clicked(780,x_unicode='captured locale text',x_float32_bits=0x7fc00001,y_float32_bits=0x80000000))
        self.assertTrue(p.complete)
        self.assertEqual(p.movement_push_order,(0x80000000,0x7fc00001))

    def test_movement_return_is_not_inferred_from_known_coordinates(self):
        p=run(S(1,1),clicked(780,normal_returns={**MOVE,'movement':False}))
        self.assertFalse(p.complete)
        self.assertEqual(p.needed,('normal','movement'))
        self.assertEqual(p.movement_push_order,(0x44020000,0x444e4000))

    def test_contracts(self):
        with self.assertRaises(ValueError):S(256,0)
        with self.assertRaises(ValueError):O(selected_index_dword=-1)
        with self.assertRaises(ValueError):O(caption_ansi='not ANSI bytes')
        with self.assertRaises(ValueError):O(normal_returns={'selected_index':1})
        with self.assertRaises(ValueError):run(S(),None)


if __name__=='__main__':unittest.main()
