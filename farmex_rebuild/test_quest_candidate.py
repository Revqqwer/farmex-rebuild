import unittest
from quest_candidate import QuestCandidateFrame,QuestCandidateObservation as Observation,resolve_quest_zone,ZONE_MATCHES


def capture(**changes):
    values=dict(lookup_eax=0x1000,zone=21,kind_not3=1,kind_not4=1,nation_gate=1,nation_value=1,nation_eax=1,
        class_gate=1,class_value=1,class_eax=1,field24=4,field30=1,
        minimum_nonzero=5,minimum_not100=5,minimum_value=5,level_eax=5,status_key=9,status_eax=0)
    values.update(changes);return Observation(values,{k:True for k in values})


class QuestCandidateTests(unittest.TestCase):
    def test_five_normalized_region_codes_first_match_and_no_match(self):
        for name,code in ZONE_MATCHES:
            p=resolve_quest_zone({n:n==name for n,c in ZONE_MATCHES})
            self.assertEqual((p.complete,p.code),(True,code))
        self.assertEqual(resolve_quest_zone({n:False for n,c in ZONE_MATCHES}).code,0)
        self.assertEqual(resolve_quest_zone({'Moradon':True,'Luferson':object()}).compared,('Moradon',))

    def test_missing_comparison_is_not_false_or_raw_zone_fallback(self):
        p=resolve_quest_zone({'Moradon':False})
        self.assertEqual((p.complete,p.needed),(False,'Luferson'))
        with self.assertRaises(ValueError):QuestCandidateFrame(0,0)

    def test_success_stops_before_names_or_display_row(self):
        p=QuestCandidateFrame(0,21).advance(capture())
        self.assertEqual((p.complete,p.eligible,p.status),(True,True,'eligible_for_name_stage'))
        self.assertEqual(p.calls[-1],('004d5244',('owned_quest_context',9),'status_eax'))
        self.assertNotIn('004d51f0',[c[0] for c in p.calls])

    def test_lookup0_short_circuits_unreached_bad_fields(self):
        p=QuestCandidateFrame(0,21).advance(Observation({'lookup_eax':0,'zone':object()},{'lookup_eax':True}))
        self.assertEqual((p.status,p.reads),('null_candidate',()))

    def test_region_and_both_kind_rejections_are_independent(self):
        for fields,status in (({'zone':1},'zone_mismatch'),({'kind_not3':3},'kind3'),({'kind_not4':4},'kind4')):
            with self.subTest(status=status):self.assertEqual(QuestCandidateFrame(0,21).advance(capture(**fields)).status,status)
        p=QuestCandidateFrame(0,21).advance(capture(kind_not3=4,kind_not4=3))
        self.assertTrue(p.eligible)

    def test_nation_wildcard_skips_fresh_second_byte_and_helper(self):
        o=capture(nation_gate=3,nation_value=object(),nation_eax=object())
        p=QuestCandidateFrame(0,21).advance(o)
        self.assertTrue(p.eligible)
        self.assertNotIn('nation_value',[r[2] for r in p.reads])
        self.assertNotIn('00462690',[c[0] for c in p.calls])

    def test_nation_compares_full_helper_dword_not_low_byte(self):
        self.assertEqual(QuestCandidateFrame(0,21).advance(capture(nation_eax=0x10000001)).status,'nation_mismatch')
        self.assertTrue(QuestCandidateFrame(0,21).advance(capture(nation_gate=2,nation_value=1,nation_eax=1)).eligible)

    def test_class_wildcard_and_helper_low_al(self):
        self.assertTrue(QuestCandidateFrame(0,21).advance(capture(class_gate=5,class_value=object(),class_eax=object())).eligible)
        self.assertTrue(QuestCandidateFrame(0,21).advance(capture(class_eax=0x10000001)).eligible)
        self.assertEqual(QuestCandidateFrame(0,21).advance(capture(class_eax=2)).status,'class_mismatch')

    def test_field24_field30_and_minimum_early_gates(self):
        for fields,status in (({'field24':3},'field24_not4'),({'field30':0},'field30_zero'),
                              ({'minimum_nonzero':0},'minimum_zero'),({'minimum_not100':100},'minimum100')):
            with self.subTest(status=status):self.assertEqual(QuestCandidateFrame(0,21).advance(capture(**fields)).status,status)

    def test_three_fresh_minimum_reads_and_signed_level_boundary(self):
        p=QuestCandidateFrame(0,21).advance(capture(minimum_nonzero=1,minimum_not100=99,minimum_value=5,level_eax=5))
        self.assertTrue(p.eligible)
        self.assertEqual([r[3] for r in p.reads if r[0]==0x1005],[1,99,5])
        self.assertEqual(QuestCandidateFrame(0,21).advance(capture(level_eax=4)).status,'level_too_low')
        self.assertEqual(QuestCandidateFrame(0,21).advance(capture(level_eax=0xffffffff)).status,'level_too_low')

    def test_status_uses_low_al_and_no_default_for_unknown(self):
        self.assertEqual(QuestCandidateFrame(0,21).advance(capture(status_eax=0x10000002)).status,'status2')
        o=capture();values=dict(o.values);del values['status_eax']
        p=QuestCandidateFrame(0,21).advance(Observation(values,o.normal_returns))
        self.assertEqual((p.complete,p.needed),(False,('value','status_eax')))

    def test_reached_values_freeze_later_repeated_read_is_fresh(self):
        f=QuestCandidateFrame(0,21);o=capture()
        returns=dict(o.normal_returns);del returns['kind_not4']
        p=f.advance(Observation(o.values,returns))
        self.assertEqual(p.needed,('normal','kind_not4'))
        later=capture(lookup_eax=0,zone=0,kind_not3=3,kind_not4=3)
        self.assertTrue(f.advance(later).eligible)
        self.assertEqual(f.pointer,0x1000)
        self.assertEqual([r[3] for r in f.final.reads if r[0]==0x101a],[1,3])

    def test_normal_receipt_and_value_gaps_do_not_duplicate_call_requests(self):
        f=QuestCandidateFrame(30000,21)
        p=f.advance();self.assertEqual(p.needed,('normal','lookup_eax'))
        p=f.advance(Observation(normal_returns={'lookup_eax':True}))
        self.assertEqual(p.needed,('value','lookup_eax'))
        p=f.advance(Observation({'lookup_eax':0}))
        self.assertEqual(len(p.calls),1)
        self.assertIs(f.advance(object()),p)

    def test_source_index_bounds_raw_byte_and_unreached_input_validation(self):
        for index in (-1,30001,True):
            with self.assertRaises(ValueError):QuestCandidateFrame(index,21)
        with self.assertRaises(ValueError):QuestCandidateFrame(0,21).advance(capture(zone=256))
        p=QuestCandidateFrame(0,21).advance(capture(zone=1,kind_not3=object()))
        self.assertEqual(p.status,'zone_mismatch')


if __name__=='__main__':unittest.main()
