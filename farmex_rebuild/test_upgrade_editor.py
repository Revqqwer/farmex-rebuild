import unittest
from dataclasses import replace
from upgrade_editor import UpgradeEditorFrame,UpgradeEditorObservation as O
from test_target_id_frames import sample


class Sink:
    def __init__(self,rows=None):self.rows=[] if rows is None else rows;self.text='old';self.writes=[];self.counts=[]
    def count(self):self.counts.append(len(self.rows));return len(self.rows)
    def set_checked(self,index,value):self.rows[index]['checked']=value;self.writes.append(index)
    def set_anvil_text(self,text):self.text=text;self.writes.append(text)


class UpgradeEditorTests(unittest.TestCase):
    def test_nested_onchange_must_finish_before_id_text_cleanup(self):
        sink=Sink();ready=[False];sink.anvil_text_ready=lambda:ready[0]
        f=UpgradeEditorFrame('target_id',sink)
        p=f.advance(O(target=sample(7),format_returned=True,cleanup_returned=True))
        self.assertEqual(sink.text,'7');self.assertEqual(p.needed,('nested_parameters',))
        self.assertNotIn('cleanup_returned',f.cache)
        ready[0]=True;p=f.advance(O(cleanup_returned=True))
        self.assertTrue(p.complete);self.assertEqual(sink.writes,['7'])

    def test_selection_gate_is_required_and_zero_does_not_read_rows(self):
        sink=Sink([dict(caption='invalid',checked=False)]);f=UpgradeEditorFrame('select_all',sink)
        self.assertEqual(f.advance().needed,('gate_byte',));self.assertEqual(sink.counts,[])
        p=f.advance(O(gate_byte=0,target={}))
        self.assertTrue(p.complete);self.assertEqual(p.status,'gate_closed');self.assertEqual(sink.counts,[])

    def test_select_all_is_not_toggle_and_preserves_rows_and_invalid_captions(self):
        rows=[dict(caption='bad',subitems=['x'],checked=True),dict(caption='bad',subitems=[],checked=False)]
        sink=Sink(rows);f=UpgradeEditorFrame('select_all',sink);p=f.advance(O(gate_byte=255))
        self.assertTrue(p.complete);self.assertEqual(sink.counts,[2,2,2]);self.assertEqual(sink.writes,[0,1])
        self.assertTrue(all(row['checked'] for row in rows));self.assertEqual(rows[0]['subitems'],['x'])
        self.assertIs(f.advance({}),p)

    def test_count_is_fresh_can_grow_or_shrink_between_setters(self):
        sink=Sink([dict(checked=False)]);original=sink.set_checked
        def grow(index,value):
            original(index,value)
            if index==0:sink.rows.append(dict(checked=False))
        sink.set_checked=grow
        self.assertEqual(UpgradeEditorFrame('select_all',sink).advance(O(gate_byte=1)).selected_rows,2)
        sink=Sink([dict(checked=False),dict(checked=False)]);original=sink.set_checked
        def shrink(index,value):original(index,value);sink.rows.pop()
        sink.set_checked=shrink
        self.assertEqual(UpgradeEditorFrame('select_all',sink).advance(O(gate_byte=1)).selected_rows,1)

    def test_chunk_continuation_retains_gate_and_does_not_repeat_setters(self):
        sink=Sink([dict(checked=False) for _ in range(80)]);f=UpgradeEditorFrame('select_all',sink)
        p=f.advance(O(gate_byte=1));self.assertFalse(p.done)
        p=f.advance(O(gate_byte=0));self.assertTrue(p.complete)
        self.assertEqual(sink.writes,list(range(80)));self.assertEqual(f.cache['gate_byte'],1)

    def test_id_event_ignores_gate_and_zero_target_preserves_text(self):
        sink=Sink();f=UpgradeEditorFrame('target_id',sink)
        p=f.advance(O(gate_byte={},target=sample(0),format_returned={},cleanup_returned={}))
        self.assertTrue(p.complete);self.assertEqual(p.status,'no_target');self.assertEqual(sink.text,'old')

    def test_target_normal_format_and_cleanup_are_separate(self):
        sink=Sink();f=UpgradeEditorFrame('target_id',sink)
        p=f.advance(O(target=replace(sample(0xffffffff),getter_returned=False)))
        self.assertEqual(p.needed,('target',('getter_returned',)));self.assertEqual(sink.writes,[])
        p=f.advance(O(target=sample(1)));self.assertEqual(p.needed,('format_returned',))
        self.assertEqual(sink.writes,[])
        p=f.advance(O(format_returned=True));self.assertEqual(p.needed,('cleanup_returned',))
        self.assertEqual(sink.writes,['-1']);sink.text='manual'
        p=f.advance(O(cleanup_returned=True));self.assertTrue(p.complete);self.assertEqual(sink.text,'manual')
        self.assertEqual(sink.writes,['-1']);self.assertFalse(p.native_execution_verified)

    def test_signed32_full_target_is_formatted_without_word_truncation(self):
        for target,expected in ((65536,'65536'),(0x80000000,'-2147483648'),(0x7fffffff,'2147483647')):
            sink=Sink();p=UpgradeEditorFrame('target_id',sink).advance(O(target=sample(target),format_returned=True,cleanup_returned=True))
            self.assertTrue(p.complete);self.assertEqual(sink.text,expected)

    def test_sink_failure_retains_prefix_and_cancel_is_terminal(self):
        sink=Sink([dict(checked=False),dict(checked=False)]);original=sink.set_checked
        def fail(index,value):
            if index==1:raise ValueError('deleted row')
            original(index,value)
        sink.set_checked=fail;f=UpgradeEditorFrame('select_all',sink);p=f.advance(O(gate_byte=1))
        self.assertFalse(p.complete);self.assertTrue(p.done);self.assertEqual(sink.writes,[0])
        g=UpgradeEditorFrame('target_id',Sink());p=g.cancel('profile');self.assertIs(g.advance(O(target=sample(4))),p)


if __name__=='__main__':unittest.main()
