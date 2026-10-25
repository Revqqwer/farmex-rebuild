import unittest
from dataclasses import replace
from quest_collection import QuestCollection,QuestVectorHeader as Header
from quest_record import QuestRecord
from quest_row import QuestRow,QuestRowSink,QuestRowFrame,QuestRowObservation
from quest_npc_filter import QuestNpcFilterFrame,QuestNpcFilterObservation as Observation


def rec(npc=b'A',level=5,name=b'Quest'):
    return QuestRecord(900,0x4000,b'a',15,level,name,npc)


def setup(records,selection=1,**kwargs):
    c=QuestCollection(tuple(records),Header(0x1000,0x1000+len(records)*28))
    rows=QuestRowSink((QuestRow('old'),))
    return c,rows,QuestNpcFilterFrame(c,rows,selection,('HEPSI','A','B'),**kwargs)


def capture(count=3,**changes):
    normal={label:True for label,_ in QuestNpcFilterFrame.PREFIX}
    normal.update({('npc_compare',i):True for i in range(count)})
    normal.update({label:True for label in ('sort_returned','selected_ansi_cleanup','epilogue')})
    row=QuestRowObservation({label:True for label,_ in QuestRowFrame.STEPS},1254)
    fields=dict(normal_returns=normal,code_page=1254,hepsi_equal=False,
                npc_equal={i:True for i in range(count)},rows={i:row for i in range(count)},sort_permutation=tuple(range(count)))
    fields.update(changes);return Observation(**fields)


