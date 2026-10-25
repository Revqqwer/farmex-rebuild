import unittest
from quest_collection import (QuestCollection,QuestVectorHeader as Header,QuestAppendFrame,
                               QuestAppendObservation as Observation,quest_extent)
from quest_record import QuestRecord


def record(index=7):return QuestRecord(index,0x4000,b'a.lua',15,5,b'Quest',b'NPC')


def capture(**changes):
    fields=dict(size_header=Header(0x1000,0x1000),capacity_header=Header(0x1000,capacity_end=0x1038),
                size_returned=True,capacity_returned=True,inplace_returned=True,inplace_end_dword=0x101c,
                reallocate_returned=True,reallocate_end_returned=True,post_header=Header(0x1000,0x101c,0x1038))
    fields.update(changes);return Observation(**fields)


class QuestExtentTests(unittest.TestCase):
    def test_null_begin_does_not_read_unused_end_or_capacity(self):
        self.assertEqual(quest_extent(Header(0,object(),object())).raw_count,0)
        self.assertEqual(quest_extent(Header(0,object(),object()),True).reads,((0x10,0),))

    def test_signed_difference_divides_toward_zero_then_returns_raw_dword(self):
        self.assertEqual(quest_extent(Header(100,72)).raw_count,0xffffffff)
        self.assertEqual(quest_extent(Header(100,73)).raw_count,0)
        self.assertEqual(quest_extent(Header(0xfffffff0,12)).raw_count,1)

    def test_missing_header_field_is_not_zero(self):
        self.assertEqual(quest_extent(Header(0x1000)).needed,'end')
        self.assertEqual(quest_extent(Header(0x1000),True).needed,'capacity_end')


class QuestAppendTests(unittest.TestCase):
    def test_inplace_append_and_header_store(self):
        state=QuestCollection(header=Header(0x1000,0x1000,0x1038));f=QuestAppendFrame(state,record())
        p=f.advance(capture())
        self.assertEqual((p.complete,p.branch,p.committed), (True,'inplace',True))
        self.assertEqual((state.records,state.header.end,state.revision),((record(),),0x101c,1))

    def test_reallocate_uses_explicit_new_header_not_invented_growth(self):
        state=QuestCollection();f=QuestAppendFrame(state,record())
        p=f.advance(capture(size_header=Header(0),capacity_header=Header(0),
            inplace_returned=object(),post_header=Header(0x8000,0x801c,0x8054)))
        self.assertEqual((p.complete,p.branch,state.header.capacity_end),(True,'reallocate',0x8054))

    def test_inplace_end_write_and_record_prefix_survive_missing_post_capture(self):
        state=QuestCollection(header=Header(0x1000,0x1000,0x1038));f=QuestAppendFrame(state,record())
        p=f.advance(capture(post_header=None))
        self.assertEqual((p.complete,p.committed,p.needed),(False,True,('post_header',)))
        self.assertEqual((len(state.records),state.header.end),(1,0x101c))
        p=f.advance(Observation(post_header=Header(0x1000,0x101c,0x1038)))
        self.assertTrue(p.complete);self.assertEqual((len(state.records),state.revision),(1,1))

    def test_reallocate_return_does_not_fabricate_unknown_post_state(self):
        state=QuestCollection();f=QuestAppendFrame(state,record())
        p=f.advance(capture(size_header=Header(0),capacity_header=Header(0),post_header=None))
        self.assertEqual((p.needed,state.records),(('post_header',),()))
        self.assertTrue(f.advance(Observation(post_header=Header(0x1000,0x101c,0x101c))).complete)

    def test_helper_return_and_eax_are_separate_gaps(self):
        state=QuestCollection();f=QuestAppendFrame(state,record())
        self.assertEqual(f.advance(capture(inplace_returned=None)).needed,('inplace_returned',))
        self.assertEqual(f.advance(Observation(inplace_returned=True)).needed,('inplace_end_dword',))
        self.assertEqual(state.records,())
        self.assertTrue(f.advance(Observation(inplace_end_dword=0x101c,post_header=Header(0x1000,0x101c))).complete)

    def test_size_and_capacity_queries_have_independent_fresh_headers(self):
        state=QuestCollection();f=QuestAppendFrame(state,record())
        p=f.advance(capture(size_header=Header(0,end=object()),capacity_header=Header(0x1000,capacity_end=0x101c)))
        self.assertEqual((p.complete,p.branch),(True,'inplace'))

    def test_unsigned_branch_comparison_is_not_signed_python_compare(self):
        state=QuestCollection((record(),));f=QuestAppendFrame(state,record(8))
        p=f.advance(capture(size_header=Header(0x1000,0x101c),capacity_header=Header(0x1000,capacity_end=0xfe4),
                            inplace_returned=None))
        self.assertEqual((p.branch,p.needed),('inplace',('inplace_returned',)))

    def test_external_collection_change_is_not_overwritten(self):
        state=QuestCollection();f=QuestAppendFrame(state,record())
        f.advance(capture(inplace_returned=None));state.records=(record(8),);state.revision+=1
        self.assertEqual(f.advance(capture()).status,'collection_conflict')
        self.assertEqual(state.records,(record(8),))

    def test_size_and_post_count_mismatch_remain_unresolved(self):
        state=QuestCollection();f=QuestAppendFrame(state,record())
        self.assertEqual(f.advance(capture(size_header=Header(0x1000,0x101c))).status,'unresolved_captured_size')
        state=QuestCollection();f=QuestAppendFrame(state,record())
        p=f.advance(capture(post_header=Header(0x1000,0x1038)))
        self.assertEqual((p.complete,p.status,len(state.records)),(False,'unresolved_post_header',1))

    def test_reallocate_branch_gets_end_iterator_before_calling_growth_helper(self):
        state=QuestCollection();f=QuestAppendFrame(state,record())
        p=f.advance(capture(size_header=Header(0),capacity_header=Header(0),reallocate_end_returned=None))
        self.assertEqual(p.needed,('reallocate_end_returned',))
        self.assertFalse(any(helper=='004d71b0' for helper,_ in p.calls))
        p=f.advance(capture(size_header=Header(0),capacity_header=Header(0)))
        self.assertTrue(p.complete)


if __name__=='__main__':unittest.main()
