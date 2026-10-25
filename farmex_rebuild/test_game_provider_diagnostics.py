"""Mocked Win32 boundaries only; never opens a game or changes privileges."""
import ctypes
import os
import unittest
import hashlib
import re
from pathlib import Path
from ctypes import wintypes
from unittest.mock import patch
from game_provider import ReadOnlyGameProvider, SOURCE_PROFILES,REFRESHED_SOURCE_PROFILES


class FakeFunction:
    def __init__(self, fn):
        self.fn = fn
    def __call__(self, *args):
        return self.fn(*args)


class FakeKernel:
    def __init__(self, failure=None,table=None):
        self.failure = failure
        self.table=table or SOURCE_PROFILES['us']
        self.closed = []
        self.open_rights=[]
        self.read_calls=0
        self.read_addresses=[]
        self.OpenProcess = FakeFunction(self.open)
        self.CloseHandle = FakeFunction(lambda h: self.closed.append(h))
        self.QueryFullProcessImageNameW = FakeFunction(self.query)
        self.ReadProcessMemory = FakeFunction(self.read)

    def open(self, rights, inherit, pid):
        self.open_rights.append(rights)
        if rights == 0x10 and self.failure == 'open_read':
            ctypes.set_last_error(5)
            return 0
        return 101 if rights == 0x1000 else 102

    def query(self, handle, flags, name, length):
        name.value = r'C:\NTTGame\KnightOnlineEn\KnightOnLine.exe'
        return 1

    def read(self, handle, address, value, size, count):
        self.read_calls+=1
        self.read_addresses.append(address.value)
        if self.failure == 'partial_read':
            ctypes.cast(count, ctypes.POINTER(ctypes.c_size_t)).contents.value = 2
            ctypes.set_last_error(5)
            return 0
        table = self.table
        memory = {table['root_slot']: 0x100000,
                  0x100000 + table['hp']: 300, 0x100000 + table['hp_max']: 500,
                  0x100000 + table['mp']: 100, 0x100000 + table['mp_max']: 200}
        ctypes.cast(value, ctypes.POINTER(wintypes.DWORD)).contents.value = memory[address.value]
        ctypes.cast(count, ctypes.POINTER(ctypes.c_size_t)).contents.value = 4
        return 1


