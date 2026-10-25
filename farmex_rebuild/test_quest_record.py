import unittest
from dataclasses import replace
from quest_candidate import QuestCandidatePlan
from quest_record import (QuestStringFrame,QuestStringObservation as StringObservation,
                          QuestRecordFrame,QuestRecordObservation as Observation,EXCLUDED_NPC,
                          QuestPreparedFrame,QuestPreparedObservation)


def string(text,count=15,**changes):
    values=dict(storage_dword=1,bad_read_dword=0,captured=(text+b'\0').ljust(count,b'\0'),helper_returned=True)
    values.update(changes);return StringObservation(**values)


def capture(**changes):
    values=dict(display_key=22,display_lookup_eax=0x2000,fresh_minimum=80,npc_key=33,npc_lookup_eax=0x3000,npc_not_excluded=True)
    labels=('display_key','display_lookup_eax','display_string_span','script_string_span','fresh_minimum',
            'display_assignment_returned','npc_key','npc_lookup_eax','npc_helper','npc_assignment_span',
            'npc_comparison','npc_comparison_cleanup')
    fields=dict(values=values,normal_returns={n:True for n in labels},
                strings={'display':string(b'Quest A',50),'script':string(b'quest.lua'),'npc':string(b'NPC')})
    fields.update(changes);return Observation(**fields)


def candidate():return QuestCandidatePlan(True,'eligible_for_name_stage',True,source_index=7,pointer=0x1000)


class QuestStringTests(unittest.TestCase):
    def test_three_inline_layouts_do_not_read_pointer(self):
        for kind,base,offset,count in (('display',0x2000,0x10,50),('script',0x1000,0x38,15),('npc',0x3000,4,15)):
            with self.subTest(kind=kind):
                p=QuestStringFrame(kind,base).advance(string(b'Name',count,pointer_dword=object()))
                self.assertEqual((p.complete,p.ansi_bytes,p.copy_address,p.copy_count),(True,b'Name',base+offset,count))
                self.assertEqual(len(p.reads),1)

    def test_indirect_count_is_storage_not_strlen(self):
        p=QuestStringFrame('script',0x1000).advance(string(b'hi',16,storage_dword=16,pointer_dword=0x8000))
        self.assertEqual((p.ansi_bytes,p.copy_count,p.copy_address),(b'hi',16,0x8000))
        self.assertEqual([r[2] for r in p.reads],['storage','pointer'])

    def test_signed_highbit_storage_selects_inline(self):
        for storage in (0x80000000,0xffffffff):
            p=QuestStringFrame('script',0x1000).advance(string(b'x',storage_dword=storage,pointer_dword=object()))
            self.assertEqual((p.copy_count,p.copy_address,p.storage_dword),(15,0x1038,storage))

    def test_zero_base_is_not_an_empty_lookup_shortcut(self):
        f=QuestStringFrame('display',0)
        self.assertEqual(f.advance().needed,('storage_dword',))
        p=f.advance(StringObservation(storage_dword=0,bad_read_dword=1,helper_returned=True))
        self.assertEqual((p.ansi_bytes,p.reads[0][0],p.copy_address),(b'',0x20,0x10))

    def test_bad_read_bypasses_copy_even_for_oversized_count(self):
        p=QuestStringFrame('script',0x1000).advance(StringObservation(storage_dword=513,pointer_dword=0,
                                                                   bad_read_dword=1,captured=object(),helper_returned=True))
        self.assertEqual((p.complete,p.ansi_bytes),(True,b''))

    def test_overflow_and_unterminated_source_paths_are_unresolved(self):
        p=QuestStringFrame('script',0x1000).advance(StringObservation(storage_dword=513,pointer_dword=1,bad_read_dword=0))
        self.assertEqual((p.complete,p.status),(False,'unresolved_source_stack_overflow'))
        p=QuestStringFrame('script',0x1000).advance(StringObservation(storage_dword=512,pointer_dword=1,
                                                                   bad_read_dword=0,captured=b'x'*512,helper_returned=True))
        self.assertEqual((p.complete,p.status),(False,'unresolved_unterminated_source_buffer'))

    def test_captured_bytes_and_nul_freeze_while_helper_return_waits(self):
        f=QuestStringFrame('script',0x1000)
        p=f.advance(string(b'a\0ignored',helper_returned=None))
        self.assertEqual(p.needed,('helper_returned',))
        p=f.advance(StringObservation(helper_returned=True,captured=object()))
        self.assertEqual(p.ansi_bytes,b'a')

    def test_short_capture_can_be_completed_without_replaying_storage(self):
        f=QuestStringFrame('script',0x1000)
        self.assertEqual(f.advance(StringObservation(1,bad_read_dword=0,captured=b'x')).needed,('captured_bytes',15))
        p=f.advance(StringObservation(captured=b'x\0'+b'\0'*13,helper_returned=True))
        self.assertEqual(p.ansi_bytes,b'x')


