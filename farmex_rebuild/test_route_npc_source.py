import unittest
from dataclasses import replace
from route_npc_source import NpcSourceFrame,NpcSourceInput
from route_npc_click import NpcClickInput,NpcValueCapture
from target_id_frames import TargetIdObservation
from route_npc_name import RouteNpcNameObservation
from test_target_id_frames import sample
from test_route_npc_name import observed
from test_route_coordinate_click import Sink
from npc_actor_lookup import NpcLookupObservation
from test_npc_actor_lookup import sample as lookup_sample
from npc_unicode import NpcUnicodeObservation
from test_npc_unicode import observed as unicode_observed


def source(name_bytes=b'DC Sundries',third=3001,**changes):
    values=dict(target_gate=sample(77),target_lookup=sample(88,slot=0x200),
                actor=NpcValueCapture(0x1000,True),name=observed(data=name_bytes),
                target_classify=sample(third,slot=0x300))
    values.update(changes);return NpcSourceInput(**values)


class NpcSourceTests(unittest.TestCase):
    def test_late_unicode_child_preserves_row_prefix_and_blocks_ready_text_bypass(self):
        sink=Sink();f=NpcSourceFrame(sink)
        p=f.advance(source(b'Name',third=0,trade_text=unicode_observed(rtl_returned=False)))
        self.assertEqual(sink.rows,[['User Trade',[]]])
        self.assertEqual(p.needed,('trade_text',('rtl_returned',)))
        p=f.advance(NpcSourceInput(trade_text=NpcValueCapture('Bypass',True)))
        self.assertFalse(p.done);self.assertIn('bypass',p.error)
        p=f.advance(NpcSourceInput(trade_text=unicode_observed()))
        self.assertTrue(p.complete);self.assertEqual(sink.rows,[['User Trade',['Name','-']]])

    def test_unreached_unicode_input_is_not_consumed_by_npc_branch(self):
        f=NpcSourceFrame(Sink());p=f.advance(source(trade_text=NpcUnicodeObservation(ansi_is_null={})))
        self.assertTrue(p.complete);self.assertIsNone(f.unicode)

    def test_deleted_trade_row_stops_before_late_unicode_receipt(self):
        sink=Sink();f=NpcSourceFrame(sink)
        f.advance(source(b'Name',third=0,trade_text=unicode_observed(constructor_returned=False)))
        sink.rows[:]=[['replacement',[]]]
        p=f.advance(NpcSourceInput(trade_text=unicode_observed()))
        self.assertTrue(p.done);self.assertFalse(p.complete)
        self.assertNotIn('constructor_returned',f.unicode.cache)

    def test_typed_lookup_child_uses_second_target_and_blocks_ready_actor_bypass(self):
        sink=Sink();f=NpcSourceFrame(sink)
        p=f.advance(source(actor=replace(lookup_sample(),indirect_returned=False)))
        self.assertEqual(p.needed,('actor',('indirect_returned',)));self.assertIsNone(f.name)
        self.assertEqual(f.lookup.input_id,88)
        p=f.advance(NpcSourceInput(actor=NpcValueCapture(0x1000,True)))
        self.assertFalse(p.done);self.assertIn('bypass',p.error);self.assertEqual(sink.rows,[])
        p=f.advance(source(actor=lookup_sample()))
        self.assertTrue(p.complete);self.assertEqual(f.lookup.final.call.pushes,(1,88))
        self.assertEqual(sink.rows,[['NPC',['DC Sundries','-']]])

    def test_typed_lookup_zero_stops_before_name_or_third_target(self):
        f=NpcSourceFrame(Sink());p=f.advance(source(actor=lookup_sample(0),name={},target_classify={}))
        self.assertEqual(p.status,'lookup_empty');self.assertIsNone(f.name)
        self.assertIsNone(f.targets['target_classify'].observation.root_address_dword)

    def test_complete_lower_chain_creates_npc_without_ready_name_or_target(self):
        sink=Sink();f=NpcSourceFrame(sink);p=f.advance(source())
        self.assertTrue(p.complete);self.assertEqual(sink.rows,[['NPC',['DC Sundries','-']]])
        self.assertEqual([f.targets[k].final.value for k in ('target_gate','target_lookup','target_classify')],[77,88,3001])
        self.assertEqual(f.name.final.name_bytes,b'DC Sundries')

    def test_pending_name_leaves_third_target_fresh_and_completed_targets_stable(self):
        sink=Sink();f=NpcSourceFrame(sink)
        p=f.advance(source(name=replace(observed(),copy_returned=False),target_classify={}))
        self.assertEqual(p.needed,('name_bytes','copy_returned'));self.assertEqual(sink.rows,[])
        self.assertIsNone(f.targets['target_classify'].observation.root_address_dword)
        p=f.advance(source(name=observed(data=b'Other'),third=0,target_gate=sample(0),target_lookup=sample(0)))
        self.assertFalse(p.done);self.assertEqual(f.targets['target_gate'].final.value,77)
        self.assertEqual(sink.rows,[['User Trade',[]]])
        p=f.advance(NpcSourceInput(trade_text=NpcValueCapture('Late Unicode',True)))
        self.assertTrue(p.complete);self.assertEqual(sink.rows,[['User Trade',['Late Unicode','-']]])
        self.assertEqual(f.name.final.name_bytes,b'Potion')

    def test_first_zero_avoids_lookup_and_name_producers(self):
        f=NpcSourceFrame(Sink());p=f.advance(source(target_gate=sample(0),target_lookup={},actor={},name={}))
        self.assertEqual(p.status,'no_selection');self.assertIsNone(f.name)
        self.assertIsNone(f.targets['target_lookup'].observation.root_address_dword)

    def test_opaque_lookup_keeps_explicit_return_and_zero_exit(self):
        f=NpcSourceFrame(Sink());p=f.advance(source(actor=NpcValueCapture(0,False),name={}))
        self.assertFalse(p.done);self.assertEqual(p.needed,'actor.returned');self.assertIsNone(f.name)
        p=f.advance(NpcSourceInput(actor=NpcValueCapture(99,True)))
        self.assertEqual(p.status,'lookup_empty');self.assertIsNone(f.name)

    def test_source_gaps_cannot_be_bypassed_by_ready_inputs(self):
        f=NpcSourceFrame(Sink());p=f.advance(NpcSourceInput())
        self.assertEqual(p.needed,('target_gate',('root_address_dword',)))
        p=f.advance(NpcClickInput(target_gate=NpcValueCapture(3,True)))
        self.assertFalse(p.done);self.assertIn('bypass',p.error)
        self.assertTrue(f.advance(source()).complete)
        g=NpcSourceFrame(Sink());g.advance(NpcClickInput(target_gate=NpcValueCapture(3,True)))
        self.assertIn('mode',g.advance(source()).error)

    def test_own_dialog_is_only_ready_capture_allowed_in_source_mode(self):
        sink=Sink();f=NpcSourceFrame(sink);p=f.advance(source(b'Royal National'))
        self.assertEqual(p.needed,'dialog_text.value');self.assertEqual(sink.rows,[])
        p=f.advance(NpcClickInput(dialog_text=NpcValueCapture('4',True)))
        self.assertTrue(p.complete);self.assertEqual(sink.rows,[['NPC',['Royal National Enchanter','4']]])

    def test_wrong_child_capture_is_pending_and_correctable_without_fake_row(self):
        sink=Sink();f=NpcSourceFrame(sink);p=f.advance(source(target_gate={}))
        self.assertFalse(p.done);self.assertTrue(p.error);self.assertEqual(sink.rows,[])
        p=f.advance(source());self.assertTrue(p.complete);self.assertEqual(len(sink.rows),1)

    def test_cancel_and_deleted_trade_row_never_consume_late_input(self):
        sink=Sink();f=NpcSourceFrame(sink);f.advance(source(third=0))
        sink.rows[:]=[['replacement',[]]]
        p=f.advance(NpcSourceInput(trade_text=NpcValueCapture('Name',True)))
        self.assertTrue(p.done);self.assertFalse(p.complete);self.assertEqual(sink.rows,[['replacement',[]]])
        g=NpcSourceFrame(Sink());g.advance(NpcSourceInput());p=g.cancel('profile')
        self.assertIs(g.advance(source()),p);self.assertIs(g.hold('late'),p)


if __name__=='__main__':unittest.main()
