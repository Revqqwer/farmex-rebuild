import unittest
from dataclasses import replace
from upgrade_refresh import UpgradeRefreshFrame,UpgradeRefreshObservation,UpgradeRefreshSlot,GuardedCapture
from source_coin import GuardedDwordSample,GuardedByteSample
from item_name import ItemNameObservation
from npc_unicode import NpcUnicodeObservation
from test_route_coordinate_click import Sink as BaseSink


class Sink(BaseSink):
    def clear(self):self.events.append('clear');self.rows.clear()


def dword(address,value,returned=True):return GuardedCapture(GuardedDwordSample(address,1,value),returned)
def byte(address,value,returned=True):return GuardedCapture(GuardedByteSample(address,1,value),returned)


def filled(slot=14,name=b'Item',*,base=1000,first=2,fresh=9,kind=5):
    record=0x5000+slot*0x100;lookup=0x8000;metadata=0x9000
    return UpgradeRefreshSlot(0x20,dword(0x4000+0x20+slot*4,record),
        dword(record+0x60,lookup),dword(record+0x64,metadata),dword(lookup,base),dword(metadata,first),True,
        ItemNameObservation(metadata_category=5,storage_dword=15,pointer_dword=int.from_bytes((name+b'\0'*4)[:4],'little'),bad_read_result=0,captured=name+b'\0'*(255-len(name))),
        True,NpcUnicodeObservation(False,1254,None,True,True,True),True,True,True,
        dword(metadata,fresh),byte(metadata+0x44,kind),True,True,True)


def observed(**changes):
    slots={slot:UpgradeRefreshSlot(0x20,dword(0x4000+0x20+slot*4,0)) for slot in range(14,42)}
    slots[14]=filled()
    fields=dict(gate_byte=1,initial_text_returned=True,global_root_dword=0x100,root=dword(0x100,0x1000),
        inventory_offset_dword=8,inventory=dword(0x1008,0x4000),slots=slots,final_cleanup_returned=True)
    fields.update(changes);return UpgradeRefreshObservation(**fields)


def finish(frame,o):
    for _ in range(20):
        p=frame.advance(o)
        if p.done or p.status!='continuation':return p
    raise AssertionError('own test refresh continuation did not finish')