class QuestRecordTests(unittest.TestCase):
    def test_seven_fields_preserve_source_storage_and_fresh_level(self):
        p=QuestRecordFrame(candidate()).advance(capture())
        self.assertEqual((p.complete,p.eligible_for_append,p.status),(True,True,'ready_for_append'))
        self.assertEqual(p.record.fields(),{0:7,4:0x1000,8:b'quest.lua',0xc:1,0x10:80,0x14:b'Quest A',0x18:b'NPC'})
        self.assertNotEqual(p.record.script_storage_dword,len(p.record.script_bytes))

    def test_fresh_minimum_is_not_the_earlier_candidate_filter_byte(self):
        f=QuestRecordFrame(candidate());o=capture();returns=dict(o.normal_returns);del returns['fresh_minimum']
        self.assertEqual(f.advance(replace(o,normal_returns=returns)).needed,('normal','fresh_minimum'))
        values=dict(o.values);values['fresh_minimum']=99
        p=f.advance(replace(o,values=values))
        self.assertEqual(p.record.minimum_dword,99)

    def test_completed_script_is_not_read_again_at_later_scalar_gap(self):
        f=QuestRecordFrame(candidate());o=capture();returns=dict(o.normal_returns);del returns['fresh_minimum']
        f.advance(replace(o,normal_returns=returns))
        strings=dict(o.strings);strings['script']=object()
        p=f.advance(replace(o,strings=strings))
        self.assertEqual(p.record.script_bytes,b'quest.lua')

    def test_missing_npc_lookup_returns_source_empty_literal_without_string_reads(self):
        o=capture();values=dict(o.values);values['npc_lookup_eax']=0;strings=dict(o.strings);strings['npc']=object()
        p=QuestRecordFrame(candidate()).advance(replace(o,values=values,strings=strings))
        self.assertEqual(p.record.npc_bytes,b'')
        self.assertNotIn('npc',dict(p.string_reads))

    def test_display_lookup0_still_needs_storage_and_guard_observations(self):
        o=capture();values=dict(o.values);values['display_lookup_eax']=0;strings=dict(o.strings);del strings['display']
        f=QuestRecordFrame(candidate());p=f.advance(replace(o,values=values,strings=strings))
        self.assertEqual(p.needed,('string','display','needs_observation',('storage_dword',)))
        strings['display']=StringObservation(storage_dword=0,bad_read_dword=1,helper_returned=True)
        p=f.advance(replace(o,strings=strings))
        self.assertEqual((p.record.display_bytes,dict(p.string_reads)['display'][0][0]),(b'',0x20))

    def test_excluded_npc_still_waits_for_comparison_cleanup(self):
        o=capture();values=dict(o.values);values['npc_not_excluded']=False;returns=dict(o.normal_returns);del returns['npc_comparison_cleanup']
        strings=dict(o.strings);strings['npc']=string(EXCLUDED_NPC,len(EXCLUDED_NPC)+1,
            storage_dword=len(EXCLUDED_NPC)+1,pointer_dword=0x5000)
        f=QuestRecordFrame(candidate());p=f.advance(replace(o,values=values,normal_returns=returns,strings=strings))
        self.assertFalse(p.complete);self.assertIsNotNone(p.record)
        self.assertEqual(p.needed,('normal','npc_comparison_cleanup'))
        p=f.advance(Observation(normal_returns={'npc_comparison_cleanup':True}))
        self.assertEqual((p.status,p.complete,p.eligible_for_append),('npc_excluded',True,False))

    def test_unknown_comparison_does_not_assume_true_from_bytes(self):
        o=capture();values=dict(o.values);del values['npc_not_excluded']
        p=QuestRecordFrame(candidate()).advance(replace(o,values=values))
        self.assertEqual(p.needed,('value','npc_not_excluded'))
        self.assertFalse(p.eligible_for_append)

    def test_classified_candidate_and_completed_record_are_immutable_boundaries(self):
        for c in (replace(candidate(),eligible=False),replace(candidate(),complete=False),replace(candidate(),pointer=0)):
            with self.assertRaises(ValueError):QuestRecordFrame(c)
        f=QuestRecordFrame(candidate());p=f.advance(capture())
        self.assertIs(f.advance(object()),p)

    def test_rejected_candidate_never_consumes_record_or_string_input(self):
        from quest_candidate import QuestCandidateObservation
        f=QuestPreparedFrame(7,21)
        p=f.advance(QuestPreparedObservation(QuestCandidateObservation({'lookup_eax':0},{'lookup_eax':True}),object()))
        self.assertEqual((p.complete,p.eligible_for_append,p.status),(True,False,'candidate_rejected'))
        self.assertIsNone(f.record)

    def test_candidate_to_record_composition_preserves_accepted_filter_prefix(self):
        from test_quest_candidate import capture as candidate_capture
        f=QuestPreparedFrame(7,21)
        p=f.advance(QuestPreparedObservation(candidate_capture(),Observation()))
        self.assertEqual(p.needed,('normal','display_key'))
        p=f.advance(QuestPreparedObservation(object(),capture()))
        self.assertEqual((p.complete,p.eligible_for_append,p.record.source_index),(True,True,7))


if __name__=='__main__':unittest.main()