class QuestNpcFilterTests(unittest.TestCase):
    def test_specific_npc_keeps_collection_caption_and_numeric_level_sort(self):
        c,rows,f=setup([rec(b'B'),rec(b'A',80,b'High'),rec(b'A',5,b'Low')],equality_mode='owned_bytes',sort_mode='owned')
        before=(c.records,c.header,c.revision);p=f.advance(capture())
        self.assertTrue(p.complete)
        self.assertEqual(rows.rows,(QuestRow('2',('5','Low')),QuestRow('1',('80','High'))))
        self.assertEqual((c.records,c.header,c.revision),before)

    def test_all_branch_uses_selected_text_not_index_and_skips_npc_comparisons(self):
        c,rows,f=setup([rec(b'B'),rec(b'A')],selection=0,equality_mode='owned_bytes',sort_mode='owned')
        o=capture(2);normal={k:v for k,v in o.normal_returns.items() if not isinstance(k,tuple)}
        p=f.advance(replace(o,normal_returns=normal,npc_equal={}))
        self.assertTrue(p.complete);self.assertTrue(p.all_npcs);self.assertEqual(len(rows.rows),2)
        self.assertFalse(any(isinstance(label,tuple) for _,label in p.calls))

    def test_index_zero_is_not_assumed_to_mean_all(self):
        c,rows,_=setup([rec(b'A'),rec(b'B')])
        f=QuestNpcFilterFrame(c,rows,0,('B',),equality_mode='owned_bytes',sort_mode='owned')
        p=f.advance(capture(2));self.assertTrue(p.complete);self.assertFalse(p.all_npcs)
        self.assertEqual(rows.rows[0].caption,'1')

    def test_selection_minus_one_clears_rows_before_unresolved_native_index(self):
        c,rows,f=setup([rec()],selection=-1)
        p=f.advance(capture(1))
        self.assertEqual((p.status,p.complete,rows.rows),('unresolved_native_item_index',False,()))
        self.assertEqual(len(c.records),1)

    def test_callback_selection_return_precedes_clear(self):
        c,rows,f=setup([rec()]);o=capture(1);normal=dict(o.normal_returns);normal['selection']=False
        p=f.advance(replace(o,normal_returns=normal))
        self.assertEqual(p.needed,('selection',));self.assertEqual(rows.rows,(QuestRow('old'),))

    def test_nonempty_selection_requires_codepage_or_explicit_ansi(self):
        c,rows,f=setup([rec()],sort_mode='owned')
        p=f.advance(replace(capture(1),code_page=None))
        self.assertEqual(p.needed,('code_page_or_selected_ansi',));self.assertEqual(rows.rows,())
        self.assertTrue(f.advance(replace(capture(1),selected_ansi=b'A',code_page=None)).complete)

    def test_hepsi_compare_result_is_frozen_but_not_used_before_cleanup(self):
        c,rows,f=setup([rec()],sort_mode='owned');o=capture(1,hepsi_equal=True)
        normal=dict(o.normal_returns);normal['hepsi_cleanup']=False
        p=f.advance(replace(o,normal_returns=normal));self.assertEqual(p.needed,('hepsi_cleanup',))
        self.assertEqual(rows.rows,())
        p=f.advance(replace(o,hepsi_equal=False))
        self.assertTrue(p.complete);self.assertTrue(p.all_npcs)

    def test_captured_npc_comparison_does_not_fall_back_to_own_equality(self):
        c,rows,f=setup([rec()],sort_mode='owned')
        p=f.advance(capture(1,npc_equal={}))
        self.assertEqual(p.needed,(('npc_equal',0),));self.assertEqual(rows.rows,())
        self.assertTrue(f.advance(capture(1,npc_equal={0:False})).complete)
        self.assertEqual(rows.rows,())

    def test_own_byte_comparison_is_case_sensitive_and_not_substring(self):
        c,rows,f=setup([rec(b'a'),rec(b'AA'),rec(b'A')],equality_mode='owned_bytes',sort_mode='owned')
        self.assertTrue(f.advance(capture()).complete)
        self.assertEqual([r.caption for r in rows.rows],['2'])

    def test_fresh_count_observes_append_after_pending_row_helper(self):
        c,rows,f=setup([rec()],equality_mode='owned_bytes',sort_mode='owned');o=capture(2)
        row=o.rows[0];normal=dict(row.normal_returns);normal['epilogue']=False
        p=f.advance(replace(o,rows={0:replace(row,normal_returns=normal)}))
        self.assertFalse(p.complete);c.records+=(rec(level=7),);c.header=Header(0x1000,0x1038)
        self.assertTrue(f.advance(o).complete);self.assertEqual(len(rows.rows),2)

    def test_row_values_are_read_after_match_result_is_known(self):
        c,rows,f=setup([rec(level=80)],sort_mode='owned');o=capture(1,npc_equal={})
        f.advance(o);c.records=(rec(level=5,name=b'New'),)
        self.assertTrue(f.advance(capture(1)).complete)
        self.assertEqual(rows.rows,(QuestRow('0',('5','New')),))

    def test_final_cleanup_gap_keeps_sorted_rows_without_repeating_sort(self):
        c,rows,f=setup([rec()],equality_mode='owned_bytes',sort_mode='owned');o=capture(1)
        normal=dict(o.normal_returns);normal['selected_ansi_cleanup']=False
        p=f.advance(replace(o,normal_returns=normal));revision=rows.revision
        self.assertEqual(p.needed,('selected_ansi_cleanup',))
        self.assertTrue(f.advance(o).complete);self.assertEqual(rows.revision,revision)

    def test_invalid_display_codepage_can_resume_known_row_prefix(self):
        c,rows,f=setup([rec(name=b'Name')],equality_mode='owned_bytes',sort_mode='owned');o=capture(1)
        bad=replace(o.rows[0],code_page=0)
        with self.assertRaises(ValueError):f.advance(replace(o,rows={0:bad}))
        self.assertEqual(rows.rows,(QuestRow('0',('5',)),))
        self.assertTrue(f.advance(o).complete);self.assertEqual(len(rows.rows),1)

    def test_external_row_edit_stays_conflict(self):
        c,rows,f=setup([rec()]);f.advance();rows.rows=(QuestRow('external'),)
        self.assertEqual(f.advance(capture(1)).status,'row_sink_conflict')
        self.assertEqual(f.advance(capture(1)).status,'row_sink_conflict')


if __name__=='__main__':unittest.main()
