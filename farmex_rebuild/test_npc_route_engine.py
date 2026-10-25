import unittest
from npc_route_engine import NpcRouteFrame, npc_route_step

ALL=('Sundries','Armor','Weapon','Potion','DC Sundries','Inn Hostess','Royal National Enchanter')


class NpcRouteTests(unittest.TestCase):
    def run_phase(self,phase,kind='',fields=None,globals=None,helpers=None):
        return npc_route_step(NpcRouteFrame(phase,fields or {},globals or {}),
                              {name:name==kind for name in ALL},helpers)

    def test_skipped_phases_walk_to_one_shot_completion(self):
        frame=NpcRouteFrame(3)
        for phase in range(4,10):
            result=npc_route_step(frame,{name:False for name in ALL})
            self.assertEqual(result.frame.phase,phase)
            self.assertFalse(result.returned_true)
            frame=result.frame
        result=npc_route_step(frame,{name:False for name in ALL})
        self.assertEqual(result.frame.phase,11);self.assertTrue(result.returned_true)
        self.assertFalse(npc_route_step(result.frame,{}).returned_true)

    def test_missing_lookup_not_invented(self):
        for phase in (1,2):self.assertEqual(self.run_phase(phase).status,'needs_observation')

    def test_unknown_comparison_preserves_state(self):
        frame=NpcRouteFrame(4,{0x650:0})
        result=npc_route_step(frame,{})
        self.assertEqual(result.frame,frame);self.assertEqual(result.status,'needs_observation')

    def test_sale_begin_and_terminal_code42(self):
        result=self.run_phase(3,'Sundries',{0x63c:0},{0x561f58:0})
        self.assertEqual(result.frame.fields[0x63c],1)
        self.assertEqual(result.frame.globals[0x561faa],1)
        result=self.run_phase(3,'Sundries',dict(result.frame.fields),{0x561f58:0},{'004edf34':42})
        self.assertEqual(result.frame.phase,4);self.assertEqual(result.frame.globals[0x561faa],0)

    def test_sale_mode2_skip_uses_flag(self):
        r=self.run_phase(3,'Armor',globals={0x561f58:2,0x56fad2:1})
        self.assertEqual(r.frame.phase,4);self.assertEqual(r.calls,())

    def test_phase4_guard_blocks_helper(self):
        r=self.run_phase(4,'Potion',{0x650:1},helpers={'004fe384':1})
        self.assertEqual(r.calls,('004fe384',));self.assertEqual(r.frame.phase,4)

    def test_phase4_initial13_then43_resets(self):
        r=self.run_phase(4,'Potion',{0x650:0})
        self.assertEqual(r.frame.fields[0x654],13)
        r=self.run_phase(4,'Potion',dict(r.frame.fields),helpers={'004fe384':0,'004eebf4':43})
        self.assertEqual(r.frame.phase,5);self.assertEqual(r.frame.fields[0x650],0)
        self.assertEqual(r.frame.fields[0x654],13)

    def test_shared_start_phase5_and8_use_different_direction(self):
        for phase,kind,direction in ((5,'Potion',1),(8,'Inn Hostess',0)):
            r=self.run_phase(phase,kind,{0x556:1,0x688:0},{0x5690cc:20}, {'0046fe90':0})
            self.assertEqual(r.frame.globals[0x5690c1],direction)
            self.assertEqual(r.frame.globals[0x5690c8],20)
            self.assertEqual(r.frame.globals[0x5690b8],1)

    def test_shared_count47_vs48_and_single_high_count_retry(self):
        for phase,kind,retry,end in ((5,'Potion',4,6),(8,'Inn Hostess',7,9)):
            for count,marker,expected in ((47,1,retry),(48,0,retry),(48,1,end),(0xffffffff,1,retry)):
                r=self.run_phase(phase,kind,{0x556:1,0x688:1},
                                {0x5690b8:0,0x5690cc:count,0x5690d8:marker},{'0046fe90':0})
                self.assertEqual(r.frame.phase,expected)
                self.assertEqual(r.frame.fields[0x688],0)
                if count==48 and marker==0:self.assertEqual(r.frame.globals[0x5690d8],1)

    def test_phase8_guard_returns_before_local_start(self):
        r=self.run_phase(8,'Inn Hostess',{0x556:1},helpers={'0046fe90':1})
        self.assertEqual(r.frame.phase,8);self.assertNotIn(0x688,r.frame.fields)

    def test_shared_disabled_skips_without_missing_globals(self):
        r=self.run_phase(5,'Weapon',{0x556:0},{0x56fae4:0})
        self.assertEqual(r.frame.phase,6)

    def test_vector_zero_start_short_circuits_end(self):
        r=self.run_phase(6,'Weapon',{0x689:0,0x18:0},{0x561f58:0})
        self.assertEqual(r.frame.phase,7);self.assertEqual(r.frame.fields[0x68c],0)

    def test_vector_count_signed_truncation_and_begin_marker(self):
        for end,count in ((172,2),(27,-2)):
            r=self.run_phase(6,'Armor',{0x689:0,0x18:100,0x1c:end},{0x561f58:0})
            self.assertEqual(r.frame.fields[0x68c],count)
            self.assertEqual(r.frame.fields[0x690],0xffffffff)
            self.assertEqual(r.frame.phase,6)

    def test_vector_helper_equality_not_complete(self):
        for progress,phase in ((2,6),(3,7),(0xffffffff,6)):
            r=self.run_phase(6,'Weapon',{0x689:1,0x68c:2},{0x561f58:0},
                             {'004fe384':0,'004efa84':progress})
            self.assertEqual(r.frame.phase,phase)

    def test_phase6_mode2_skips_list_fields(self):
        self.assertEqual(self.run_phase(6,'Sundries',globals={0x561f58:2}).frame.phase,7)

    def test_deposit_start_wait_and_reset(self):
        r=self.run_phase(7,'Inn Hostess',{0x6d8:0},helpers={'004fe384':0})
        self.assertEqual(r.frame.globals[0x5690e4],1)
        self.assertEqual(r.frame.globals[0x5690e0],1)
        for busy,phase in ((1,7),(0,8)):
            r=self.run_phase(7,'Inn Hostess',{0x6d8:1},{0x5690e0:busy},{'004fe384':0})
            self.assertEqual(r.frame.phase,phase)

    def test_enchanter_terminal8_completes_same_invocation(self):
        r=self.run_phase(9,'Royal National Enchanter',{0x6c0:0})
        self.assertEqual(r.frame.fields[0x6c0],1);self.assertFalse(r.returned_true)
        r=self.run_phase(9,'Royal National Enchanter',dict(r.frame.fields),helpers={'004f035c':8})
        self.assertTrue(r.returned_true);self.assertEqual(r.frame.phase,11)
        self.assertEqual(r.frame.fields[0x6c0],0)

    def test_incomplete_helper_return_not_fabricated(self):
        r=self.run_phase(9,'Royal National Enchanter',{0x6c0:1})
        self.assertEqual(r.status,'needs_observation');self.assertFalse(r.returned_true)
        self.assertEqual(r.calls,('004f035c',))

    def test_frame_copies_input_and_blocks_mutation(self):
        source={0x650:0};frame=NpcRouteFrame(4,source);source[0x650]=1
        self.assertEqual(frame.fields[0x650],0)
        with self.assertRaises(TypeError):frame.fields[0x650]=1

    def test_phase1_lookup_filters_and_counter_reset(self):
        for kind,name in (('Potion','otion'),('Sundries','undries'),('Armor','rmor'),
                          ('Weapon','eapon'),('DC Sundries','DC Sund'),
                          ('Royal National Enchanter','Royal National Enchanter')):
            r=self.run_phase(1,kind,helpers={'00465960:'+name:7})
            self.assertEqual(r.frame.phase,2);self.assertEqual(r.frame.fields[0x604],7)
            self.assertEqual(r.frame.globals[0x5690cc],0)
            self.assertEqual(r.frame.globals[0x5690d8],0)

    def test_phase1_lookup_zero_waits(self):
        r=self.run_phase(1,'Potion',helpers={'00465960:otion':0})
        self.assertEqual(r.frame.phase,1);self.assertFalse(r.returned_true)

    def test_phase1_no_match_retains_existing_id(self):
        r=self.run_phase(1,fields={0x604:9})
        self.assertEqual(r.frame.phase,2);self.assertEqual(r.calls,())

    def test_inn_moradon_distance_strictly_over30(self):
        matches={name:name=='Inn Hostess' for name in ALL}
        for moradon,distance,name in ((False,None,'Inn'),(True,30,'Inn'),(True,30.001,'Kronil')):
            r=npc_route_step(NpcRouteFrame(1),matches,{'00465960:'+name:8},
                             inn_in_moradon=moradon,inn_distance=distance)
            self.assertEqual(r.frame.fields[0x604],8)
            self.assertIn('00465960:'+name,r.calls)

    def test_phase2_missing_pointer_waits_without_text(self):
        r=self.run_phase(2,fields={0x604:8},helpers={'00464a10':0})
        self.assertEqual(r.frame.phase,2);self.assertEqual(r.calls,('00464a10',))

    def test_phase2_signed16_boundary_and_observed_text(self):
        for raw_length in (15,16,0xffffffff):
            helpers={'00464a10':0x100000,'0045dc44:raw_field_fec':raw_length,
                     '0045dc44:raw_field_fe8':27}
            r=npc_route_step(NpcRouteFrame(2,{0x604:8},{0x553fec:12,0x553fe8:8}),{},helpers,
                             observed_text='observed raw converted text')
            self.assertEqual(r.frame.phase,3)
            self.assertEqual(r.frame.texts[0x610],'observed raw converted text')
            self.assertEqual('0045dc44:raw_field_fe8' in r.calls,raw_length==16)

    def test_phase2_does_not_invent_formatter_output(self):
        r=npc_route_step(NpcRouteFrame(2,{0x604:8},{0x553fec:12,0x553fe8:8}),{},
                         {'00464a10':0x100000,'0045dc44:raw_field_fec':1})
        self.assertEqual(r.status,'needs_observation');self.assertNotIn(0x610,r.frame.texts)

    def test_phase2_copies_observed_indirect_ansi_bytes(self):
        r=npc_route_step(NpcRouteFrame(2,{0x604:8},{0x553fec:12,0x553fe8:8}),{},
                         {'00464a10':0x100000,'0045dc44:raw_field_fec':16,
                          '0045dc44:raw_field_fe8':0x200000},
                         text_readable=True,copied_bytes=b'Potion\0'+b'\0'*9,codec='ascii')
        self.assertEqual(r.frame.phase,3);self.assertEqual(r.frame.texts[0x610],'Potion')
        self.assertEqual(r.text_request.address,0x200000);self.assertEqual(r.text_request.byte_count,16)

    def test_phase2_unverified_codepage_blocks_advancement(self):
        r=npc_route_step(NpcRouteFrame(2,{0x604:8},{0x553fec:12,0x553fe8:8}),{},
                         {'00464a10':0x100000,'0045dc44:raw_field_fec':15},
                         text_readable=True,copied_bytes=b'\xdd'+b'\0'*254)
        self.assertEqual(r.frame.phase,2);self.assertEqual(r.missing,'game_text:needs_codepage')
        self.assertEqual(r.text_request.address,0x100008)
