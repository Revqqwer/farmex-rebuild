import unittest
from dataclasses import replace
from quest_collection import QuestCollection
from quest_record import QuestRecord
from quest_row import QuestRow
from quest_details import QuestDetailsFrame,QuestDetailsState,QuestDetailsObservation as Observation


def rec(level=33,display=b'Quest B',npc=b'NPC B'):
    return QuestRecord(999,0x4000,b'a',15,level,display,npc)


def setup(*,selected=0,caption='1',owned=True):
    collection=QuestCollection((rec(5,b'Quest A',b'NPC A'),rec()))
    state=QuestDetailsState(('Old0','Old1'),(QuestRow('old',('value',)),))
    f=QuestDetailsFrame(collection,state,(QuestRow(caption),),selected,use_owned_scalar_model=owned)
    return collection,state,f


def capture(**changes):
    fields=dict(normal_returns={label:True for label,_ in QuestDetailsFrame.STEPS},
                code_pages={name:1254 for name in ('display','npc','task','reward')})
    fields.update(changes);return Observation(**fields)


class QuestDetailsTests(unittest.TestCase):
    def test_headers_and_four_rows_use_caption_record_index(self):
        c,s,f=setup();p=f.advance(capture())
        self.assertTrue(p.complete);self.assertEqual(p.record_index,1)
        self.assertEqual(s.headings,('Level : 33','Quest B'))
        self.assertEqual(s.rows,(QuestRow('NPC:',('NPC B',)),QuestRow('-',('Görev',)),QuestRow(),QuestRow('-',('Ödül',))))
        self.assertEqual([offset for _,offset,_,_ in p.reads],[0x10,0x14,0x18])

    def test_negative_selection_preserves_headers_and_rows(self):
        c,s,f=setup(selected=-1);before=(s.headings,s.rows,s.revision)
        p=f.advance(Observation({'selection':True,'epilogue':True}))
        self.assertEqual((p.complete,p.status,p.reads),(True,'no_selection',()))
        self.assertEqual((s.headings,s.rows,s.revision),before)

    def test_invalid_caption_does_not_become_zero(self):
        c,s,f=setup(caption='bad');p=f.advance(capture())
        self.assertEqual(p.status,'needs_native_StrToInt_exception_path')
        self.assertEqual(s.headings,('Old0','Old1'));self.assertEqual(s.rows[0].caption,'old')

    def test_negative_parsed_index_is_not_negative_selection(self):
        c,s,f=setup(caption='-1');p=f.advance(capture())
        self.assertEqual(p.record_index,0xffffffff)
        self.assertEqual(p.needed,('owned_record',0xffffffff));self.assertFalse(p.complete)

    def test_first_header_is_written_before_cleanups_and_row_clear(self):
        c,s,f=setup();o=capture();normal=dict(o.normal_returns);normal['level_heading_cleanup']=False
        p=f.advance(replace(o,normal_returns=normal))
        self.assertEqual(p.needed,('level_heading_cleanup',))
        self.assertEqual(s.headings,('Level : 33','Old1'));self.assertEqual(s.rows[0].caption,'old')
        self.assertTrue(f.advance(o).complete)

    def test_second_header_cleanup_still_precedes_details_clear(self):
        c,s,f=setup();o=capture();normal=dict(o.normal_returns);normal['display_cleanup']=False
        f.advance(replace(o,normal_returns=normal))
        self.assertEqual(s.headings,('Level : 33','Quest B'));self.assertEqual(s.rows[0].caption,'old')
        self.assertTrue(f.advance(o).complete);self.assertEqual(len(s.rows),4)

    def test_missing_display_conversion_keeps_first_header_and_old_rows(self):
        c,s,f=setup();o=capture(code_pages={})
        p=f.advance(o);self.assertEqual(p.needed,('code_page_or_unicode','display'))
        self.assertEqual(s.headings,('Level : 33','Old1'));self.assertEqual(s.rows[0].caption,'old')
        self.assertTrue(f.advance(capture()).complete)

    def test_missing_npc_conversion_keeps_cleared_list_and_npc_caption(self):
        c,s,f=setup();o=capture(code_pages={'display':1254})
        p=f.advance(o);self.assertEqual(p.needed,('code_page_or_unicode','npc'))
        self.assertEqual(s.rows,(QuestRow('NPC:'),))
        self.assertTrue(f.advance(capture()).complete)
        self.assertEqual(len(s.rows),4)

    def test_turkish_literals_need_their_own_explicit_conversion(self):
        c,s,f=setup();o=capture(code_pages={'display':1254,'npc':1254})
        p=f.advance(o);self.assertEqual(p.needed,('code_page_or_unicode','task'))
        self.assertEqual(s.rows,(QuestRow('NPC:',('NPC B',)),QuestRow('-')))
        p=f.advance(capture(code_pages={},unicode_values={'task':'Görev','reward':'Ödül'}))
        self.assertTrue(p.complete);self.assertEqual(s.rows[3],QuestRow('-',('Ödül',)))

    def test_record_fields_are_fresh_after_prior_cleanup(self):
        c,s,f=setup();o=capture();normal=dict(o.normal_returns);normal['caption_cleanup']=False
        f.advance(replace(o,normal_returns=normal));c.records=(c.records[0],rec(7,b'New',b'Fresh'))
        normal=dict(o.normal_returns);normal['level_number_cleanup']=False
        f.advance(replace(o,normal_returns=normal));c.records=(c.records[0],rec(8,b'Newer',b'Latest'))
        p=f.advance(o);self.assertTrue(p.complete)
        self.assertEqual(s.headings,('Level : 7','Newer'))
        self.assertEqual(s.rows[0],QuestRow('NPC:',('Latest',)))

    def test_scalar_returns_and_normal_receipts_are_independent(self):
        c,s,f=setup(owned=False);o=capture(caption_parse_dword=1,level_unicode='33')
        normal=dict(o.normal_returns);normal['caption_parse']=False
        p=f.advance(replace(o,normal_returns=normal));self.assertEqual(p.needed,('caption_parse',))
        self.assertTrue(f.advance(o).complete)

    def test_invalid_codepage_retry_keeps_known_heading_prefix(self):
        c,s,f=setup();o=capture(code_pages={'display':0})
        with self.assertRaises(ValueError):f.advance(o)
        self.assertEqual(s.headings,('Level : 33','Old1'))
        self.assertTrue(f.advance(capture()).complete)

    def test_null_ansi_is_not_silently_empty(self):
        c,s,f=setup();c.records=(c.records[0],rec(display=None))
        with self.assertRaises(ValueError):f.advance(capture())
        self.assertEqual(s.headings,('Level : 33','Old1'))

    def test_blank_row_is_preserved_before_reward_row_and_cleanup_gap(self):
        c,s,f=setup();o=capture();normal=dict(o.normal_returns);normal['reward_caption_convert']=False
        p=f.advance(replace(o,normal_returns=normal))
        self.assertFalse(p.complete);self.assertEqual(s.rows[2:],(QuestRow(),QuestRow()))
        self.assertTrue(f.advance(o).complete);self.assertEqual(s.rows[2],QuestRow())

    def test_foreign_details_edit_is_not_overwritten(self):
        c,s,f=setup();f.advance();s.headings=('foreign','change')
        self.assertEqual(f.advance(capture()).status,'details_state_conflict')
        self.assertEqual(f.advance(capture()).status,'details_state_conflict')

    def test_terminal_resume_is_idempotent_and_never_changes_collection(self):
        c,s,f=setup();before=(c.records,c.header,c.revision)
        p=f.advance(capture());snapshot=(s.headings,s.rows,s.revision)
        self.assertIs(f.advance(),p);self.assertEqual((s.headings,s.rows,s.revision),snapshot)
        self.assertEqual((c.records,c.header,c.revision),before)


if __name__=='__main__':unittest.main()
