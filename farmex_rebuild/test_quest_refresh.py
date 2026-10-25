import unittest
from dataclasses import replace
from collections.abc import Mapping
from quest_candidate import QuestCandidateObservation,ZONE_MATCHES
from quest_record import QuestPreparedObservation
from quest_collection import QuestCollection,QuestVectorHeader as Header
from quest_row import QuestRow,QuestRowSink
from quest_list_emit import QuestNpcSink
from quest_refresh import QuestRefreshState,QuestRefreshFrame,QuestRefreshObservation as Observation
from test_quest_candidate import capture as candidate_capture
from test_quest_record import capture as record_capture
from test_quest_collection import record, capture as append_capture
from test_quest_list_emit import capture as emission_capture


NULL=QuestPreparedObservation(QuestCandidateObservation({'lookup_eax':0},{'lookup_eax':True}))


def setup(**kwargs):
    s=QuestRefreshState(QuestCollection((record(),),Header(0x1000,0x101c,0x1038)),
                        QuestRowSink((QuestRow('old'),)),QuestNpcSink(('oldNPC',)),2)
    return s,QuestRefreshFrame(s,**kwargs)


def capture(zone='Moradon',**changes):
    normal={label:True for label,helper in QuestRefreshFrame.PREFIX if helper is not None}
    normal.update({(kind,name):True for name,_ in ZONE_MATCHES for kind in ('zone_literal','zone_compare','zone_cleanup')})
    normal.update({label:True for label in QuestRefreshFrame.TAIL});normal['sort_returned']=True
    fields=dict(normal_returns=normal,clear_header=Header(0x1000,0x1000,0x1038),
                zone_matches={name:name==zone for name,_ in ZONE_MATCHES},sort_permutation=())
    fields.update(changes);return Observation(**fields)


class TrackingNulls(Mapping):
    def __init__(self,overrides=None):self.seen=[];self.overrides=overrides or {}
    def __getitem__(self,index):
        if not 0<=index<=30000:raise KeyError(index)
        self.seen.append(index);return self.overrides.get(index,NULL)
    def __iter__(self):return iter(range(30001))
    def __len__(self):return 30001


