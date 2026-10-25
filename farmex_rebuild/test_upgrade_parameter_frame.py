import unittest
from dataclasses import replace
from upgrade_parameter_frame import UpgradeParameterState,UpgradeParameterFrame,UpgradeParameterObservation


def observed(**changes):
    fields=dict(gate_byte=1,text_init_returns={k:True for k in ('scroll','anvil','wait')},
        text_get_returns={k:True for k in ('scroll','anvil','wait')},effective_codepage=1254,
        scroll_conversion_returned=True,scroll_assignment_returned=True,
        scroll_ansi_cleanup_returned=True,scroll_unicode_cleanup_returned=True,
        scalar_returns={'anvil':True,'wait':True},number_cleanup_returns={'anvil':True,'wait':True})
    fields.update(changes);return UpgradeParameterObservation(**fields)


class ParameterTests(unittest.TestCase):
    def frame(self,texts=None,state=None):
        texts=dict(scroll='Scroll',anvil='1',wait='2000') if texts is None else texts
        state=UpgradeParameterState(b'old',1254,9,99) if state is None else state
        reads=[]
        def read(name):reads.append(name);return texts[name]
        return UpgradeParameterFrame(state,read),state,texts,reads

    def test_unknown_or_zero_gate_does_not_read_text_or_change_state(self):
        f,state,texts,reads=self.frame();self.assertEqual(f.advance().needed,('gate_byte',))
        p=f.advance(UpgradeParameterObservation(gate_byte=0,text_init_returns={}))
        self.assertTrue(p.complete);self.assertEqual(reads,[]);self.assertEqual(state.scroll_bytes,b'old')

    def test_order_and_low_dword_from_accepted_full_int64(self):
        f,state,texts,reads=self.frame(dict(scroll='Ş',anvil='$100000001',wait='-9223372036854775808'))
        p=f.advance(observed());self.assertTrue(p.complete)
        self.assertEqual(reads,['scroll','anvil','wait']);self.assertEqual(state.scroll_bytes,b'\xde')
        self.assertEqual((state.anvil_dword,state.interval_dword),(1,0))
        self.assertEqual([w[0] for w in p.writes],['scroll_ansi','anvil_dword','wait_dword'])
        self.assertFalse(p.native_execution_verified);self.assertFalse(p.live_compatibility_verified)

    def test_scroll_conversion_and_assignment_are_separate_before_prefix_write(self):
        for field in ('scroll_conversion_returned','scroll_assignment_returned'):
            f,state,texts,reads=self.frame();p=f.advance(observed(**{field:False}))
            self.assertEqual(state.scroll_bytes,b'old');self.assertEqual(reads,['scroll'])
            self.assertEqual(p.needed,(None,field));self.assertTrue(f.advance(observed()).complete)
            self.assertEqual(reads,['scroll','anvil','wait'])

    def test_scroll_cleanup_gap_keeps_written_ansi_and_does_not_read_anvil(self):
        for field in ('scroll_ansi_cleanup_returned','scroll_unicode_cleanup_returned'):
            f,state,texts,reads=self.frame();p=f.advance(observed(**{field:False}))
            self.assertEqual(state.scroll_bytes,b'Scroll');self.assertEqual(reads,['scroll'])
            self.assertEqual(state.anvil_dword,9);self.assertEqual(len(p.writes),1)
            texts['scroll']='Changed';self.assertTrue(f.advance(observed()).complete)
            self.assertEqual(state.scroll_bytes,b'Scroll')

    def test_later_fields_are_fresh_and_text_reads_are_not_repeated(self):
        f,state,texts,reads=self.frame();p=f.advance(observed(number_cleanup_returns={'anvil':False,'wait':True}))
        self.assertEqual(p.needed,('number_cleanup_returns','anvil'));self.assertEqual(state.anvil_dword,1)
        texts['anvil']='99';texts['wait']='$FFFFFFFFFFFFFFFF'
        self.assertTrue(f.advance(observed()).complete)
        self.assertEqual(state.anvil_dword,1);self.assertEqual(state.interval_dword,0xffffffff)
        self.assertEqual(reads,['scroll','anvil','wait'])

    def test_invalid_scalar_needs_observed_helper_result_not_assumed_fallback(self):
        f,state,texts,reads=self.frame(dict(scroll='S',anvil='invalid',wait='also invalid'))
        p=f.advance(observed());self.assertEqual(p.needed,('scalar_qwords','anvil'))
        self.assertEqual(state.anvil_dword,9);self.assertEqual(state.scroll_bytes,b'S')
        p=f.advance(observed(scalar_qwords={'anvil':0},scalar_returns={'anvil':False}))
        self.assertEqual(p.needed,('scalar_returns','anvil'));self.assertEqual(state.anvil_dword,9)
        p=f.advance(observed(scalar_qwords={'anvil':123,'wait':2000}))
        self.assertTrue(p.complete);self.assertEqual(state.anvil_dword,0);self.assertEqual(state.interval_dword,2000)
        self.assertEqual([r[3] for r in p.requests],[0,2000])

    def test_accepted_scalar_still_requires_helper_normal_return(self):
        f,state,texts,reads=self.frame();p=f.advance(observed(scalar_returns={'anvil':False,'wait':True}))
        self.assertEqual(p.needed,('scalar_returns','anvil'));self.assertEqual(state.anvil_dword,9)
        with self.assertRaises(ValueError):
            g,_,_,_=self.frame();g.advance(observed(scalar_qwords={'anvil':2}))
        self.assertTrue(f.advance(observed()).complete)

    def test_nonempty_scroll_needs_codepage_and_empty_scroll_does_not_guess_one(self):
        f,state,texts,reads=self.frame();p=f.advance(observed(effective_codepage=None))
        self.assertEqual(p.needed,('effective_codepage',));self.assertEqual(state.scroll_bytes,b'old')
        g,state,_,_=self.frame(dict(scroll='',anvil='1',wait='2'))
        self.assertTrue(g.advance(observed(effective_codepage={})).complete)
        self.assertEqual((state.scroll_bytes,state.scroll_codepage),(b'',None))

    def test_counted_unicode_to_ansi_keeps_embedded_nul(self):
        f,state,_,_=self.frame(dict(scroll='A\0B',anvil='1',wait='2'))
        self.assertTrue(f.advance(observed()).complete);self.assertEqual(state.scroll_bytes,b'A\0B')

    def test_init_and_get_returns_are_distinct_and_pending_get_does_not_reread(self):
        f,state,texts,reads=self.frame();p=f.advance(observed(text_init_returns={'scroll':False}))
        self.assertEqual(reads,[]);self.assertEqual(p.needed,('text_init_returns','scroll'))
        p=f.advance(observed(text_get_returns={'scroll':False}));self.assertEqual(reads,['scroll'])
        texts['scroll']='Changed';self.assertTrue(f.advance(observed()).complete)
        self.assertEqual(state.scroll_bytes,b'Scroll');self.assertEqual(reads,['scroll','anvil','wait'])

    def test_final_cleanup_gap_preserves_all_writes_without_duplicate(self):
        f,state,_,_=self.frame();p=f.advance(observed(number_cleanup_returns={'anvil':True,'wait':False}))
        self.assertFalse(p.complete);self.assertEqual((state.anvil_dword,state.interval_dword),(1,2000))
        self.assertEqual(len(p.writes),3);p=f.advance(observed());self.assertTrue(p.complete)
        self.assertEqual(len(p.writes),3);self.assertIs(f.advance({}),p)

    def test_cancel_preserves_prefix_and_does_not_consume_unreached_values(self):
        f,state,_,reads=self.frame();f.advance(observed(scroll_unicode_cleanup_returned=False,scalar_returns={}))
        p=f.cancel('profile');self.assertIs(f.advance(observed()),p)
        self.assertEqual(state.scroll_bytes,b'Scroll');self.assertEqual(reads,['scroll'])


if __name__=='__main__':unittest.main()
