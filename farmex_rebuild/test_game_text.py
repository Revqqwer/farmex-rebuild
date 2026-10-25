import unittest
from game_text import npc_text_request, replay_text_copy


class GameTextTests(unittest.TestCase):
    def test_inline_signed_length_and_pointer_wrap(self):
        for length in (0,15,0xffffffff):
            r=npc_text_request(0xfffffff0,32,length)
            self.assertEqual((r.address,r.byte_count,r.indirect),(16,255,False))

    def test_indirect16_requires_observed_pointer(self):
        r=npc_text_request(0x100000,32,16)
        self.assertIsNone(r.address);self.assertEqual(r.byte_count,16)
        self.assertEqual(npc_text_request(0x100000,32,16,0x200000).address,0x200000)

    def test_bad_pointer_empty_source_fallback(self):
        self.assertEqual(replay_text_copy(0xffffffff,False).text,'')

    def test_zero_and_embedded_nul(self):
        self.assertEqual(replay_text_copy(0,True,b'').text,'')
        r=replay_text_copy(8,True,b'NPC\0junk',codec='ascii')
        self.assertEqual(r.text,'NPC');self.assertEqual(r.ansi_bytes,b'NPC')

    def test_zeroed_tail_terminates255_byte_copy(self):
        r=replay_text_copy(255,True,b'a'*255,codec='ascii')
        self.assertEqual(r.text,'a'*255)

    def test_codepage_unknown_not_guessed(self):
        r=replay_text_copy(2,True,b'\xdd\0')
        self.assertEqual(r.status,'needs_codepage');self.assertIsNone(r.text)
        self.assertEqual(replay_text_copy(2,True,b'\xdd\0',codec='cp1254').text,'İ')

    def test_native512_without_nul_and_513_are_unresolved(self):
        self.assertEqual(replay_text_copy(512,True,b'a'*512).status,'unresolved_native_string_overread')
        self.assertEqual(replay_text_copy(513,True).status,'unresolved_native_buffer_overflow')

    def test_missing_and_wrong_length_observations(self):
        self.assertEqual(replay_text_copy(4,None).status,'needs_observation')
        self.assertEqual(replay_text_copy(4,True).status,'needs_observation')
        with self.assertRaises(ValueError):replay_text_copy(4,True,b'a')

    def test_explicit_invalid_conversion_not_replaced(self):
        r=replay_text_copy(1,True,b'\xff',codec='utf-8')
        self.assertEqual(r.status,'unresolved_conversion');self.assertIsNone(r.text)

    def test_lookup_unsigned16_differs_from_route_signed16(self):
        route=npc_text_request(0x100000,32,0xffffffff)
        lookup=npc_text_request(0x100000,32,0xffffffff,0x200000,signed_threshold=False)
        self.assertFalse(route.indirect);self.assertEqual(route.byte_count,255)
        self.assertTrue(lookup.indirect);self.assertEqual(lookup.byte_count,0xffffffff)
