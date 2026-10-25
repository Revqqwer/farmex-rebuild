import unittest
from dataclasses import replace
from action_queue import CallbackQueueGate
from attack_lock import (AttackLockState,LockCallbackObservation,plan_attack_unlock,
                         plan_callback_attack_unlock,apply_lock_write_plans)

class AttackLockTests(unittest.TestCase):
    def setUp(self):
        self.g=CallbackQueueGate(1,1,0,0,1)
        self.o=LockCallbackObservation(0,0,0,0,{h:True for h in
            ('00458c70','004c79a0','004ff918','00470a94','0045a4dc','00458f98')})
    def test_zero_lock_needs_no_clock_and_keeps_existing_duration(self):
        p=plan_attack_unlock(AttackLockState(0,1000,55))
        self.assertTrue(p.complete);self.assertEqual(p.calls,());self.assertEqual(p.state.started_ms,55)
    def test_expiry_boundary_preserves_duration_and_start(self):
        st=AttackLockState(255,600,1000)
        self.assertEqual(plan_attack_unlock(st,1599).state,st)
        p=plan_attack_unlock(st,1600)
        self.assertEqual(p.state,AttackLockState(0,600,1000));self.assertEqual(p.writes,(('00561f7e',0),))
    def test_expiry_dword_wrap_and_large_unsigned_interval(self):
        st=AttackLockState(1,5,0xfffffffd)
        self.assertEqual(plan_attack_unlock(st,1).state.byte,1)
        self.assertEqual(plan_attack_unlock(st,2).state.byte,0)
        self.assertEqual(plan_attack_unlock(AttackLockState(1,0xffffffff,0),0xfffffffe).state.byte,1)
        self.assertEqual(plan_attack_unlock(AttackLockState(1,0xffffffff,0),0xffffffff).state.byte,0)
    def test_outer_gate_short_circuit_never_clears_expired_lock(self):
        st=AttackLockState(1,0,0)
        for gate in (replace(self.g,ready_46edb0=0),replace(self.g,connection_462738=2),
                     replace(self.g,byte_562208=1),replace(self.g,byte_56221d=1),
                     replace(self.g,initial_reader_f3c=0,byte_561f55=1,helper_46f33c=1)):
            p=plan_callback_attack_unlock(st,gate,self.o,1000)
            self.assertEqual(p.status,'callback_skipped_lock');self.assertEqual(p.state,st)
            self.assertFalse(p.timer_reached)
    def test_post_queue_worker_exits_before_unlock_but_vip_has_priority(self):
        st=AttackLockState(1)
        p=plan_callback_attack_unlock(st,self.g,replace(self.o,byte_568dbc=1),1000)
        self.assertEqual(p.status,'worker_skipped_lock');self.assertEqual(p.state,st)
        p=plan_callback_attack_unlock(st,self.g,replace(self.o,byte_5690b8=1,byte_568dbc=1),1000)
        self.assertEqual(p.status,'lock_cleared');self.assertIn('004ff918',p.calls)
        self.assertNotIn('00470a94',p.calls)
    def test_inn_and_optional_work_sender_must_complete(self):
        o=replace(self.o,byte_5690e0=1,byte_561f60=1)
        p=plan_callback_attack_unlock(AttackLockState(1),self.g,o,1)
        self.assertEqual(p.calls,('00458c70','004c79a0','00470a94','0045a4dc','00458f98','005074da'))
        p=plan_callback_attack_unlock(AttackLockState(1),self.g,replace(o,completed={}),1)
        self.assertFalse(p.complete);self.assertFalse(p.timer_reached)
        self.assertEqual(p.state.byte,1)
    def test_missing_observations_do_not_become_unlocked(self):
        p=plan_callback_attack_unlock(AttackLockState(1),self.g,self.o)
        self.assertEqual((p.status,p.timer_reached,p.state.byte),('needs_observation',True,1))
        self.assertFalse(p.complete)
        p=plan_callback_attack_unlock(AttackLockState(1),CallbackQueueGate(),self.o,1)
        self.assertFalse(p.timer_reached);self.assertEqual(p.state.byte,1)
    def test_selector_lock_write_does_not_refresh_old_timer(self):
        st=AttackLockState(0,600,1000)
        st=apply_lock_write_plans(st,(('00561f7e',1),('0056fee0',1)))
        self.assertEqual(st,AttackLockState(1,600,1000))
        self.assertEqual(plan_attack_unlock(st,2000).state.byte,0)
    def test_special_lock_triple_updates_are_reduced_in_order(self):
        st=apply_lock_write_plans(AttackLockState(),(('00561f80',1600),('00561f84',2000),('00561f7e',1)))
        self.assertEqual(st,AttackLockState(1,1600,2000))
        self.assertEqual(plan_attack_unlock(st,3599).state.byte,1)
        self.assertEqual(plan_attack_unlock(st,3600).state.byte,0)
    def test_invalid_observation_types(self):
        for make in (lambda:AttackLockState(True),lambda:AttackLockState(1,-1),
                     lambda:LockCallbackObservation(byte_568dbc=256),lambda:plan_attack_unlock(AttackLockState(1),True)):
            with self.assertRaises(ValueError):make()
