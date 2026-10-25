import sys,tempfile,unittest
from pathlib import Path
from route_load_runtime import stream_source_route,load_source_route_choice,WindowsRouteReader
from route_save_runtime import RouteSaveContext
from name_codec import WindowsNameCodec


class Sink:
    def __init__(self,events):self.events=events;self.rows=[['old',['keep']]]
    def clear(self):self.events.append('clear');self.rows=[]
    def add_row(self):self.events.append('add');self.rows.append(['',[]]);return len(self.rows)-1
    def set_caption(self,index,text):self.events.append(('caption',text));self.rows[index][0]=text
    def add_subitem(self,index,text):self.events.append(('subitem',text));self.rows[index][1].append(text)


class Reader:
    def __init__(self,events,count=1,exists=True):self.events=events;self.n=count;self.present=exists
    def exists(self):self.events.append('exists');return self.present
    def count(self):self.events.append('count');return self.n
    def value(self,index,prefix):self.events.append(('read',index,prefix));return {b'ISLEM':b'Town',b'Sub1':b'1',b'Sub2':b'2'}[prefix]


class Codec:
    def decode(self,value):return value.decode('ascii')


class RouteLoadStreamingTests(unittest.TestCase):
    def test_missing_and_nonpositive_counts_preserve_without_clearing(self):
        for count,exists,status in [(1,False,'file_missing_preserve'),(0,True,'nonpositive_count_preserve'),(0xffffffff,True,'nonpositive_count_preserve'),(0x80000000,True,'nonpositive_count_preserve')]:
            events=[];sink=Sink(events)
            p=stream_source_route(Reader(events,count,exists),Codec(),sink)
            self.assertTrue(p.complete);self.assertEqual(p.status,status);self.assertEqual(sink.rows,[['old',['keep']]])
            self.assertEqual(events,['exists','count'] if exists else ['exists'])

    def test_source_order_reads_three_fields_then_adds_and_sets_caption_and_subitems(self):
        events=[];sink=Sink(events);p=stream_source_route(Reader(events),Codec(),sink)
        self.assertTrue(p.complete);self.assertEqual(p.completed_rows,1)
        self.assertEqual(events,['exists','count','clear',('read',0,b'ISLEM'),('read',0,b'Sub1'),('read',0,b'Sub2'),
                                 'add',('caption','Town'),('subitem','1'),('subitem','2')])
        self.assertEqual(sink.rows,[['Town',['1','2']]])

    def test_read_error_after_first_row_retains_completed_prefix_without_second_add(self):
        events=[];reader=Reader(events,2);original=reader.value
        def value(index,prefix):
            if index==1:raise OSError('injected read failure')
            return original(index,prefix)
        reader.value=value;sink=Sink(events);p=stream_source_route(reader,Codec(),sink)
        self.assertFalse(p.complete);self.assertEqual(p.completed_rows,1);self.assertTrue(p.cleared)
        self.assertEqual(p.phase,'read_ISLEM_1');self.assertEqual(sink.rows,[['Town',['1','2']]])

    def test_caption_conversion_failure_keeps_already_added_blank_row(self):
        events=[];sink=Sink(events)
        class BadCodec:
            def decode(self,value):raise ValueError('own caption conversion failure')
        p=stream_source_route(Reader(events),BadCodec(),sink)
        self.assertFalse(p.complete);self.assertEqual(p.phase,'caption_0');self.assertEqual(sink.rows,[['',[]]])

    def test_second_subitem_failure_keeps_caption_and_first_subitem(self):
        events=[];sink=Sink(events)
        class BadSecondCodec:
            def decode(self,value):
                if value==b'2':raise ValueError('own subitem conversion failure')
                return value.decode('ascii')
        p=stream_source_route(Reader(events),BadSecondCodec(),sink)
        self.assertFalse(p.complete);self.assertEqual(p.phase,'sub2_0');self.assertEqual(sink.rows,[['Town',['1']]])

    def test_own_budget_and_invalid_count_preserve_before_clear(self):
        for count in (True,-1,0x100000000,2):
            events=[];sink=Sink(events);p=stream_source_route(Reader(events,count),Codec(),sink,max_rows=1)
            self.assertFalse(p.complete);self.assertFalse(p.cleared);self.assertEqual(sink.rows,[['old',['keep']]])


@unittest.skipUnless(sys.platform=='win32','Real own Windows profile API and codec')
class RouteLoadNativeTests(unittest.TestCase):
    def test_actual_raw_unknown_command_empty_keys_and_truncation(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'own.R';path.write_bytes(b'[Count]\nValue=2\n[ROUTE]\nISLEM0=CustomUnknown\nSub10=\xfd\xfe\xfd\nISLEM1='+b'A'*600+b'\n')
            sink=Sink([]);p=load_source_route_choice(path.name,RouteSaveContext(directory,WindowsNameCodec(1254)),sink)
            self.assertTrue(p.complete);self.assertEqual(p.completed_rows,2)
            self.assertEqual(sink.rows,[['CustomUnknown',['ışı','']],['A'*254,['','']]])

    def test_placeholder_missing_nonpositive_files_and_path_confinement(self):
        with tempfile.TemporaryDirectory() as directory:
            context=RouteSaveContext(directory,WindowsNameCodec(1254))
            for name in ('Rota Seciniz !','missing.R'):
                sink=Sink([]);p=load_source_route_choice(name,context,sink)
                self.assertEqual(p.status,'file_missing_preserve');self.assertEqual(sink.rows,[['old',['keep']]])
            for name in ('../outside.R','..\\outside.R','C:\\outside.R'):
                p=load_source_route_choice(name,context,Sink([]),reader_factory=lambda _:self.fail('must not construct reader'))
                self.assertFalse(p.complete)
            path=Path(directory)/'zero.R';path.write_bytes(b'[Count]\nValue=-1\n')
            sink=Sink([]);p=stream_source_route(WindowsRouteReader(str(path)),context.codec,sink)
            self.assertEqual(p.status,'nonpositive_count_preserve');self.assertFalse(p.cleared)


if __name__=='__main__':unittest.main()
