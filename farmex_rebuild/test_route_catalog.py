import unittest
from route_catalog import RouteCatalogEntry as E,plan_route_catalog as plan,route_filename_accepted as accepted,PLACEHOLDER

class RouteCatalogTests(unittest.TestCase):
    def test_only_exact_uppercase_extension(self):
        for name in (b'a.R',b'route.backup.R',b'.hidden.R'):self.assertTrue(accepted(name))
        for name in (b'a.r',b'route.R.bak',b'a.R ',b'a.rR',b'a',b'..'):self.assertFalse(accepted(name))
    def test_minimum_byte_length_excludes_bare_extension(self):
        self.assertFalse(accepted(b'.R'));self.assertFalse(accepted(b''))
        self.assertTrue(accepted(b'\x81.R'))
    def test_no_sort_dedup_or_extension_removal(self):
        entries=(E(b'z.R','z.R',True),E(b'a.R','a.R',True),E(b'z.R','z.R',True))
        p=plan(entries,enumeration_complete=True)
        self.assertTrue(p.complete);self.assertEqual(p.rows,('z.R','a.R','z.R'))
        self.assertEqual(p.ansi_names,(b'z.R',b'a.R',b'z.R'));self.assertFalse(p.native_execution_verified)
    def test_empty_catalog_placeholder_is_conditional_on_completed_enumeration(self):
        for done in (None,False):
            p=plan((),enumeration_complete=done);self.assertFalse(p.complete);self.assertEqual(p.rows,())
        p=plan((),enumeration_complete=True);self.assertTrue(p.complete);self.assertEqual(p.rows,(PLACEHOLDER,))
    def test_filtered_empty_has_placeholder_and_ignores_unreached_conversions(self):
        p=plan((E(b'.R'),E(b'a.r'),E(b'.'),E(b'..')),enumeration_complete=True)
        self.assertTrue(p.complete);self.assertEqual(p.rows,(PLACEHOLDER,));self.assertEqual(p.examined,4)
    def test_prefix_cannot_certify_full_catalog_even_with_names(self):
        p=plan((E(b'one.R','one.R',True),),enumeration_complete=False)
        self.assertFalse(p.complete);self.assertEqual(p.rows,('one.R',));self.assertIn('enumeration',p.missing)
    def test_conversion_gaps_do_not_invent_unicode_or_consume_tail(self):
        for e in (E(b'one.R','one.R'),E(b'one.R',conversion_returned=True)):
            p=plan((e,E(b'later.R','later.R',True)),enumeration_complete=True)
            self.assertFalse(p.complete);self.assertEqual(p.rows,());self.assertEqual(p.examined,1)
    def test_conversion_result_not_guessed_from_filename_encoding(self):
        p=plan((E(b'\xdd.R','İ.R',True),),enumeration_complete=True)
        self.assertTrue(p.complete);self.assertEqual(p.rows,('İ.R',))
    def test_source_predicate_has_no_file_type_filter(self):
        p=plan((E(b'directory.R','directory.R',True),),enumeration_complete=True)
        self.assertEqual(p.rows,('directory.R',)) # Entry type is not an input to this source predicate.
    def test_types_and_nul_boundary(self):
        for name in (b'a.R\0junk','a.R'):
            with self.assertRaises(ValueError):accepted(name)
        with self.assertRaises(ValueError):E(b'a.R\0')
        with self.assertRaises(ValueError):E(b'a.R',conversion_returned=1)
        with self.assertRaises(ValueError):plan([],enumeration_complete=True)
        with self.assertRaises(ValueError):plan((),enumeration_complete=1)

if __name__=='__main__':unittest.main()
