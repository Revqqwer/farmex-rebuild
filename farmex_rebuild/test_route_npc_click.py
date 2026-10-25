import unittest
from dataclasses import FrozenInstanceError
from route_npc_click import NpcClickFrame,NpcClickInput,NpcValueCapture
from route_npc_click import NpcCaptureContext
from test_route_coordinate_click import Sink


def sample(name=b'Potion',third=3001,**changes):
    c=lambda value:NpcValueCapture(value,True)
    values=dict(target_gate=c(99),target_lookup=c(100),actor=c(0x1000),
                name_bytes=c(name),target_classify=c(third))
    values.update(changes)
    return NpcClickInput(**values)


class NpcClickTests(unittest.TestCase):
    def test_context_is_immutable_and_demand_specific(self):
        context=NpcCaptureContext(1,2,'name_bytes','name_bytes.value')
        with self.assertRaises(FrozenInstanceError):context.phase='actor'

    def test_provider_hold_preserves_demand_and_cannot_resurrect_cancel(self):
        frame=NpcClickFrame(Sink());before=frame.advance()
        after=frame.hold('provider unavailable')
        self.assertEqual(before.needed,after.needed);self.assertFalse(after.done)
        end=frame.cancel('profile changed');self.assertIs(frame.hold('late'),end)

    def test_three_independent_selected_ids_and_third_zero_is_user_trade(self):
        s=Sink();f=NpcClickFrame(s)
        p=f.advance(sample(third=0,trade_text=NpcValueCapture('Other player',True)))
        self.assertTrue(p.complete);self.assertEqual(s.rows,[['User Trade',['Other player','-']]])
        self.assertEqual([f.cache[k]['value'] for k in ('target_gate','target_lookup','target_classify')],[99,100,0])

    def test_missing_data_and_false_receipt_never_create_rows(self):
        s=Sink();f=NpcClickFrame(s);p=f.advance()
        self.assertEqual(p.needed,'target_gate.value');self.assertEqual(s.rows,[])
        p=f.advance(NpcClickInput(target_gate=NpcValueCapture(10,False)))
        self.assertEqual(p.needed,'target_gate.returned');self.assertEqual(s.rows,[])
        p=f.advance(NpcClickInput(target_gate=NpcValueCapture(20,True)))
        self.assertEqual(f.cache['target_gate']['value'],10);self.assertEqual(p.needed,'target_lookup.value')

    def test_first_zero_and_lookup_zero_have_distinct_outcomes_without_later_reads(self):
        for field,status in [('target_gate','no_selection'),('actor','lookup_empty')]:
            with self.subTest(field=field):
                s=Sink();f=NpcClickFrame(s);p=f.advance(sample(**{field:NpcValueCapture(0,True)},name_bytes={}))
                self.assertTrue(p.complete);self.assertEqual(p.status,status);self.assertEqual(s.rows,[])
                self.assertNotIn('name_bytes',f.cache)

    def test_name_search_priority_and_case_sensitive_substrings(self):
        cases=[(b'DC Potion Sundries','Potion'),(b'DC Sundries','DC Sundries'),
               (b'Sundries Armor','Sundries'),(b'Armor Weapon','Armor'),
               (b'Weapon Inn','Weapon'),(b'Inn','Inn Hostess'),(b'Kronil','Inn Hostess'),
               (b'otion','Potion'),(b'undries','Sundries'),(b'rmor','Armor'),(b'eapon','Weapon')]
        for name,label in cases:
            with self.subTest(name=name):
                s=Sink();p=NpcClickFrame(s).advance(sample(name))
                self.assertTrue(p.complete);self.assertEqual(s.rows,[['NPC',[label,'-']]])
        for name in (b'POTION',b'ARMOR',b'unknown',b''):
            s=Sink();p=NpcClickFrame(s).advance(sample(name))
            self.assertEqual(p.status,'name_unmatched');self.assertEqual(s.rows,[])

    def test_royal_preempts_other_names_and_requires_exact_dialog_code(self):
        for text in ('0','1','2','3','4','','01',' 1','1 ','5','\x001'):
            with self.subTest(text=text):
                s=Sink();f=NpcClickFrame(s)
                p=f.advance(sample(b'Royal National Potion',dialog_text=NpcValueCapture(text,True)))
                self.assertTrue(p.complete)
                if text in ('0','1','2','3','4'):
                    self.assertEqual(s.rows,[['NPC',['Royal National Enchanter',text]]])
                else:self.assertEqual(s.rows,[]);self.assertEqual(p.status,'dialog_rejected')

    def test_dialog_pending_has_no_row_and_consumed_name_cannot_change(self):
        s=Sink();f=NpcClickFrame(s);p=f.advance(sample(b'Royal National'))
        self.assertEqual(p.needed,'dialog_text.value');self.assertEqual(s.rows,[])
        p=f.advance(sample(b'Potion',dialog_text=NpcValueCapture('2',True)))
        self.assertTrue(p.complete);self.assertEqual(s.rows,[['NPC',['Royal National Enchanter','2']]])
        self.assertEqual(f.cache['name_bytes']['value'],b'Royal National')

    def test_trade_conversion_is_separate_after_add_caption(self):
        s=Sink();f=NpcClickFrame(s);p=f.advance(sample(third=3000))
        self.assertEqual(s.events,['add','caption']);self.assertEqual(s.rows,[['User Trade',[]]])
        self.assertEqual(p.needed,'trade_text.value')
        p=f.advance(NpcClickInput(trade_text=NpcValueCapture('Türkçe',False)))
        self.assertEqual(p.needed,'trade_text.returned');self.assertEqual(s.events,['add','caption'])
        p=f.advance(NpcClickInput(trade_text=NpcValueCapture('Changed',True)))
        self.assertTrue(p.complete);self.assertEqual(s.rows,[['User Trade',['Türkçe','-']]])

    def test_invalid_reached_value_can_be_corrected_but_unreached_input_is_ignored(self):
        s=Sink();f=NpcClickFrame(s);p=f.advance(NpcClickInput(target_gate=NpcValueCapture(True,True)))
        self.assertFalse(p.done);self.assertTrue(p.error);self.assertNotIn('value',f.cache['target_gate'])
        p=f.advance(sample(dialog_text={},trade_text={}))
        self.assertTrue(p.complete);self.assertNotIn('dialog_text',f.cache);self.assertNotIn('trade_text',f.cache)

    def test_partial_setter_failure_is_terminal_and_prefix_is_preserved(self):
        s=Sink('sub2');f=NpcClickFrame(s);p=f.advance(sample())
        self.assertTrue(p.done);self.assertFalse(p.complete);self.assertEqual(s.rows,[['NPC',['Potion']]])
        self.assertIs(f.advance(sample()),p);self.assertEqual(s.events.count('add'),1)

    def test_deleted_trade_row_cannot_write_into_replacement(self):
        s=Sink();f=NpcClickFrame(s);f.advance(sample(third=1));s.rows[:]=[['replacement',[]]]
        p=f.advance(NpcClickInput(trade_text=NpcValueCapture('name',True)))
        self.assertTrue(p.done);self.assertFalse(p.complete);self.assertEqual(f.cache['trade_text'],{})
        self.assertEqual(s.rows,[['replacement',[]]])

    def test_reentrant_advance_and_cancel_do_not_duplicate_or_continue_writes(self):
        s=Sink();f=NpcClickFrame(s);original=s.set_caption
        def caption(row,text):
            f.advance(sample());original(row,text);f.cancel('own profile change')
        s.set_caption=caption;p=f.advance(sample())
        self.assertEqual(p.status,'cancelled');self.assertEqual(s.events,['add','caption'])
        self.assertIs(f.advance(sample()),p)

    def test_new_invocation_needs_fresh_capture_and_raw_dword_upper_boundary(self):
        s=Sink();f=NpcClickFrame(s);p=f.advance(sample(third=0xffffffff))
        self.assertTrue(p.complete);g=NpcClickFrame(s);q=g.advance()
        self.assertFalse(q.done);self.assertEqual(len(s.rows),1)
        for bad in (-1,1<<32,'1'):
            h=NpcClickFrame(Sink());q=h.advance(sample(target_gate=NpcValueCapture(bad,True)))
            self.assertFalse(q.done);self.assertTrue(q.error)


if __name__=='__main__':unittest.main()
