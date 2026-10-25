"""Mocked Toolhelp boundaries; never open/read a game process."""
import os,ctypes,unittest
from unittest.mock import patch,MagicMock
from concurrent.futures import Future
from types import SimpleNamespace
from game_provider import discover_game_processes,find_game_processes,ProcessDiscovery,ProcessDiscoveryError

class Call:
    def __init__(self,fn):self.fn=fn
    def __call__(self,*args):return self.fn(*args)

class Kernel:
    def __init__(self,rows=(),first_error=None,next_error_at=None,next_error=5,snapshot_error=None,missing_error=False):
        self.rows=rows;self.first_error=first_error;self.next_error_at=next_error_at;self.next_error=next_error
        self.snapshot_error=snapshot_error;self.missing_error=missing_error;self.closed=[];self.index=0
        self.CreateToolhelp32Snapshot=Call(self.snapshot)
        self.Process32FirstW=Call(self.first);self.Process32NextW=Call(self.next)
        self.CloseHandle=Call(self.close)
    def snapshot(self,flags,pid):
        assert (flags,pid)==(2,0)
        if self.snapshot_error is not None:
            ctypes.set_last_error(self.snapshot_error);return ctypes.c_void_p(-1).value
        return 100
    def fill(self,pointer):
        if self.index>=len(self.rows):
            if not self.missing_error:ctypes.set_last_error(18)
            return 0
        entry=pointer._obj
        assert entry.dwSize==ctypes.sizeof(entry)
        entry.szExeFile,entry.th32ProcessID=self.rows[self.index]
        return 1
    def first(self,handle,pointer):
        assert handle==100;self.index=0
        if self.first_error is not None:ctypes.set_last_error(self.first_error);return 0
        return self.fill(pointer)
    def next(self,handle,pointer):
        self.index+=1
        if self.next_error_at==self.index:ctypes.set_last_error(self.next_error);return 0
        return self.fill(pointer)
    def close(self,handle):
        self.closed.append(handle);ctypes.set_last_error(999);return 1

@unittest.skipUnless(os.name=='nt','Win32 ctypes boundary tests')
class ProcessDiscoveryTests(unittest.TestCase):
    def discover(self,k):
        with patch('game_provider.ctypes.WinDLL',return_value=k):return discover_game_processes()
    def test_complete_snapshot_reports_exact_names_and_scanned_count(self):
        k=Kernel((('other.exe',1),('KnightOnLine.EXE',42),('knightonline.exe.helper',43),('knightonline.exe',44)))
        p=self.discover(k);self.assertEqual(p.status,'complete');self.assertTrue(p.enumeration_complete)
        self.assertEqual(p.pids,(42,44));self.assertEqual(p.scanned_count,4);self.assertEqual(k.closed,[100])
    def test_first_no_more_files_is_complete_empty(self):
        p=self.discover(Kernel());self.assertTrue(p.enumeration_complete);self.assertEqual(p.pids,());self.assertEqual(p.scanned_count,0)
    def test_complete_snapshot_without_match_is_distinct_from_error(self):
        p=self.discover(Kernel((('other.exe',1),)));self.assertEqual(p.status,'complete');self.assertEqual((p.pids,p.scanned_count),((),1))
    def test_first_access_error_is_not_empty_success_and_survives_close(self):
        p=self.discover(Kernel(first_error=5));self.assertFalse(p.enumeration_complete)
        self.assertEqual((p.failed_operation,p.error_code),('Process32FirstW',5));self.assertEqual(p.status,'unavailable')
    def test_mid_scan_error_keeps_diagnostics_but_rejects_partial_pid_list(self):
        k=Kernel((('KnightOnLine.exe',42),('other.exe',2)),next_error_at=1)
        p=self.discover(k);self.assertEqual((p.pids,p.scanned_count),((42,),1));self.assertFalse(p.enumeration_complete)
        self.assertEqual((p.failed_operation,p.error_code),('Process32NextW',5))
        with patch('game_provider.discover_game_processes',return_value=p):
            with self.assertRaises(ProcessDiscoveryError) as ctx:find_game_processes()
        self.assertEqual(ctx.exception.winerror,5);self.assertIs(ctx.exception.discovery,p)
    def test_false_with_no_error_is_unknown_not_no_more_files(self):
        ctypes.set_last_error(18)
        p=self.discover(Kernel(missing_error=True));self.assertFalse(p.enumeration_complete);self.assertEqual(p.error_code,0)
    def test_snapshot_failure_does_not_close_invalid_handle(self):
        k=Kernel(snapshot_error=5);p=self.discover(k)
        self.assertEqual((p.failed_operation,p.error_code),('CreateToolhelp32Snapshot',5));self.assertEqual(k.closed,[])
    def test_snapshot_failure_with_zero_error_is_not_success_message(self):
        p=self.discover(Kernel(snapshot_error=0));self.assertFalse(p.enumeration_complete);self.assertEqual(p.error_code,0)
        self.assertIn('kodu sağlanmadı',p.error)
    def test_legacy_interface_only_returns_complete_pids(self):
        with patch('game_provider.discover_game_processes',return_value=ProcessDiscovery('complete',(42,),3,True)):
            self.assertEqual(find_game_processes(),[42])
        with patch('game_provider.discover_game_processes',return_value=ProcessDiscovery('unsupported')):
            self.assertEqual(find_game_processes(),[])
    def test_connection_ui_does_not_observe_partial_discovery(self):
        from connection_ui import ConnectionPage
        page=object.__new__(ConnectionPage);page.pending=None
        page.mode=SimpleNamespace(get=lambda:'external');page.profile=SimpleNamespace(get=lambda:'us')
        page.result=MagicMock();page.status=MagicMock();page.button=MagicMock();page.frame=MagicMock()
        def immediate(fn):
            future=Future();future.set_result(fn());return future
        page.executor=SimpleNamespace(submit=immediate)
        result=ProcessDiscovery('unavailable',(42,),1,False,'Process32NextW',5,'scan failed')
        with patch('connection_ui.find_game_processes',side_effect=ProcessDiscoveryError(result)),patch('connection_ui.ReadOnlyGameProvider') as provider:
            page.check();observation=page.pending.result();provider.return_value.observe.assert_not_called()
        self.assertEqual((observation.failed_operation,observation.error_code,observation.fields),('Process32NextW',5,{}))
        page.poll();self.assertIn('Süreç listesi alınamadı',page.result.set.call_args[0][0]);self.assertIsNone(page.pending)

if __name__=='__main__':unittest.main()
