import unittest
from quest_metadata import (QuestMetadataFrame,QuestMetadataObservation as Observation,
                            QuestMetadataDatabase as Database,QuestMetadataRecord as Record)


class Sink:
    def __init__(self,rows=('1','0'),selection=0):self.rows=list(rows);self.selection=selection;self.caption_reads=[]
    def selected_index(self):return self.selection
    def count(self):return len(self.rows)
    def caption(self,index):self.caption_reads.append(index);return self.rows[index]


def capture(**changes):
    returned={i:True for i in range(-1,100)}
    values=dict(selection_returned=True,setup_returns=returned,caption_returns=returned,
        conversion_returns=returned,cleanup_returns=returned,read_returns=returned,epilogue_returns=returned,
        database=Database(0x1000,(Record(111,0x2000,444),Record(222,0x3000,555))))
    values.update(changes);return Observation(**values)


class QuestMetadataTests(unittest.TestCase):
    def test_selected_caption_index_differs_from_ui_row(self):
        sink=Sink();f=QuestMetadataFrame('cancel',sink);p=f.advance(capture())
        self.assertEqual((p.complete,p.processed_rows),(True,1))
        self.assertEqual(p.reads,((0,1,0x1020,0x3000,'direct_data_pointer'),(0,1,0x301c,555,'guarded_0045dc44')))

    def test_take_all_only_reads_entry0_not_selected_take_or_guarded_helper(self):
        f=QuestMetadataFrame('take_all',Sink())
        p=f.advance(capture(database=Database(0x1000,(Record(111),Record(222))),read_returns={}))
        self.assertEqual((p.complete,p.processed_rows),(True,2))
        self.assertEqual([r[3:] for r in p.reads],[(222,'direct_entry0'),(111,'direct_entry0')])

    def test_no_selection_still_requires_helper_setup_and_epilogue(self):
        sink=Sink(selection=-1);f=QuestMetadataFrame('cancel',sink)
        p=f.advance(capture(setup_returns={}))
        self.assertEqual(p.needed,('setup_returns',-1));self.assertEqual(sink.caption_reads,[])
        p=f.advance(Observation(setup_returns={-1:True},epilogue_returns={-1:True}))
        self.assertEqual((p.status,p.reads),('no_selection',()))

    def test_caption_freezes_while_conversion_return_waits(self):
        sink=Sink();f=QuestMetadataFrame('cancel',sink)
        self.assertEqual(f.advance(capture(conversion_returns={})).needed,('conversion_returns',0))
        sink.rows[0]='0'
        p=f.advance(capture())
        self.assertEqual(p.reads[-1][1:4],(1,0x301c,555))
        self.assertEqual(sink.caption_reads,[0])

    def test_count_is_fresh_after_child_return(self):
        sink=Sink();f=QuestMetadataFrame('take_all',sink)
        p=f.advance(capture(epilogue_returns={}))
        self.assertEqual((p.needed,len(p.reads)),(('epilogue_returns',0),1))
        sink.rows.pop()
        p=f.advance(Observation(epilogue_returns={0:True}))
        self.assertEqual((p.complete,p.processed_rows,len(p.reads)),(True,1,1))

    def test_guarded_result_and_pointer_survive_later_gaps_without_database_replay(self):
        f=QuestMetadataFrame('cancel',Sink())
        p=f.advance(capture(read_returns={}))
        self.assertEqual((p.needed,len(p.reads)),(('read_returns',0),1))
        p=f.advance(Observation(read_returns={0:True},epilogue_returns={0:True}))
        self.assertTrue(p.complete);self.assertEqual(p.reads[-1][2:4],(0x301c,555))

    def test_pointer_prefix_survives_unknown_guarded_result(self):
        f=QuestMetadataFrame('cancel',Sink())
        p=f.advance(capture(database=Database(0x1000,(Record(),Record(data_pointer_dword=0x3000)))))
        self.assertEqual((p.needed,len(p.reads)),(('field_1c_dword',0),1))
        p=f.advance(capture(database=Database(0x9999,(Record(),Record(data_pointer_dword=0x9999,field_1c_dword=555)))))
        self.assertEqual(p.reads[-1][2:4],(0x301c,555))

    def test_invalid_caption_exception_is_not_coerced_to_record0(self):
        f=QuestMetadataFrame('cancel',Sink(('bad',)))
        p=f.advance(capture())
        self.assertEqual(p.needed[:2],('caption_exception_outcome',0));self.assertEqual(p.reads,())

    def test_null_database_and_outside_fixture_are_distinct_from_empty_success(self):
        f=QuestMetadataFrame('cancel',Sink())
        self.assertEqual(f.advance(capture(database=Database(0,(Record(),Record())))).needed,('native_null_record_array',0))
        f=QuestMetadataFrame('cancel',Sink(('-1',)))
        p=f.advance(capture())
        self.assertEqual((p.status,p.done,p.complete),('outside_fixture_database',True,False))

    def test_cancel_all_reads_each_1c_and_cancel_preserves_known_prefix(self):
        f=QuestMetadataFrame('cancel_all',Sink());p=f.advance(capture(epilogue_returns={}))
        self.assertEqual(len(p.reads),2)
        f.cancel('profile_change')
        self.assertEqual(f.advance(capture()).status,'cancelled')
        self.assertEqual(len(f.result.reads),2)

    def test_large_loop_yields_and_completed_frame_is_idempotent(self):
        f=QuestMetadataFrame('take_all',Sink(('0',)*30))
        p=f.advance(capture())
        self.assertEqual(p.status,'continuation')
        while not p.done:p=f.advance(capture())
        self.assertEqual((p.processed_rows,len(p.reads)),(30,30))
        self.assertIs(f.advance(object()),p)


if __name__=='__main__':unittest.main()
