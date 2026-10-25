import ctypes,os,unittest
from ctypes import wintypes as w
from unittest.mock import patch
from process_access import _ObjectBasic,query_granted_access

class Function:
    def __init__(self,mask=0,status=0,length=56):self.mask=mask;self.status=status;self.length=length;self.handles=[]
    def __call__(self,handle,kind,output,size,returned):
        self.handles.append(handle)
        assert kind==0 and size==ctypes.sizeof(_ObjectBasic)
        ctypes.cast(output,ctypes.POINTER(_ObjectBasic)).contents.granted_access=self.mask
        ctypes.cast(returned,ctypes.POINTER(w.DWORD)).contents.value=self.length
        return self.status

@unittest.skipUnless(os.name=='nt','Windows metadata boundary')
class ProcessAccessTests(unittest.TestCase):
    def query(self,function):
        class Library:pass
        library=Library();library.NtQueryObject=function
        with patch('process_access.ctypes.WinDLL',return_value=library):return query_granted_access(102)

    def test_zero_mask_is_observed_not_unknown(self):
        function=Function();self.assertEqual(self.query(function),0)
        self.assertEqual(function.handles,[102])

    def test_read_mask_and_layout_match_public_structure(self):
        self.assertEqual(ctypes.sizeof(_ObjectBasic),56)
        self.assertEqual(_ObjectBasic.granted_access.offset,4)
        self.assertEqual(self.query(Function(0x1010)),0x1010)

    def test_failure_status_or_unexpected_length_remains_unknown(self):
        for function in (Function(status=-1),Function(status=1),Function(length=0),Function(length=8)):
            self.assertIsNone(self.query(function))

    def test_unavailable_export_does_not_claim_denied_access(self):
        with patch('process_access.ctypes.WinDLL',return_value=object()):
            self.assertIsNone(query_granted_access(102))

    def test_unavailable_library_does_not_claim_denied_access(self):
        with patch('process_access.ctypes.WinDLL',side_effect=OSError('unavailable')):
            self.assertIsNone(query_granted_access(102))

if __name__=='__main__':unittest.main()
