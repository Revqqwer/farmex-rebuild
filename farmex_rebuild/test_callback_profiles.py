import unittest
from native_profile_versions import LEGACY_SOURCE_SHA256,CURRENT_SOURCE_SHA256,versioned_callback_globals

class CallbackProfileTests(unittest.TestCase):
 def test_old_US_field_differs_from_current_and_Steam(self):
  old_us=versioned_callback_globals(LEGACY_SOURCE_SHA256,'us');new_us=versioned_callback_globals(CURRENT_SOURCE_SHA256,'us')
  self.assertEqual((old_us[0x553e80],old_us[0x5540d4],old_us[0x554204]),(0x111563c,0x370,0x8c))
  self.assertEqual((new_us[0x553e80],new_us[0x5540d4],new_us[0x554204]),(0x1128a7c,0x3b0,0x8c))
  self.assertEqual(versioned_callback_globals(LEGACY_SOURCE_SHA256,'steam')[0x553e80],0x11ebab0)
  self.assertEqual(versioned_callback_globals(CURRENT_SOURCE_SHA256,'steam')[0x553e80],0x11eaab0)
 def test_source_hash_required_and_conflicting_offsets_rejected(self):
  with self.assertRaises(ValueError):versioned_callback_globals('unknown','us')
  with self.assertRaises(ValueError):versioned_callback_globals(CURRENT_SOURCE_SHA256,'unknown')
  with self.assertRaises(ValueError):versioned_callback_globals(CURRENT_SOURCE_SHA256,'us',runtime_globals={0x5540d4:0x370})
 def test_projection_immutable_and_extra_captured_slot_explicit(self):
  r=versioned_callback_globals(CURRENT_SOURCE_SHA256,'steam',runtime_globals={0x554228:123})
  self.assertEqual(r[0x554228],123)
  with self.assertRaises(TypeError):r[0x5540d4]=0
  with self.assertRaises(ValueError):versioned_callback_globals(CURRENT_SOURCE_SHA256,'steam',runtime_globals={0x554228:True})

if __name__=='__main__':unittest.main()
