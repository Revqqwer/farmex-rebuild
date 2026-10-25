import unittest
from armor_start import ArmorStartObservation,ITEM_IDS
from armor_start_frame import ArmorStartFrame,ArmorStartFrameObservation
from operation_engine import UpgradeRunner


def capture(**changes):
    values=dict(filter_ready_returned=True,npc_id_dword=9,npc_pointer_dword=0x7000,
        x_offset_dword=4,y_offset_dword=8,x_ftol_dword=30,y_ftol_dword=100,
        distance_ftol_dword=9,bag_flag_byte=0,
        message_returns={reason:True for reason in ('npc_missing','too_far','item_missing','bag_full')})
    values.update(changes)
    return ArmorStartFrameObservation(1,ArmorStartObservation(**values),{'first':True,'second':True},True,
        {(reason,index):True for reason in ('npc_missing','too_far','item_missing','bag_full') for index in (0,1)})


class ArmorStartFrameTests(unittest.TestCase):
    def frame(self,index=6):
        self.index=index;self.reads=[]
        r=UpgradeRunner(source_clock=True);r.state=1;r.queue=(11,);r.armor_attempts=8
        r.queue_stamp_qword=77;r.armor_stamp_qword=99;r.source_start_ui=(True,False)
        def reader():self.reads.append(self.index);return self.index
        return ArmorStartFrame(r,reader),r

    def test_gate0_preserves_runner_and_ignores_combo(self):
        f,r=self.frame()
        self.assertEqual(f.advance(ArmorStartFrameObservation(gate_byte=0)).status,'gate_closed')
        self.assertFalse(hasattr(r,'armor_source_fields'));self.assertEqual(self.reads,[])

    def test_success_keeps_queue_clocks_and_ui_flags(self):
        f,r=self.frame()
        self.assertEqual(f.advance(capture()).status,'armor_armed')
        self.assertEqual((r.state,r.armor_attempts,r.queue,r.queue_stamp_qword,r.armor_stamp_qword),(2,0,(11,),77,99))
        self.assertEqual((r.armor_source_fields[0x58],r.armor_source_fields[0x5c]),(ITEM_IDS[6],6))
        self.assertEqual((self.reads,r.source_start_ui),([6,6],(True,False)))

    def test_first_combo_freezes_but_second_is_fresh_after_mapping_gap(self):
        f,r=self.frame();o=capture()
        o=ArmorStartFrameObservation(o.gate_byte,o.source,o.combo_returns)
        self.assertEqual(f.advance(o).needed,('item_mapping_returned',))
        self.index=18
        self.assertEqual(f.advance(capture()).status,'armor_armed')
        self.assertEqual((r.armor_source_fields[0x58],r.armor_source_fields[0x5c]),(ITEM_IDS[6],18))
        self.assertEqual(self.reads,[6,18])

    def test_coordinate_prefix_survives_later_gap_without_prior_snapshot(self):
        f,r=self.frame()
        self.assertEqual(f.advance(capture(y_ftol_dword=None)).needed,('y_ftol_dword',))
        self.assertEqual(r.armor_source_fields[0x50],30)
        later=ArmorStartObservation(y_ftol_dword=100,distance_ftol_dword=9,bag_flag_byte=0)
        p=f.advance(ArmorStartFrameObservation(source=later,combo_returns={'first':True,'second':True},item_mapping_returned=True))
        self.assertEqual(p.status,'armor_armed')
        self.assertEqual(r.armor_source_fields[0x50],30)

    def test_blank_mapping_never_reads_second_combo_or_bag(self):
        f,r=self.frame(5)
        self.assertEqual(f.advance(capture(bag_flag_byte=None)).status,'item_missing')
        self.assertEqual((self.reads,r.state,r.armor_attempts),([5],1,8))
        self.assertNotIn(0x5c,r.armor_source_fields)

    def test_second_getter_freezes_while_its_normal_return_waits(self):
        f,r=self.frame();o=capture()
        p=f.advance(ArmorStartFrameObservation(1,o.source,{'first':True},True))
        self.assertEqual(p.needed,('combo_return','second'))
        self.index=18
        self.assertEqual(f.advance(capture()).status,'armor_armed')
        self.assertEqual((r.armor_source_fields[0x5c],self.reads),(6,[6,6]))

    def test_message_has_two_independent_cleanup_receipts(self):
        f,r=self.frame();o=capture(npc_id_dword=0)
        p=f.advance(ArmorStartFrameObservation(1,o.source))
        self.assertEqual((p.needed,r.armor_source_fields[0x4c]),(('message_cleanup','npc_missing',0),0))
        p=f.advance(ArmorStartFrameObservation(message_cleanup_returns={('npc_missing',0):True}))
        self.assertEqual(p.needed,('message_cleanup','npc_missing',1))
        self.assertEqual(f.advance(ArmorStartFrameObservation(message_cleanup_returns={('npc_missing',1):True})).status,'npc_missing')
        self.assertEqual((r.state,r.armor_attempts,self.reads),(1,8,[]))

    def test_signed_distance_and_pointer_zero_boundaries(self):
        f,r=self.frame();self.assertEqual(f.advance(capture(distance_ftol_dword=0x80000000)).status,'armor_armed')
        f,r=self.frame();self.assertEqual(f.advance(capture(distance_ftol_dword=10)).status,'too_far')
        f,r=self.frame();self.assertEqual(f.advance(capture(npc_pointer_dword=0)).status,'npc_pointer_zero')
        self.assertEqual(self.reads,[])

    def test_cancel_keeps_prefix_and_ignores_late_capture(self):
        f,r=self.frame();f.advance(capture(y_ftol_dword=None));f.cancel('profile_change')
        self.assertEqual(f.advance(capture()).status,'cancelled')
        self.assertEqual((r.state,r.armor_attempts,r.armor_source_fields[0x50]),(1,8,30))


if __name__=='__main__':unittest.main()
