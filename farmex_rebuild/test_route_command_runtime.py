import unittest
from route_command_runtime import append_source_route_command


class Sink:
    def __init__(self,fail=None):self.rows=[];self.events=[];self.fail=fail
    def before(self,phase):
        self.events.append(phase)
        if self.fail==phase:raise OSError('own setter failure')
    def add_row(self):self.before('add');self.rows.append(['',[]]);return len(self.rows)-1
    def set_caption(self,index,text):self.before('caption');self.rows[index][0]=text
    def add_subitem(self,index,text):self.before('sub%d'%(len(self.rows[index][1])+1));self.rows[index][1].append(text)


class RouteCommandTests(unittest.TestCase):
    def test_constants_use_two_dash_placeholders_and_append_in_order(self):
        sink=Sink()
        for method,caption in [('town','Town'),('gate_skill','Gate Skill'),('sit','Otur'),('stand','Kalk')]:
            p=append_source_route_command(method,sink)
            self.assertTrue(p.complete);self.assertEqual(sink.rows[-1],[caption,['-','-']])
        self.assertEqual(sink.events,['add','caption','sub1','sub2']*4)

    def test_wait_own_integer_policy_preserves_signed64_and_default5(self):
        for text,expected,defaulted in [('7','7',False),('-2','-2',False),('$FFFFFFFFFFFFFFFF','-1',False),
                                      ('bad','5',True),('','5',True),('5 ','5',True)]:
            sink=Sink();p=append_source_route_command('wait',sink,lambda:text)
            self.assertTrue(p.complete);self.assertEqual(sink.rows,[['Bekle',[expected,'-']]])
            self.assertEqual(p.integer.used_default,defaulted);self.assertFalse(p.integer.native_bot_catch_verified)

    def test_wait_text_is_read_after_blank_add_and_caption(self):
        sink=Sink()
        def read():
            self.assertEqual(sink.rows,[['Bekle',[]]])
            self.assertEqual(sink.events,['add','caption']);return '9'
        p=append_source_route_command('wait',sink,read)
        self.assertTrue(p.complete);self.assertEqual(sink.rows,[['Bekle',['9','-']]])

    def test_later_setter_failure_keeps_completed_prefix(self):
        for phase,expected in [('caption',[['',[]]]),('sub1',[['Town',[]]]),('sub2',[['Town',['-']]])]:
            sink=Sink(phase);p=append_source_route_command('town',sink)
            self.assertFalse(p.complete);self.assertEqual(p.phase,phase);self.assertEqual(sink.rows,expected)

    def test_wait_reader_failure_keeps_added_caption_without_subitems(self):
        sink=Sink()
        def read():raise OSError('own text unavailable')
        p=append_source_route_command('wait',sink,read)
        self.assertFalse(p.complete);self.assertEqual(p.phase,'wait_text');self.assertEqual(sink.rows,[['Bekle',[]]])

    def test_unknown_command_does_not_mutate(self):
        sink=Sink()
        with self.assertRaises(ValueError):append_source_route_command('unknown',sink)
        self.assertEqual(sink.rows,[])


if __name__=='__main__':unittest.main()
