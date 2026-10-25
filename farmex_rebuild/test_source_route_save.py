import sys
import tempfile
import unittest
from pathlib import Path

from source_route_save import write_source_route_calls,write_source_route_ini,write_source_route_dynamic_calls
from source_route_ini import read_source_route_ini


class SourceRouteWriteBoundaryTests(unittest.TestCase):
    def test_dynamic_rows_are_read_after_remove_and_fresh_each_iteration_with_cached_count(self):
        rows=[(b'old',b'0',b'0'),(b'old2',b'0',b'0')];seen=[]
        def remove(path):rows[0]=(b'after_remove',b'1',b'2');return 0
        def row(index):seen.append(index);return rows[index]
        def write(section,key,value,path):
            if key==b'Sub20':
                rows[1]=(b'fresh_second',b'3',b'4');rows.append((b'ignored',b'',b''))
            return 1
        p=write_source_route_dynamic_calls(b'C:\\own.R',2,row,remove,write)
        self.assertEqual(seen,[0,1]);self.assertEqual(len(p.calls),8)
        self.assertEqual(p.calls[1].value,b'after_remove');self.assertEqual(p.calls[5].value,b'fresh_second')
        self.assertEqual([c.value for c in p.calls if c.key==b'Value'],[b'2',b'2'])

    def test_dynamic_missing_later_row_retains_completed_write_prefix(self):
        def row(index):
            if index==1:raise IndexError('own row disappeared')
            return (b'Town',b'0',b'0')
        p=write_source_route_dynamic_calls(b'C:\\own.R',2,row,lambda _:0,lambda *args:1)
        self.assertFalse(p.complete);self.assertEqual(len(p.calls),4)
        self.assertTrue(all(c.result==1 for c in p.calls));self.assertIn('disappeared',p.error)

    def test_repeated_count_and_zero_based_keys_keep_exact_call_order(self):
        events=[]
        def remove(path):events.append(('remove',path));return -1
        def write(*args):events.append(('write',)+args);return 1
        rows=((b'Town',b'0',b'0'),(b'Bekle',b'5',b''))
        p=write_source_route_calls(b'C:\\own.R',rows,remove,write)
        self.assertTrue(p.complete);self.assertTrue(p.writes_succeeded)
        self.assertEqual(p.remove_result,-1)
        self.assertEqual(events[0],('remove',b'C:\\own.R'))
        self.assertEqual([(c.section,c.key,c.value) for c in p.calls],
            [(b'Count',b'Value',b'2'),(b'ROUTE',b'ISLEM0',b'Town'),
             (b'ROUTE',b'Sub10',b'0'),(b'ROUTE',b'Sub20',b'0'),
             (b'Count',b'Value',b'2'),(b'ROUTE',b'ISLEM1',b'Bekle'),
             (b'ROUTE',b'Sub11',b'5'),(b'ROUTE',b'Sub21',b'')])
        self.assertEqual(len(events),9)

    def test_failed_write_bool_does_not_stop_source_call_sequence(self):
        observed=[]
        def write(*args):observed.append(args);return 0 if len(observed)==2 else 1
        p=write_source_route_calls(b'C:\\own.R',((b'Town',b'',b''),),lambda _:0,write)
        self.assertTrue(p.complete);self.assertFalse(p.writes_succeeded)
        self.assertEqual(len(p.calls),4);self.assertEqual(p.calls[1].result,0)
        self.assertFalse(p.native_execution_verified)

    def test_backend_exception_retains_attempted_and_completed_prefix(self):
        count=[0]
        def write(*args):
            count[0]+=1
            if count[0]==3:raise OSError('own injected backend failure')
            return 1
        p=write_source_route_calls(b'C:\\own.R',((b'Town',b'',b''),),lambda _:-1,write)
        self.assertFalse(p.complete);self.assertEqual(p.status,'backend_incomplete')
        self.assertEqual([c.result for c in p.calls],[1,1,None])
        self.assertIsNone(p.writes_succeeded)

    def test_empty_rows_no_remove_and_invalid_rows_rejected_before_mutation(self):
        def forbidden(*args):raise AssertionError('backend must not run')
        self.assertEqual(write_source_route_calls(b'C:\\own.R',(),forbidden,forbidden).status,'empty_rows_preserve')
        for rows in ([],((b'Town',b'0'),),(('Town',b'0',b'0'),)):
            with self.assertRaises(ValueError):write_source_route_calls(b'C:\\own.R',rows,forbidden,forbidden)
        with self.assertRaises(ValueError):write_source_route_calls(b'C:\\bad\0.R',(),forbidden,forbidden)


@unittest.skipUnless(sys.platform=='win32','Real owned Windows A profile API fixture')
class SourceRouteNativeWriterTests(unittest.TestCase):
    def test_real_writer_reader_roundtrip_and_previous_file_replacement(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'round trip.R'
            path.write_bytes(b'[stale]\nobsolete=value\n[Count]\nValue=99\n')
            rows=((b'Koordinat',b'12.5',b'-3'),(b'NPC',b'\xfd\xfe\xf0',b'extra'))
            p=write_source_route_ini(str(path),rows)
            self.assertTrue(p.complete);self.assertTrue(p.writes_succeeded)
            self.assertEqual(p.remove_result,0)
            self.assertEqual(read_source_route_ini(str(path)).rows,rows)
            self.assertNotIn(b'obsolete',path.read_bytes())
            self.assertEqual(len(p.calls),8)

    def test_empty_preserves_existing_file_and_missing_parent_not_created(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'keep.R';path.write_bytes(b'leave unchanged')
            p=write_source_route_ini(str(path),())
            self.assertEqual(p.status,'empty_rows_preserve');self.assertEqual(path.read_bytes(),b'leave unchanged')
            target=Path(directory)/'absent'/'no.R'
            p=write_source_route_ini(str(target),((b'Town',b'0',b'0'),))
            self.assertEqual(p.status,'parent_missing');self.assertFalse(target.parent.exists())

    def test_real_ansi_api_nul_prefix_and_quotes_match_reader_behavior(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'api.R'
            p=write_source_route_ini(str(path),((b'Town\0ignored',b'"quoted"',b''),))
            self.assertTrue(p.writes_succeeded)
            self.assertEqual(read_source_route_ini(str(path)).rows,((b'Town',b'quoted',b''),))


if __name__=='__main__':unittest.main()
