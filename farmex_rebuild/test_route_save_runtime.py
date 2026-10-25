import sys,tempfile,unittest
from pathlib import Path
from name_codec import WindowsNameCodec
from route_save_runtime import RouteSaveContext,save_source_route_panel
from source_route_save import write_source_route_dynamic_calls


class RouteSaveGuardTests(unittest.TestCase):
    def test_empty_name_and_empty_count_do_not_reach_directory_or_writer(self):
        def forbidden(*args):raise AssertionError('unreached callback')
        p=save_source_route_panel(lambda:'',forbidden,forbidden,forbidden,forbidden)
        self.assertEqual(p.status,'name_required')
        p=save_source_route_panel(lambda:'name',lambda:0,forbidden,forbidden,forbidden)
        self.assertEqual(p.status,'empty_rows_preserve')


@unittest.skipUnless(sys.platform=='win32','Explicit owned Windows codec')
class RouteSaveRuntimeTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.codec=WindowsNameCodec(1254)
        self.context=RouteSaveContext(self.temp.name,self.codec)
    def tearDown(self):self.temp.cleanup()
    def writer(self,path,count,row):
        return write_source_route_dynamic_calls(path.encode('ascii'),count,row,lambda _:0,lambda *args:1)

    def test_three_fresh_name_reads_and_reached_ansi_row_conversion(self):
        names=iter(('checked','fresh-path','notice-name'));events=[]
        def name():value=next(names);events.append(('name',value));return value
        def writer(path,count,row):
            events.append(('writer',Path(path).name,count));return self.writer(path,count,row)
        def row(index):events.append(('row',index));return ('NPC','ışık','extra')
        p=save_source_route_panel(name,lambda:1,lambda:self.context,row,writer)
        self.assertEqual(Path(p.path).name,'fresh-path.R');self.assertEqual(p.notice_name,'notice-name')
        self.assertEqual(events,[('name','checked'),('name','fresh-path'),('writer','fresh-path.R',1),('row',0),('name','notice-name')])
        self.assertEqual(p.write.calls[2].value,self.codec.encode('ışık')[0])

    def test_path_confinement_rejects_traversal_before_writer(self):
        def forbidden(*args):raise AssertionError('writer must not run')
        for name in ('../outside','..\\outside','C:\\outside','sub/name','x\0y'):
            p=save_source_route_panel(lambda:name,lambda:1,lambda:self.context,forbidden,forbidden)
            self.assertEqual(p.status,'save_incomplete',name)

    def test_missing_directory_stops_before_second_name_and_row_reads(self):
        calls=[]
        def name():calls.append('name');return 'test'
        def forbidden(*args):raise AssertionError('not reached')
        context=RouteSaveContext(str(Path(self.temp.name)/'absent'),self.codec)
        p=save_source_route_panel(name,lambda:1,lambda:context,forbidden,forbidden)
        self.assertEqual(p.status,'directory_missing');self.assertEqual(calls,['name'])

    def test_bool_failure_still_reaches_third_name_but_success_is_false(self):
        names=[]
        def name():names.append('read');return 'own'
        def writer(path,count,row):
            return write_source_route_dynamic_calls(b'C:\\own.R',count,row,lambda _:-1,lambda *args:0)
        p=save_source_route_panel(name,lambda:1,lambda:self.context,lambda _:('Town','0','0'),writer)
        self.assertEqual(p.status,'write_calls_completed');self.assertEqual(len(names),3)
        self.assertFalse(p.write.writes_succeeded);self.assertEqual(len(p.write.calls),4)

    def test_no_trim_or_extension_deduplication(self):
        for name,expected in [('  ','  .R'),('already.R','already.R.R')]:
            p=save_source_route_panel(lambda:name,lambda:1,lambda:self.context,lambda _:('Town','0','0'),self.writer)
            self.assertEqual(Path(p.path).name,expected);self.assertTrue(p.write.writes_succeeded)


if __name__=='__main__':unittest.main()
