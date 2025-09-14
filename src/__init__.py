"""
StatesFlowWishes · Z3r0CL0cK · sH1FTSyNc
Main integration module for the complete system
"""

from .states_flow_wishes import StatesFlowWishes, StateType, State
from .zero_clock import Z3r0CL0cK, ClockState, TimeEvent
from .shift_sync import ShiftSync, TemporalShiftManager, SyncState, SyncPoint

__all__ = [
    'StatesFlowWishes', 'StateType', 'State',
    'Z3r0CL0cK', 'ClockState', 'TimeEvent', 
    'ShiftSync', 'TemporalShiftManager', 'SyncState', 'SyncPoint',
    'create_integrated_system'
]

__version__ = '1.0.0'
__author__ = 'Z3r0CL0cK'
__description__ = 'StatesFlowWishes · Z3r0CL0cK · sH1FTSyNc - Integrated state flow, timing, and synchronization system'


def create_integrated_system():
    """
    Create a fully integrated system with StatesFlowWishes, Z3r0CL0cK, and sH1FTSyNc
    
    Returns:
        tuple: (states_flow, zero_clock, shift_sync, temporal_manager)
    """
    # Initialize core components
    states_flow = StatesFlowWishes()
    zero_clock = Z3r0CL0cK()
    shift_sync = ShiftSync()
    
    # Set up integration
    shift_sync.set_master_clock(zero_clock)
    shift_sync.register_participant('states_flow', states_flow)
    shift_sync.register_participant('zero_clock', zero_clock)
    
    # Create temporal shift manager
    temporal_manager = TemporalShiftManager(shift_sync, zero_clock)
    
    return states_flow, zero_clock, shift_sync, temporal_manager