#!/usr/bin/env python3
"""
Test suite for StatesFlowWishes · Z3r0CL0cK · sH1FTSyNc system
"""

import unittest
import time
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src import create_integrated_system, StateType
from src.states_flow_wishes import StatesFlowWishes, State
from src.zero_clock import Z3r0CL0cK, ClockState
from src.shift_sync import ShiftSync, SyncState


class TestStatesFlowWishes(unittest.TestCase):
    """Test cases for StatesFlowWishes"""
    
    def setUp(self):
        self.states_flow = StatesFlowWishes()
    
    def test_create_state(self):
        """Test state creation"""
        state = self.states_flow.create_state("test", StateType.ACTIVE)
        self.assertEqual(state.name, "test")
        self.assertEqual(state.state_type, StateType.ACTIVE)
        self.assertIn("test", self.states_flow.states)
    
    def test_state_transitions(self):
        """Test state transitions"""
        self.states_flow.create_state("start", StateType.INITIAL, transitions=["end"])
        self.states_flow.create_state("end", StateType.COMPLETED)
        
        # Test valid transition
        self.assertTrue(self.states_flow.transition_to("start"))
        self.assertEqual(self.states_flow.current_state, "start")
        
        self.assertTrue(self.states_flow.transition_to("end"))
        self.assertEqual(self.states_flow.current_state, "end")
    
    def test_invalid_transition(self):
        """Test invalid state transition"""
        self.states_flow.create_state("start", StateType.INITIAL, transitions=[])
        self.states_flow.create_state("end", StateType.COMPLETED)
        
        self.states_flow.transition_to("start")
        # Should fail because end is not in start's transitions
        self.assertFalse(self.states_flow.transition_to("end"))
    
    def test_wishes(self):
        """Test wish callbacks"""
        wish_executed = []
        
        def test_wish():
            wish_executed.append(True)
        
        self.states_flow.add_wish("start_to_end", test_wish)
        self.states_flow.create_state("start", StateType.INITIAL, transitions=["end"])
        self.states_flow.create_state("end", StateType.COMPLETED)
        
        self.states_flow.transition_to("start")
        self.states_flow.transition_to("end")
        
        self.assertTrue(wish_executed)


class TestZ3r0CL0cK(unittest.TestCase):
    """Test cases for Z3r0CL0cK"""
    
    def setUp(self):
        self.clock = Z3r0CL0cK()
    
    def tearDown(self):
        self.clock.stop()
    
    def test_clock_states(self):
        """Test clock state management"""
        self.assertEqual(self.clock.state, ClockState.STOPPED)
        
        self.clock.start()
        self.assertEqual(self.clock.state, ClockState.RUNNING)
        
        self.clock.pause()
        self.assertEqual(self.clock.state, ClockState.PAUSED)
        
        self.clock.stop()
        self.assertEqual(self.clock.state, ClockState.STOPPED)
    
    def test_elapsed_time(self):
        """Test elapsed time calculation"""
        self.clock.start()
        time.sleep(0.1)
        elapsed = self.clock.get_elapsed_time()
        self.assertGreater(elapsed, 0.05)
        self.assertLess(elapsed, 0.2)
    
    def test_event_scheduling(self):
        """Test event scheduling"""
        event_executed = []
        
        def test_event():
            event_executed.append(True)
        
        self.clock.start()
        self.clock.schedule_event("test", 0.1, test_event)
        
        time.sleep(0.2)
        self.assertTrue(event_executed)
    
    def test_recurring_events(self):
        """Test recurring events"""
        event_count = []
        
        def recurring_event():
            event_count.append(1)
        
        self.clock.start()
        self.clock.schedule_event("recurring", 0.05, recurring_event, recurring=True, interval=0.05)
        
        time.sleep(0.25)
        self.assertGreater(len(event_count), 2)


class TestShiftSync(unittest.TestCase):
    """Test cases for ShiftSync"""
    
    def setUp(self):
        self.shift_sync = ShiftSync()
        self.states_flow = StatesFlowWishes()
        self.zero_clock = Z3r0CL0cK()
        
        self.shift_sync.register_participant("states", self.states_flow)
        self.shift_sync.register_participant("clock", self.zero_clock)
    
    def tearDown(self):
        self.zero_clock.stop()
    
    def test_participant_registration(self):
        """Test participant registration"""
        self.assertIn("states", self.shift_sync.participants)
        self.assertIn("clock", self.shift_sync.participants)
        
        self.assertTrue(self.shift_sync.unregister_participant("states"))
        self.assertNotIn("states", self.shift_sync.participants)
    
    def test_sync_point_creation(self):
        """Test sync point creation"""
        sync_point = self.shift_sync.create_sync_point("test_sync", ["states", "clock"])
        self.assertEqual(sync_point.name, "test_sync")
        self.assertIn("test_sync", self.shift_sync.sync_points)
    
    def test_synchronization(self):
        """Test synchronization trigger"""
        sync_point = self.shift_sync.create_sync_point("test_sync", ["states", "clock"])
        
        # Set up participants in ready state
        self.states_flow.create_state("ready", StateType.ACTIVE)
        self.states_flow.transition_to("ready")
        self.zero_clock.start()
        
        result = self.shift_sync.trigger_sync("test_sync")
        self.assertTrue(result)
        self.assertEqual(self.shift_sync.state, SyncState.SYNCHRONIZED)


class TestIntegratedSystem(unittest.TestCase):
    """Test cases for the integrated system"""
    
    def test_system_creation(self):
        """Test integrated system creation"""
        states_flow, zero_clock, shift_sync, temporal_manager = create_integrated_system()
        
        self.assertIsInstance(states_flow, StatesFlowWishes)
        self.assertIsInstance(zero_clock, Z3r0CL0cK)
        self.assertIsInstance(shift_sync, ShiftSync)
        
        # Test integration
        self.assertEqual(shift_sync.master_clock, zero_clock)
        self.assertIn("states_flow", shift_sync.participants)
        self.assertIn("zero_clock", shift_sync.participants)
    
    def test_temporal_shift(self):
        """Test temporal shift functionality"""
        states_flow, zero_clock, shift_sync, temporal_manager = create_integrated_system()
        
        zero_clock.start()
        temporal_manager.create_temporal_shift("test_shift", 0.1, ["states_flow"])
        
        self.assertTrue(temporal_manager.start_temporal_shift("test_shift"))
        self.assertIn("test_shift", temporal_manager.get_active_shifts())
        
        time.sleep(0.2)
        self.assertNotIn("test_shift", temporal_manager.get_active_shifts())
        
        zero_clock.stop()


if __name__ == "__main__":
    print("🧪 Running StatesFlowWishes · Z3r0CL0cK · sH1FTSyNc Test Suite")
    print("=" * 60)
    
    unittest.main(verbosity=2)