@unittest.skipUnless(os.name == 'nt', 'Win32 API mock boundary tests')
class ProviderDiagnosticsTests(unittest.TestCase):
    def disk(self):
        disk = bytearray(256)
        disk[:2] = b'MZ'
        disk[0x3c:0x40] = (64).to_bytes(4, 'little')
        disk[64:68] = b'PE\0\0'
        disk[68:70] = (0x14c).to_bytes(2, 'little')
        disk[116:120] = (0x400000).to_bytes(4, 'little')
        return bytes(disk)

    def observe(self, kernel, disk=None, expected_size=None, expected_hash=None,profiles=None,profile='us',granted_access=None):
        disk=self.disk() if disk is None else disk
        expected_size=len(disk) if expected_size is None else expected_size
        expected_hash=hashlib.sha256(disk).hexdigest() if expected_hash is None else expected_hash
        with patch('game_provider.ctypes.WinDLL', return_value=kernel), patch(
                'game_provider.Path.read_bytes', return_value=disk), patch(
                'game_provider.GAME_IMAGE_PROFILES',{(expected_size,expected_hash):profiles or SOURCE_PROFILES}), patch(
                'game_provider.query_granted_access',return_value=granted_access):
            return ReadOnlyGameProvider(profile=profile).observe(123)

    def test_open_handle_without_observed_read_right_never_reads_memory(self):
        for mask in (0,0x1000):
            kernel=FakeKernel();result=self.observe(kernel,granted_access=mask)
            self.assertEqual(result.failed_operation,'validate_vm_read_handle_access')
            self.assertEqual((result.status,result.bytes_read,result.fields),('unavailable',0,{}))
            self.assertEqual(result.granted_access,mask);self.assertEqual(kernel.read_calls,0)
            self.assertTrue(result.disk_identity_verified)
            self.assertEqual(kernel.closed,[102,101])
            self.assertEqual(result.error_code,0) # own validation, not a fabricated Win32 failure

    def test_observed_read_right_still_does_not_verify_game_fields(self):
        kernel=FakeKernel();result=self.observe(kernel,granted_access=0x1010)
        self.assertEqual((result.status,result.bytes_read,result.granted_access),('candidate',24,0x1010))
        self.assertFalse(result.independently_verified)

    def test_unavailable_handle_metadata_retains_existing_read_boundary(self):
        kernel=FakeKernel('partial_read');result=self.observe(kernel,granted_access=None)
        self.assertEqual(result.failed_operation,'ReadProcessMemory(character_root)')
        self.assertIsNone(result.granted_access)

    def test_refreshed_us_uses_new_root_and_mp_offsets(self):
        kernel=FakeKernel(table=REFRESHED_SOURCE_PROFILES['us'])
        result=self.observe(kernel,profiles=REFRESHED_SOURCE_PROFILES)
        self.assertEqual((result.status,result.bytes_read),('candidate',24))
        self.assertEqual(kernel.read_addresses,[0x11289c0,0x1006d8,0x1006d4,0x100d60,0x100d5c,0x11289c0])
        self.assertFalse(result.independently_verified)

    def test_refreshed_steam_uses_its_distinct_root(self):
        kernel=FakeKernel(table=REFRESHED_SOURCE_PROFILES['steam'])
        result=self.observe(kernel,profiles=REFRESHED_SOURCE_PROFILES,profile='steam')
        self.assertEqual((result.status,result.bytes_read),('candidate',24))
        self.assertEqual(kernel.read_addresses[0],0x11e9638)
        self.assertEqual(kernel.read_addresses[-1],0x11e9638)

    def test_production_registry_keeps_build_tables_separate(self):
        from game_provider import GAME_IMAGE_PROFILES,KNOWN_GAME_IMAGE_SIZE,KNOWN_GAME_IMAGE_SHA256,REFRESHED_GAME_IMAGE_SIZE,REFRESHED_GAME_IMAGE_SHA256
        self.assertIs(GAME_IMAGE_PROFILES[(KNOWN_GAME_IMAGE_SIZE,KNOWN_GAME_IMAGE_SHA256)],SOURCE_PROFILES)
        self.assertIs(GAME_IMAGE_PROFILES[(REFRESHED_GAME_IMAGE_SIZE,REFRESHED_GAME_IMAGE_SHA256)],REFRESHED_SOURCE_PROFILES)
        self.assertNotEqual(SOURCE_PROFILES['us']['mp'],REFRESHED_SOURCE_PROFILES['us']['mp'])

    def test_unknown_disk_hash_cannot_open_or_read_game_memory(self):
        kernel=FakeKernel()
        result=self.observe(kernel,expected_hash='0'*64)
        self.assertEqual(result.failed_operation,'validate_disk_identity')
        self.assertEqual((result.status,result.bytes_read,result.fields),('unavailable',0,{}))
        self.assertEqual(kernel.open_rights,[0x1000]);self.assertEqual(kernel.read_calls,0)
        self.assertEqual(result.image_sha256,hashlib.sha256(self.disk()).hexdigest())
        self.assertFalse(result.disk_identity_verified)
        self.assertEqual(kernel.closed,[101])

    def test_wrong_disk_size_cannot_open_memory_even_when_digest_matches(self):
        kernel=FakeKernel()
        result=self.observe(kernel,expected_size=len(self.disk())+1)
        self.assertEqual(result.failed_operation,'validate_disk_identity')
        self.assertEqual(kernel.open_rights,[0x1000]);self.assertEqual(kernel.read_calls,0)

    def test_pe_gate_still_applies_to_identity_matched_fixture(self):
        disk=bytearray(self.disk());disk[68:70]=(0x8664).to_bytes(2,'little')
        kernel=FakeKernel();result=self.observe(kernel,disk=bytes(disk))
        self.assertEqual(result.failed_operation,'validate_disk_image')
        self.assertEqual(kernel.open_rights,[0x1000]);self.assertEqual(kernel.read_calls,0)

    def test_python_and_native_use_same_recorded_identity(self):
        from game_provider import KNOWN_GAME_IMAGE_SIZE,KNOWN_GAME_IMAGE_SHA256,REFRESHED_GAME_IMAGE_SIZE,REFRESHED_GAME_IMAGE_SHA256
        source=(Path(__file__).parent/'native/vitals_bridge.c').read_text(encoding='utf-8')
        for name,expected_size,expected_digest in (
                ('expected_game_sha256',KNOWN_GAME_IMAGE_SIZE,KNOWN_GAME_IMAGE_SHA256),
                ('refreshed_game_sha256',REFRESHED_GAME_IMAGE_SIZE,REFRESHED_GAME_IMAGE_SHA256)):
            array=re.search(name+r'\[32\]=\{(.*?)\}',source,re.S).group(1)
            digest=bytes(int(v,16) for v in re.findall(r'0x([0-9a-fA-F]{2})',array)).hex()
            size=int(re.search(name+r',(\d+),',source).group(1))
            self.assertEqual((expected_size,expected_digest),(size,digest))

    def test_open_read_failure_reports_exact_api(self):
        kernel = FakeKernel('open_read')
        result = self.observe(kernel)
        self.assertEqual(result.failed_operation, 'OpenProcess(PROCESS_VM_READ)')
        self.assertTrue(result.disk_identity_verified)
        self.assertEqual((result.error_code, result.bytes_read), (5, 0))
        self.assertEqual(kernel.closed, [101])

    def test_partial_read_is_counted_and_not_accepted(self):
        kernel = FakeKernel('partial_read')
        result = self.observe(kernel)
        self.assertEqual(result.failed_operation, 'ReadProcessMemory(character_root)')
        self.assertEqual((result.error_code, result.bytes_read, result.fields), (5, 2, {}))
        self.assertEqual(kernel.closed, [102, 101])

    def test_candidate_still_needs_independent_verification(self):
        kernel = FakeKernel()
        result = self.observe(kernel)
        self.assertEqual((result.status, result.bytes_read), ('candidate', 24))
        self.assertFalse(result.independently_verified)
        self.assertEqual(result.fields['hp'], 300)
        self.assertTrue(result.disk_identity_verified)
        self.assertEqual(result.failed_operation, '')
        self.assertEqual(kernel.closed, [102, 101])


if __name__ == '__main__':
    unittest.main()
