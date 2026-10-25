import unittest
from types import SimpleNamespace
from unittest.mock import patch
from route_catalog import RouteCatalogEntry as E,plan_route_catalog as plan,read_local_route_catalog,PLACEHOLDER
from name_codec import WindowsNameCodec

class Scan:
    def __init__(self,names,error=None):self.names=iter(names);self.error=error;self.closed=False
    def __enter__(self):return self
    def __exit__(self,*args):self.closed=True
    def __iter__(self):return self
    def __next__(self):
        try:return SimpleNamespace(name=next(self.names))
        except StopIteration:
            if self.error is not None:raise self.error
            raise

class RouteCatalogTerminationTests(unittest.TestCase):
    def test_known_open_failure_clears_view_without_claiming_directory_inventory(self):
        p=plan((),terminal_reason='open_failed')
        self.assertTrue(p.complete);self.assertEqual(p.rows,(PLACEHOLDER,))
        self.assertFalse(p.enumeration_verified);self.assertEqual(p.termination,'open_failed')
        with self.assertRaises(ValueError):plan((E(b'a.R','a.R',True),),terminal_reason='open_failed')
        with self.assertRaises(ValueError):plan((),enumeration_complete=True,terminal_reason='open_failed')
    def test_known_read_stop_projects_prefix_and_empty_prefix_but_not_healthy_eof(self):
        for entries,rows in (((),(PLACEHOLDER,)),((E(b'b.R','b.R',True),),('b.R',))):
            p=plan(entries,enumeration_complete=False,terminal_reason='read_stopped')
            self.assertTrue(p.complete);self.assertEqual(p.rows,rows);self.assertFalse(p.enumeration_verified)
        p=plan((E(b'b.R','b.R',True),),enumeration_complete=False)
        self.assertFalse(p.complete);self.assertEqual(p.rows,('b.R',))
    def test_open_os_error_maps_to_empty_source_shaped_view_and_keeps_diagnostic(self):
        with patch('route_catalog.os.scandir',side_effect=PermissionError(5,'denied')):
            p=read_local_route_catalog(r'C:\owned',WindowsNameCodec(1254))
        self.assertTrue(p.complete);self.assertEqual(p.rows,(PLACEHOLDER,))
        self.assertEqual(p.failed_operation,'scandir_open');self.assertIn('denied',p.local_error)
        self.assertFalse(p.enumeration_verified)
    def test_mid_scan_os_error_keeps_only_read_matching_names_and_closes_iterator(self):
        scan=Scan(('z.R','ignored.r','a.R'),OSError(5,'next failed'))
        with patch('route_catalog.os.scandir',return_value=scan):p=read_local_route_catalog(r'C:\owned',WindowsNameCodec(1254))
        self.assertTrue(p.complete);self.assertEqual(p.rows,('z.R','a.R'))
        self.assertTrue(scan.closed);self.assertEqual(p.examined,3)
        self.assertEqual(p.failed_operation,'scandir_next');self.assertIn('next failed',p.local_error)
        self.assertFalse(p.enumeration_verified)
    def test_mid_scan_error_with_no_matching_name_uses_placeholder(self):
        with patch('route_catalog.os.scandir',return_value=Scan(('x.r',),OSError(5,'stop'))):
            p=read_local_route_catalog(r'C:\owned',WindowsNameCodec(1254))
        self.assertTrue(p.complete);self.assertEqual(p.rows,(PLACEHOLDER,));self.assertFalse(p.enumeration_verified)
    def test_normal_eof_is_separate_and_budget_or_codec_error_is_not_terminal_read(self):
        scan=Scan(('a.R',))
        with patch('route_catalog.os.scandir',return_value=scan):p=read_local_route_catalog(r'C:\owned',WindowsNameCodec(1254),max_entries=1)
        self.assertTrue(p.enumeration_verified);self.assertTrue(p.complete)
        self.assertEqual(p.local_error,'');self.assertTrue(scan.closed)
        for names,budget in ((('a.R','b.R'),1),(('😀.R',),5)):
            scan=Scan(names)
            with patch('route_catalog.os.scandir',return_value=scan):
                with self.assertRaises(ValueError):read_local_route_catalog(r'C:\owned',WindowsNameCodec(1254),max_entries=budget)
            self.assertTrue(scan.closed)

if __name__=='__main__':unittest.main()
