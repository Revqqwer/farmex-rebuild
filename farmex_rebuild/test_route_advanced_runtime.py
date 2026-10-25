import unittest
from route_command_runtime import (append_source_route_advanced,CAMP_RANDOM,CAMP_MANUAL,CAMP_TEXT,SPEED_FLAGS)
from test_route_command_runtime import Sink


class RouteAdvancedTests(unittest.TestCase):
    def test_speed_priority_and_none_default_read_only_reached_flags(self):
        for flags,expected,reads in [((True,True,True),'0',1),((False,True,True),'1',2),
                                     ((False,False,True),'3',3),((False,False,False),'0',3)]:
            seen=[];sink=Sink()
            def read(path):seen.append(path);return flags[SPEED_FLAGS.index(path)]
            p=append_source_route_advanced('speed',sink,read)
            self.assertTrue(p.complete);self.assertEqual(sink.rows,[['Change Speed Hack',[expected,'-']]])
            self.assertEqual(seen,list(SPEED_FLAGS[:reads]))

    def test_speed_later_getters_observe_fresh_changed_value(self):
        values=dict.fromkeys(SPEED_FLAGS,False);sink=Sink()
        def read(path):
            if path==SPEED_FLAGS[1]:values[SPEED_FLAGS[2]]=True
            return values[path]
        p=append_source_route_advanced('speed',sink,read)
        self.assertTrue(p.complete);self.assertEqual(sink.rows[0][1],['3','-'])

    def test_camp_random_preempts_manual_and_none_maps_randomize(self):
        for random in (True,False):
            seen=[];sink=Sink()
            def read(path):
                seen.append(path)
                if path==CAMP_RANDOM:return random
                if path==CAMP_MANUAL:return False
                self.fail('manual text must not be read')
            p=append_source_route_advanced('camp',sink,read)
            self.assertTrue(p.complete);self.assertEqual(sink.rows,[['Change Camp',['Randomize','-']]])
            self.assertEqual(seen,[CAMP_RANDOM] if random else [CAMP_RANDOM,CAMP_MANUAL])

    def test_manual_camp_uses_low_dword_signed32_zero_and_default1(self):
        for text,expected in [('2','2'),('-2','-2'),('0','Randomize'),('$100000000','Randomize'),
                              ('$FFFFFFFF','-1'),('$180000000','-2147483648'),('bad','1')]:
            values={CAMP_RANDOM:False,CAMP_MANUAL:True,CAMP_TEXT:text};sink=Sink()
            def read(path):
                self.assertEqual(sink.rows,[]);return values[path]
            p=append_source_route_advanced('camp',sink,read)
            self.assertTrue(p.complete);self.assertEqual(sink.rows,[['Change Camp',[expected,'-']]])
            self.assertEqual(p.integer.used_default,text=='bad')

    def test_manual_text_failure_precedes_any_row_add(self):
        sink=Sink()
        def read(path):
            if path==CAMP_RANDOM:return False
            if path==CAMP_MANUAL:return True
            raise OSError('own text unavailable')
        p=append_source_route_advanced('camp',sink,read)
        self.assertFalse(p.complete);self.assertEqual(p.phase,'camp_text');self.assertEqual(sink.rows,[])

    def test_late_setter_failure_keeps_caption_and_first_parameter(self):
        for method,caption,first in [('camp','Change Camp','Randomize'),('speed','Change Speed Hack','0')]:
            sink=Sink('sub2');p=append_source_route_advanced(method,sink,lambda _:True)
            self.assertFalse(p.complete);self.assertEqual(sink.rows,[[caption,[first]]])

    def test_unknown_method_and_invalid_boolean_do_not_add(self):
        sink=Sink()
        with self.assertRaises(ValueError):append_source_route_advanced('unknown',sink,lambda _:True)
        p=append_source_route_advanced('speed',sink,lambda _:1)
        self.assertFalse(p.complete);self.assertEqual(sink.rows,[])


if __name__=='__main__':unittest.main()