class UpgradeRefreshTests(unittest.TestCase):
    def test_gate_zero_leaves_list_and_does_not_touch_other_fields(self):
        sink=Sink();sink.rows=[['old',[]]]
        p=UpgradeRefreshFrame(sink).advance(UpgradeRefreshObservation(gate_byte=0,root={},slots={14:{}}))
        self.assertTrue(p.complete);self.assertEqual(sink.rows,[['old',[]]]);self.assertEqual(sink.events,[])

    def test_clear_precedes_missing_initial_text_or_root_and_is_not_repeated(self):
        sink=Sink();sink.rows=[['old',[]]];f=UpgradeRefreshFrame(sink)
        p=f.advance(UpgradeRefreshObservation(gate_byte=1));self.assertEqual(p.needed,('entry','initial_text_returned'))
        self.assertEqual(sink.rows,[]);self.assertEqual(sink.events,['clear'])
        p=f.advance(UpgradeRefreshObservation(initial_text_returned=True))
        self.assertEqual(p.needed,('entry','global_root_dword'));self.assertEqual(sink.events,['clear'])

    def test_null_inventory_requires_final_cleanup_and_keeps_cleared_prefix(self):
        sink=Sink();f=UpgradeRefreshFrame(sink)
        p=f.advance(observed(inventory=dword(0x1008,0),slots={14:{}},final_cleanup_returned=False))
        self.assertEqual(p.needed,('entry','final_cleanup_returned'));self.assertEqual(sink.rows,[])
        p=f.advance(UpgradeRefreshObservation(final_cleanup_returned=True));self.assertTrue(p.complete)
        self.assertEqual(len(p.requests),2)

    def test_full_scan_rows_relative_slot_and_fresh_grade(self):
        sink=Sink();o=observed();o.slots[41]=filled(41,b'Last',first=3,fresh=102)
        f=UpgradeRefreshFrame(sink);p=finish(f,o)
        self.assertTrue(p.complete);self.assertEqual(sink.rows,[['0',['Item (+9)']],['27',['Last (+2)']]])
        records=[r for r in p.requests if isinstance(r[0],tuple) and r[0][1]=='record']
        self.assertEqual([key[0] for key,_,_ in records],list(range(14,42)))
        self.assertEqual(f.item_id,1003);self.assertFalse(p.native_execution_verified)

    def test_name_runs_before_filter_and_fresh_variant_not_consumed_early(self):
        sink=Sink();o=observed();o.slots[14]=replace(filled(kind=1),name_returned=False,variant_fresh={})
        f=UpgradeRefreshFrame(sink);p=f.advance(o)
        self.assertEqual(p.needed,(14,'name_returned'));self.assertNotIn((14,'variant_fresh'),f.reads)
        self.assertNotIn((14,'kind'),f.reads);self.assertEqual(sink.rows,[])
        self.assertTrue(finish(f,observed(slots={**observed().slots,14:filled(kind=1)})).complete)
        self.assertEqual(sink.rows,[])

    def test_name_unicode_and_assignment_cleanup_are_independent(self):
        for field in ('name_returned','assignment_returned','unicode_cleanup_returned','ansi_cleanup_returned'):
            o=observed();o.slots[14]=replace(filled(),**{field:False})
            f=UpgradeRefreshFrame(Sink());p=f.advance(o)
            self.assertEqual(p.needed,(14,field));self.assertNotIn((14,'variant_fresh'),f.reads)
            self.assertTrue(finish(f,observed()).complete)
        o=observed();o.slots[14]=replace(filled(),unicode=NpcUnicodeObservation(False,None))
        p=UpgradeRefreshFrame(Sink()).advance(o);self.assertEqual(p.needed,(14,'unicode',('codepage_word',)))

    def test_short_name_capture_can_complete_and_consumed_fields_do_not_change(self):
        o=observed();full=o.slots[14].name
        o.slots[14]=replace(filled(),name=replace(full,captured=b'Old'))
        f=UpgradeRefreshFrame(Sink());p=f.advance(o)
        self.assertEqual(p.needed,(14,'name','needs_observation','complete_captured_bytes:255'))
        o.slots[14]=replace(filled(),name=replace(full,metadata_category=7,captured=b'Kept\0'+b'\0'*250))
        self.assertTrue(finish(f,o).complete);self.assertEqual(f.names[14].ansi_bytes,b'Kept')
        self.assertEqual(f.name_fields[14]['metadata_category'],5)

    def test_missing_guard_normal_and_wrong_sample_do_not_fabricate_values(self):
        f=UpgradeRefreshFrame(Sink());o=observed(root=dword(0x100,0x1000,False))
        p=f.advance(o);self.assertEqual(p.needed,('root','returned'))
        self.assertNotIn('inventory',f.reads)
        self.assertTrue(finish(f,observed(root=dword(0x100,0x2000))).complete)
        self.assertEqual(f.reads['root']['result'],0x1000)
        g=UpgradeRefreshFrame(Sink())
        with self.assertRaises(ValueError):g.advance(observed(root=dword(0x200,0x1000)))
        self.assertTrue(finish(g,observed()).complete)

    def test_wrapped_item_key_and_distinct_name_kind_byte(self):
        o=observed();o.slots[14]=filled(base=0xffffffff,first=2,fresh=19)
        f=UpgradeRefreshFrame(Sink());self.assertTrue(finish(f,o).complete)
        self.assertEqual(f.item_id,1);self.assertEqual(f.grade,9)

    def test_caption_concat_and_row_cleanup_gaps_preserve_one_row(self):
        for field,expected in (('caption_returned',['',[]]),('concat_returned',['0',[]]),('row_cleanup_returned',['0',['Item (+9)']])):
            sink=Sink();o=observed();o.slots[14]=replace(filled(),**{field:False})
            f=UpgradeRefreshFrame(sink);p=f.advance(o)
            self.assertEqual(p.needed,(14,field));self.assertEqual(sink.rows,[expected])
            self.assertTrue(finish(f,observed()).complete);self.assertEqual(len(sink.rows),1)
            self.assertEqual(sink.events.count('add'),1)

    def test_empty_slot_does_not_read_name_and_offsets_are_fresh_per_slot(self):
        o=observed();o.slots[14]=replace(o.slots[15],record=dword(0x4000+0x20+14*4,0),name={})
        o.slots[15]=UpgradeRefreshSlot(0x24,dword(0x4000+0x24+15*4,0))
        f=UpgradeRefreshFrame(Sink());self.assertTrue(finish(f,o).complete)
        self.assertNotIn(14,f.names)
        self.assertIn(((15,'record'),0x4000+0x24+15*4,32),f.requests)

    def test_deleted_pending_row_and_cancel_never_mutate_replacement(self):
        sink=Sink();f=UpgradeRefreshFrame(sink);o=observed();o.slots[14]=replace(filled(),concat_returned=False)
        f.advance(o);sink.rows[:]=[['replacement',[]]]
        p=f.advance(observed());self.assertTrue(p.done);self.assertFalse(p.complete)
        self.assertEqual(sink.rows,[['replacement',[]]])
        g=UpgradeRefreshFrame(Sink());p=g.cancel('profile');self.assertIs(g.advance(observed()),p)


if __name__=='__main__':unittest.main()
