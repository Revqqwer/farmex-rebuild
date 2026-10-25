import unittest
from dataclasses import replace
from route_gate_record import GateRecordFrame,GateRecordObservation
from route_npc_click import NpcValueCapture as C
from test_route_coordinate_click import Sink


def observed(**changes):
    fields=dict(recording_byte=1,zone_first=C(32,True),zone_second=C(33,True),
        clock=C(123,True),reader_returned=True,actor=C(0x1000,True),
        name_setup_returned=True,name_storage=C(15,True),name_ansi=C(b'[Teleport Gate]',True),
        comparison_returned=True,format_returned=True)
    fields.update(changes);return GateRecordObservation(**fields)


class GateRecordTests(unittest.TestCase):
    def test_all_four_source_row_shapes(self):
        for packet,row in ((b'\x20\x01\x77\x00',['Delos Gate Open',['-','-']]),
          (b'\x33\xff\xff\xff\xff',['Gate Open',['4294967295','-']]),
          (b'\x4b\x00\x00\x00\x80',['Gate',['2147483648','-']]),
          (b'\x55\xff',['Delos Gate',['255','-']])):
            with self.subTest(packet=packet):
                sink=Sink();p=GateRecordFrame(packet,sink).advance(observed())
                self.assertTrue(p.complete);self.assertEqual(sink.rows,[row])
                self.assertFalse(p.native_execution_verified);self.assertFalse(p.live_compatibility_verified)

    def test_gate_clock_occurs_before_recording_flag_even_when_disabled(self):
        f=GateRecordFrame(b'\x4b',Sink())
        p=f.advance(observed(recording_byte=0,clock=C(0xffffffff,False)))
        self.assertEqual(p.needed,'clock.returned');self.assertNotIn('recording_byte',f.cache)
        p=f.advance(observed(recording_byte=0,clock=C(1,True)))
        self.assertEqual(p.status,'recording_disabled')
        self.assertEqual(p.writes,((0x561f74,32,0xffffffff),(0x561f78,32,0)))
        self.assertIs(f.advance({}),p)

    def test_other_disabled_branches_do_not_read_packet_or_helpers(self):
        for packet in (b'\x20\x01',b'\x33',b'\x55'):
            f=GateRecordFrame(packet,Sink());p=f.advance(GateRecordObservation(recording_byte=0,clock={}))
            self.assertTrue(p.complete);self.assertEqual(p.writes,())
            self.assertEqual(f.cache,{'recording_byte':0})

    def test_zones_are_fresh_distinct_calls_with_lazy_short_circuit(self):
        f=GateRecordFrame(b'\x55\x01',Sink());p=f.advance(observed(zone_first=C(32,True),zone_second={}))
        self.assertTrue(p.complete);self.assertNotIn('zone_second',f.cache)
        g=GateRecordFrame(b'\x55\x01',Sink());p=g.advance(observed(zone_first=C(33,True),zone_second=C(32,True)))
        self.assertEqual(p.status,'zone_rejected')
        h=GateRecordFrame(b'\x55\x01',Sink());p=h.advance(observed(zone_first=C(0,False),zone_second={}))
        self.assertEqual(p.needed,'zone_first.returned');self.assertNotIn('zone_second',h.cache)
        p=h.advance(observed(zone_first=C(32,True),zone_second=C(33,True)))
        self.assertTrue(p.complete);self.assertEqual(h.cache['zone_first']['value'],0)

    def test_npc_storage_filter_is_after_name_production_and_inline_count_is50(self):
        f=GateRecordFrame(b'\x20\x01\x77\0',Sink())
        p=f.advance(observed(name_storage=C(5,True),name_ansi=C(b'Other',False),comparison_returned={}))
        self.assertEqual(p.needed,'name_ansi.returned');self.assertEqual(p.name_read_count,50)
        p=f.advance(observed());self.assertEqual(p.status,'storage_rejected')
        for storage,count in ((16,16),(512,512),(0xffffffff,50)):
            g=GateRecordFrame(b'\x20\x01\x77\0',Sink())
            p=g.advance(observed(name_storage=C(storage,True)))
            self.assertEqual(p.status,'storage_rejected');self.assertEqual(p.name_read_count,count)

    def test_npc_zero_ids_and_lookup_stop_before_name(self):
        f=GateRecordFrame(b'\x20\x01\0\0',Sink());p=f.advance(observed(actor={},name_ansi={}))
        self.assertEqual(p.status,'zero_npc_id');self.assertNotIn('actor',f.cache)
        g=GateRecordFrame(b'\x20\x01\x01\0',Sink());p=g.advance(observed(actor=C(0,True),name_storage={}))
        self.assertEqual(p.status,'lookup_empty');self.assertNotIn('name_storage',g.cache)

    def test_name_equality_and_normal_comparison_remain_independent(self):
        for name in (b'[teleport gate]',b'[Teleport Gate]x',b''):
            f=GateRecordFrame(b'\x20\x01\x01\0',Sink())
            p=f.advance(observed(name_ansi=C(name,True),comparison_returned=False))
            self.assertEqual(p.needed,'comparison_returned')
            self.assertEqual(f.advance(observed()).status,'name_rejected')

    def test_formatter_return_gap_preserves_row_and_clock_prefix_without_duplicates(self):
        sink=Sink();f=GateRecordFrame(b'\x4b\x01\0\0\0',sink)
        p=f.advance(observed(format_returned=False))
        self.assertEqual(sink.rows,[['Gate',[]]]);self.assertEqual(len(p.writes),2)
        p=f.advance(observed(clock={},format_returned=False));self.assertEqual(len(p.writes),2)
        p=f.advance(observed());self.assertTrue(p.complete);self.assertEqual(sink.rows,[['Gate',['1','-']]])

    def test_missing_packet_range_is_unresolved_and_other_dispatch_is_not_certified(self):
        f=GateRecordFrame(b'\x33\x01',Sink());p=f.advance(observed())
        self.assertFalse(p.complete);self.assertEqual(p.needed,'packet_bytes[1:5]')
        self.assertIsNone(p.row)
        p=GateRecordFrame(b'\x06',Sink()).advance(observed(recording_byte={}))
        self.assertFalse(p.complete);self.assertTrue(p.done);self.assertEqual(p.status,'outside_record_scope')

    def test_deleted_row_and_cancellation_never_commit_late_subitems(self):
        sink=Sink();f=GateRecordFrame(b'\x33\x01\0\0\0',sink)
        f.advance(observed(format_returned=False));sink.rows[:]=[['replacement',[]]]
        p=f.advance(observed());self.assertFalse(p.complete);self.assertTrue(p.done)
        self.assertEqual(sink.rows,[['replacement',[]]])
        g=GateRecordFrame(b'\x33',Sink());p=g.cancel('profile')
        self.assertIs(g.advance(observed()),p)


if __name__=='__main__':unittest.main()
