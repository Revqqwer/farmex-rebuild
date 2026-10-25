import unittest
from manual_coordinate import AXIS_FIELDS, ManualCoordinateObservation
from manual_coordinate_runtime import *


NORMALS = dict(entry_setup=True, movement=True,
               **{a+'_'+s:True for a in ('x','y') for s in ('construct','get_text','parse','cleanup')})


def capture(context, bits=None, normals=None):
    return ManualCoordinateCapture(context.invocation, context.generation,
        ManualCoordinateObservation(texts=context.texts,
            float_bits={a: {'10':0x41200000,'20':0x41a00000,'30':0x41f00000}[text]
                        for a,text in context.texts.items()} if bits is None else bits,
            normal_returns=NORMALS if normals is None else normals))


class ManualCoordinateRuntimeTests(unittest.TestCase):
    def setUp(self):
        self.values={AXIS_FIELDS[0][2]:'10',AXIS_FIELDS[1][2]:'20'}
        self.r=OwnedManualCoordinate(lambda:self.values)

    def finish(self, provider=capture):
        for _ in range(15):
            if not self.r.pending:break
            self.r.tick(provider)
        self.assertFalse(self.r.pending, self.r.error)

    def test_own_click_entry_does_not_fabricate_helper_returns(self):
        p=self.r.start()
        self.assertEqual(p.needed,('normal','entry_setup'))
        self.r.tick(lambda context:None)
        self.assertEqual(self.r.result,p)

    def test_reads_each_axis_only_at_its_getter_output(self):
        self.r.start();self.r.tick(capture)
        self.assertEqual(dict(self.r.frame.observation.texts),{'x':'10'})
        self.values[AXIS_FIELDS[0][2]]='30';self.values[AXIS_FIELDS[1][2]]='30'
        self.finish()
        self.assertEqual(self.r.result.movement,(0x41200000,0x41f00000))

    def test_float_capture_must_attest_acquired_text_and_tokens(self):
        self.r.start();self.r.tick(capture)
        before=self.r.frame.observation
        def wrong(context):
            return ManualCoordinateCapture(context.invocation,context.generation,
                ManualCoordinateObservation(texts={'x':'999'},float_bits={'x':0}))
        self.r.tick(wrong)
        self.assertIs(self.r.frame.observation,before)
        self.assertIn('differs',self.r.error)
        self.finish()

    def test_unbound_float_and_future_axis_are_rejected(self):
        self.r.start();self.r.tick(capture)
        self.r.tick(lambda c:ManualCoordinateCapture(c.invocation,c.generation,
            ManualCoordinateObservation(float_bits={'x':0})))
        self.assertIn('bind',self.r.error)
        self.r.tick(lambda c:ManualCoordinateCapture(c.invocation,c.generation,
            ManualCoordinateObservation(texts={'y':'20'},float_bits={'y':0})))
        self.assertIn('differs',self.r.error)

    def test_duplicate_pending_click_and_terminal_tick_are_idempotent(self):
        self.r.start();invocation=self.r.invocation;self.r.start()
        self.assertEqual(self.r.invocation,invocation)
        self.finish();p=self.r.result
        self.assertIs(self.r.tick(lambda c:self.fail('terminal provider call')),p)
        self.r.start();self.assertEqual(self.r.invocation,invocation+1)

    def test_profile_reset_during_callback_discards_returned_capture(self):
        self.r.start();old_generation=self.r.generation
        def reset(context):
            self.r.reset()
            return capture(context)
        self.r.tick(reset)
        self.assertGreater(self.r.generation,old_generation)
        self.assertIsNone(self.r.result);self.assertFalse(self.r.pending)
        self.r.start()
        self.r.tick(lambda c:ManualCoordinateCapture(c.invocation,old_generation,ManualCoordinateObservation()))
        self.assertIn('Stale',self.r.error)
        self.finish()

    def test_reentrant_tick_never_recurses_or_duplicates_provider(self):
        self.r.start();calls=[]
        def provider(context):
            calls.append(context)
            self.r.tick(lambda c:self.fail('recursive provider'))
            self.r.start()
            return capture(context)
        self.r.tick(provider)
        self.assertEqual(len(calls),1);self.assertEqual(self.r.invocation,1)
        self.finish()

    def test_provider_error_preserves_prefix_and_can_resume(self):
        self.r.start();self.r.tick(capture)
        before=self.r.frame.observation
        def failed(context):raise OSError('capture unavailable')
        self.r.tick(failed)
        self.assertIs(self.r.frame.observation,before)
        self.assertEqual(self.r.error,'capture unavailable')
        self.finish();self.assertIsNone(self.r.error)


if __name__=='__main__':unittest.main()
