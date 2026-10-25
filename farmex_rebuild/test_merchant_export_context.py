import unittest
from dataclasses import replace
from merchant_export_context import build_source_time_fragment,ExportIdentityObservation,plan_export_identity


def observed(**kw):
    args=dict(entry_process_handle=0xffffffff,root_pointer_value=0x1000,storage_offset=0x20,data_offset=8,
              owner_eax=0x2000,storage_eax=16,data_eax=0x3000,fresh_inline_data_offset=12,
              copied_ansi=b'original',converted_unicode='decoded',final_ansi=b'converted',
              normal_returns=dict.fromkeys(('entry_process','owner','storage','data','copy','copy_to_unicode',
              'copy_cleanup','unicode_to_ansi','assign','result_cleanup','unicode_cleanup'),True))
    args.update(kw);return ExportIdentityObservation(**args)


class SourceTimeTests(unittest.TestCase):
    def test_raw_zero_based_month_and_no_zero_padding(self):
        self.assertEqual(build_source_time_fragment((3,2,1,4,0,126,0,0,0)),b'4.0.2026  1-2-3')
        self.assertEqual(build_source_time_fragment((59,58,23,31,11,126,0,0,0)),b'31.11.2026  23-58-59')

    def test_all_fields_signed_and_year_wrap(self):
        self.assertEqual(build_source_time_fragment((0xffffffff,0x80000000,0,0xffffffff,0xffffffff,0xffffffff,0,0,0)),
                         b'-1.-1.1899  0--2147483648--1')

    def test_missing_copy_is_not_replaced_by_own_clock(self):
        for v in (None,(),(1,)*8,[0]*9):
            with self.assertRaises(ValueError):build_source_time_fragment(v)


class ExportIdentityTests(unittest.TestCase):
    def test_pointer_path_uses_unsigned_storage_and_explicit_codec_output(self):
        p=plan_export_identity(observed(storage_eax=0xffffffff))
        self.assertTrue(p.complete);self.assertEqual((p.copy_address,p.copy_count),(0x3000,0xffffffff))
        self.assertEqual(p.ansi_result,b'converted');self.assertFalse(p.native_execution_verified)

    def test_inline_reads_unused_pointer_before_fresh_global_offset(self):
        p=plan_export_identity(observed(storage_eax=15))
        self.assertTrue(p.complete);self.assertEqual((p.copy_address,p.copy_count),(0x200c,255))
        self.assertIn(('read32','data',0x2008),p.steps)

    def test_inline_missing_first_data_read_is_not_skipped(self):
        p=plan_export_identity(observed(storage_eax=0,data_eax=None))
        self.assertFalse(p.complete);self.assertEqual(p.needed,('value','data_eax'))
        self.assertIsNone(p.copy_address)

    def test_missing_fresh_inline_offset_is_not_reused(self):
        p=plan_export_identity(observed(storage_eax=0,fresh_inline_data_offset=None))
        self.assertEqual(p.needed,('value','fresh_inline_data_offset'))

    def test_read_addresses_wrap_and_null_owner_does_not_early_exit(self):
        p=plan_export_identity(observed(owner_eax=0xffffffff,storage_offset=2,data_offset=3))
        self.assertIn(('read32','storage',1),p.steps);self.assertIn(('read32','data',2),p.steps)
        q=plan_export_identity(observed(owner_eax=0))
        self.assertTrue(q.complete);self.assertIn(('read32','storage',0x20),q.steps)

    def test_no_byte_roundtrip_assumption_or_encoding_fallback(self):
        p=plan_export_identity(observed(final_ansi=None))
        self.assertFalse(p.complete);self.assertIsNone(p.ansi_result)
        self.assertEqual(p.needed,('value','final_ansi'))

    def test_cleanup_failure_retains_only_assigned_result(self):
        o=observed();n=dict(o.normal_returns);n['result_cleanup']=False
        p=plan_export_identity(replace(o,normal_returns=n))
        self.assertFalse(p.complete);self.assertEqual(p.ansi_result,b'converted')
        n=dict(o.normal_returns);n['assign']=False
        q=plan_export_identity(replace(o,normal_returns=n));self.assertIsNone(q.ansi_result)

    def test_entry_process_handle_needed_despite_unused_value(self):
        p=plan_export_identity(observed(entry_process_handle=None))
        self.assertEqual(p.needed,('value','entry_process_handle'))
        self.assertFalse(any(s[0]=='read32' for s in p.steps))


if __name__=='__main__':unittest.main()
