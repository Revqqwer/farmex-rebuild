import unittest
from dataclasses import replace
from quest_collection import QuestCollection,QuestVectorHeader as Header
from quest_record import QuestRecord
from quest_row import QuestRowSink,QuestRow,QuestRowObservation
from quest_list_emit import QuestListFrame,QuestListObservation as Observation,QuestNpcSink


def rec(index=71,npc=b'NPC',display=b'Quest'):
    return QuestRecord(index,0x4000,b'a',15,5,display,npc)


def setup(records):
    collection=QuestCollection(tuple(records),Header(0x1000,0x1000+28*len(records)))
    rows=QuestRowSink();npcs=QuestNpcSink(('HEPSI',))
    return collection,rows,npcs,QuestListFrame(collection,rows,npcs)


def capture(count=1,contains=False):
    from quest_row import QuestRowFrame
    row=QuestRowObservation({label:True for label,_ in QuestRowFrame.STEPS},1254)
    return Observation({i:row for i in range(count)},
        {(i,label):True for i in range(count) for label in ('contains','npc_convert','npc_add','npc_cleanup')},
        {i:contains for i in range(count)},1254)


class QuestListTests(unittest.TestCase):
    def test_rows_use_collection_index_and_preserve_existing_npc_baseline(self):
        c,rows,npcs,f=setup([rec(),rec(900,b'B')])
        p=f.advance(capture(2))
        self.assertTrue(p.complete);self.assertFalse(p.sort_verified)
        self.assertEqual(rows.rows,(QuestRow('0',('5','Quest')),QuestRow('1',('5','Quest'))))
        self.assertEqual(npcs.items,('HEPSI','NPC','B'))

    def test_no_containment_guess_from_existing_unicode_text(self):
        c,rows,npcs,f=setup([rec(npc=b'HEPSI')])
        p=f.advance(capture(contains=False))
        self.assertTrue(p.complete);self.assertEqual(npcs.items,('HEPSI','HEPSI'))

    def test_containment_true_skips_conversion_and_add(self):
        c,rows,npcs,f=setup([rec()]);o=capture(contains=True)
        o=replace(o,normal_returns={(0,'contains'):True},code_page=None)
        self.assertTrue(f.advance(o).complete)
        self.assertEqual(npcs.items,('HEPSI',))

    def test_row_normal_return_precedes_fresh_npc_read(self):
        c,rows,npcs,f=setup([rec()]);o=capture()
        row=o.rows[0];receipts=dict(row.normal_returns);receipts['epilogue']=False
        p=f.advance(replace(o,rows={0:replace(row,normal_returns=receipts)}))
        self.assertFalse(p.complete);self.assertEqual(f.calls,[])
        c.records=(rec(npc=b'Changed'),)
        self.assertTrue(f.advance(o).complete)
        self.assertEqual(npcs.items,('HEPSI','Changed'))

    def test_count_is_fresh_after_each_iteration(self):
        c,rows,npcs,f=setup([rec()]);o=capture(2)
        normal=dict(o.normal_returns);normal[(0,'npc_cleanup')]=False
        p=f.advance(replace(o,normal_returns=normal))
        self.assertEqual(p.needed,(0,'npc_cleanup'))
        c.records+=(rec(99,b'B'),);c.header=Header(0x1000,0x1038)
        self.assertTrue(f.advance(o).complete)
        self.assertEqual(len(rows.rows),2);self.assertEqual(npcs.items,('HEPSI','NPC','B'))

    def test_npc_add_prefix_survives_cleanup_gap_without_duplicate(self):
        c,rows,npcs,f=setup([rec()]);o=capture()
        normal=dict(o.normal_returns);normal[(0,'npc_cleanup')]=None
        self.assertFalse(f.advance(replace(o,normal_returns=normal)).complete)
        self.assertEqual(npcs.items,('HEPSI','NPC'))
        self.assertTrue(f.advance(Observation(normal_returns={(0,'npc_cleanup'):True})).complete)
        self.assertEqual(npcs.items,('HEPSI','NPC'));self.assertEqual(len(rows.rows),1)

    def test_helper_normal_and_contains_result_are_independent(self):
        c,rows,npcs,f=setup([rec()]);o=capture()
        p=f.advance(replace(o,npc_contains={}))
        self.assertEqual(p.needed,(0,'contains_AL'))
        self.assertEqual(npcs.items,('HEPSI',))
        self.assertFalse(f.advance(replace(o,normal_returns={})).complete)
        self.assertEqual(len([v for v in f.calls if v[0]=='00467d90']),1)
        self.assertTrue(f.advance(o).complete)

    def test_null_begin_ignores_unreachable_bad_end(self):
        c,rows,npcs,f=setup([]);c.header=Header(0,object())
        self.assertTrue(f.advance().complete);self.assertEqual(rows.rows,())

    def test_missing_record_for_raw_unsigned_extent_stays_incomplete(self):
        c,rows,npcs,f=setup([]);c.header=Header(0x1000,0xfe4)
        p=f.advance();self.assertFalse(p.complete)
        self.assertEqual(p.needed,(0,'owned_record'));self.assertEqual(rows.rows,())

    def test_external_npc_writer_is_not_overwritten(self):
        c,rows,npcs,f=setup([rec()]);o=capture()
        f.advance(replace(o,npc_contains={}))
        npcs.items=('external',)
        self.assertEqual(f.advance(o).status,'npc_sink_conflict')
        self.assertEqual(npcs.items,('external',))

    def test_npc_conversion_requires_codepage_without_readding_row(self):
        c,rows,npcs,f=setup([rec(npc=b'\xdd',display=b'')]);o=capture()
        p=f.advance(replace(o,code_page=None))
        self.assertEqual(p.needed,(0,'code_page'))
        self.assertEqual(npcs.items,('HEPSI',));self.assertEqual(len(rows.rows),1)
        self.assertTrue(f.advance(o).complete)
        self.assertEqual(npcs.items,('HEPSI','\u0130'));self.assertEqual(len(rows.rows),1)

    def test_empty_npc_needs_no_codepage_and_is_not_assumed_contained(self):
        c,rows,npcs,f=setup([rec(npc=b'',display=b'')]);o=capture()
        self.assertTrue(f.advance(replace(o,code_page=None)).complete)
        self.assertEqual(npcs.items,('HEPSI',''))

    def test_containment_false_is_not_a_normal_return_receipt(self):
        c,rows,npcs,f=setup([rec()]);o=capture()
        p=f.advance(replace(o,normal_returns={}))
        self.assertEqual(p.needed,(0,'contains'))
        self.assertEqual(npcs.items,('HEPSI',))

    def test_finished_emission_remains_sort_pending_and_is_idempotent(self):
        c,rows,npcs,f=setup([rec()]);p=f.advance(capture())
        baseline=(rows.rows,rows.revision,npcs.items,npcs.revision)
        self.assertEqual(p.status,'rows_and_npcs_emitted_sort_pending')
        self.assertIs(f.advance(),p)
        self.assertEqual((rows.rows,rows.revision,npcs.items,npcs.revision),baseline)


if __name__=='__main__':unittest.main()