class QuestRefreshTests(unittest.TestCase):
    def test_npc_clear_prefix_precedes_hepsi_and_other_clears(self):
        s,f=setup();o=capture();normal=dict(o.normal_returns);normal['hepsi_convert']=False
        p=f.advance(replace(o,normal_returns=normal))
        self.assertEqual(p.needed,('hepsi_convert',))
        self.assertEqual((s.npcs.items,s.rows.rows,s.collection.records),((),(QuestRow('old'),),(record(),)))

    def test_hepsi_add_is_kept_once_while_cleanup_waits(self):
        s,f=setup();o=capture(zone=None);normal=dict(o.normal_returns);normal['hepsi_cleanup']=False
        f.advance(replace(o,normal_returns=normal))
        self.assertEqual((s.npcs.items,s.npc_selected),(('HEPSI',),2))
        self.assertTrue(f.advance(o).complete)
        self.assertEqual((s.npcs.items,s.npc_selected),(('HEPSI',),0))

    def test_selection_precedes_row_clear(self):
        s,f=setup();o=capture();normal=dict(o.normal_returns);normal['rows_clear']=False
        p=f.advance(replace(o,normal_returns=normal))
        self.assertEqual((p.needed,s.npc_selected,s.rows.rows),(('rows_clear',),0,(QuestRow('old'),)))

    def test_opaque_erase_needs_post_header_and_clears_are_not_repeated(self):
        s,f=setup();o=capture(zone=None,clear_header=None)
        p=f.advance(o);self.assertEqual(p.needed,('clear_header',))
        self.assertEqual((s.rows.rows,s.collection.records),((),(record(),)))
        revisions=(s.rows.revision,s.npcs.revision)
        self.assertTrue(f.advance(replace(o,clear_header=Header(0))).complete)
        self.assertEqual(s.collection.records,())
        self.assertEqual((s.rows.revision,s.npcs.revision),revisions)

    def test_nonempty_post_erase_header_is_not_accepted_as_clear(self):
        s,f=setup();p=f.advance(capture(clear_header=Header(0x1000,0x101c)))
        self.assertEqual(p.status,'unresolved_clear_header')
        self.assertEqual(s.collection.records,(record(),))

    def test_no_zone_runs_four_cleanups_and_skips_scan_and_sort(self):
        s,f=setup();o=capture(zone=None,prepared={0:object()})
        normal=dict(o.normal_returns);normal['sort_returned']=False
        p=f.advance(replace(o,normal_returns=normal))
        self.assertEqual((p.complete,p.status,p.zone_code),(True,'locally_refreshed_no_zone',0))
        self.assertEqual((s.rows.rows,s.npcs.items),((),('HEPSI',)))
        self.assertFalse(any(helper=='00506b78' for helper,_ in p.calls))

    def test_matching_zone_is_not_used_until_literal_cleanup_returns(self):
        s,f=setup();o=capture();normal=dict(o.normal_returns);normal[('zone_cleanup','Moradon')]=False
        p=f.advance(replace(o,normal_returns=normal))
        self.assertEqual(p.needed,(('zone_cleanup','Moradon'),));self.assertIsNone(p.zone_code)
        p=f.advance(replace(o,zone_matches={'Moradon':False}))
        self.assertEqual(p.zone_code,21);self.assertEqual(p.source_index,0)
        self.assertEqual(p.status,'needs_candidate')

    def test_all_30001_lookup_indices_are_reached_including_last(self):
        s,f=setup();captures=TrackingNulls()
        p=f.advance(capture(prepared=captures))
        self.assertTrue(p.complete);self.assertEqual(p.source_index,30001)
        self.assertEqual(captures.seen,list(range(30001)))
        self.assertEqual(s.collection.records,());self.assertEqual(s.rows.rows,())

    def test_last_scan_index_can_become_first_collection_row(self):
        prepared=QuestPreparedObservation(candidate_capture(),record_capture())
        captures=TrackingNulls({30000:prepared})
        s,f=setup();o=capture(prepared=captures,appends={30000:append_capture()},
                            emission=emission_capture(),sort_permutation=(0,))
        normal=dict(o.normal_returns);normal[('candidate_cleanup',30000)]=True
        p=f.advance(replace(o,normal_returns=normal))
        self.assertTrue(p.complete)
        self.assertEqual(s.collection.records[0].source_index,30000)
        self.assertEqual(s.rows.rows,(QuestRow('0',('80','Quest A')),))
        self.assertEqual(s.npcs.items,('HEPSI','NPC'))

    def test_candidate_gap_resumes_same_index_without_repeating_clear(self):
        s,f=setup();o=capture(prepared={0:NULL})
        p=f.advance(o);self.assertEqual(p.source_index,1)
        revisions=(s.rows.revision,s.npcs.revision,s.collection.revision)
        p=f.advance(Observation())
        self.assertEqual(p.source_index,1)
        self.assertEqual((s.rows.revision,s.npcs.revision,s.collection.revision),revisions)

    def test_excluded_npc_still_requires_candidate_string_cleanup(self):
        s,f=setup();r=record_capture();values=dict(r.values);values['npc_not_excluded']=False
        prepared=QuestPreparedObservation(candidate_capture(),replace(r,values=values))
        o=capture(prepared={0:prepared})
        p=f.advance(o)
        self.assertEqual(p.needed,(('candidate_cleanup',0),));self.assertEqual(s.collection.records,())
        normal=dict(o.normal_returns);normal[('candidate_cleanup',0)]=True
        p=f.advance(replace(o,normal_returns=normal))
        self.assertEqual(p.source_index,1)

    def test_sort_return_alone_is_not_an_observed_order(self):
        s,f=setup();o=capture(prepared=TrackingNulls(),sort_permutation=None)
        p=f.advance(o);self.assertEqual(p.needed,('sort_permutation',))
        revision=s.rows.revision
        p=f.advance(Observation(normal_returns={label:True for label in f.TAIL},sort_permutation=()))
        self.assertTrue(p.complete);self.assertEqual(s.rows.revision,revision+1)

    def test_tail_gap_does_not_repeat_sort_or_clear(self):
        s,f=setup(sort_mode='owned');o=capture(prepared=TrackingNulls())
        normal=dict(o.normal_returns);normal['tail_display']=False
        p=f.advance(replace(o,normal_returns=normal));self.assertFalse(p.complete)
        revisions=(s.rows.revision,s.npcs.revision,s.collection.revision)
        self.assertTrue(f.advance(o).complete)
        self.assertEqual((s.rows.revision,s.npcs.revision,s.collection.revision),revisions)
        self.assertIn('own stable',f.final.order_policy)

    def test_external_state_conflict_stays_conflict_on_retry(self):
        s,f=setup();f.advance();s.npcs.items=('external',)
        self.assertEqual(f.advance(capture()).status,'refresh_state_conflict')
        self.assertEqual(f.advance(capture()).status,'refresh_state_conflict')
        self.assertEqual(s.npcs.items,('external',))

    def test_equal_value_sink_replacement_is_still_a_lifetime_conflict(self):
        s,f=setup();f.advance();s.rows=QuestRowSink(s.rows.rows,s.rows.revision)
        self.assertEqual(f.advance(capture()).status,'refresh_state_conflict')

    def test_invalid_display_codepage_retry_retains_append_and_row_prefix(self):
        s,f=setup();prepared=TrackingNulls({0:QuestPreparedObservation(candidate_capture(),record_capture())})
        emission=emission_capture();o=capture(prepared=prepared,appends={0:append_capture()},
                                            emission=emission,sort_permutation=(0,))
        normal=dict(o.normal_returns);normal[('candidate_cleanup',0)]=True;o=replace(o,normal_returns=normal)
        bad=replace(emission,rows={0:replace(emission.rows[0],code_page=0)})
        with self.assertRaises(ValueError):f.advance(replace(o,emission=bad))
        self.assertEqual(s.rows.rows,(QuestRow('0',('80',)),))
        self.assertEqual(len(s.collection.records),1)
        self.assertTrue(f.advance(o).complete)
        self.assertEqual(s.rows.rows,(QuestRow('0',('80','Quest A')),))
        self.assertEqual(len(s.collection.records),1)


if __name__=='__main__':unittest.main()
