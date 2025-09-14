"""
sH1FTSyNc - Shift Synchronization system
Handles synchronization between different states, clocks, and processes
"""

import time
import threading
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
from enum import Enum
from .states_flow_wishes import StatesFlowWishes, StateType
from .zero_clock import Z3r0CL0cK


class SyncState(Enum):
    """Synchronization state enumeration"""
    IDLE = "idle"
    SYNCING = "syncing"
    SYNCHRONIZED = "synchronized"
    DESYNC = "desync"
    ERROR = "error"


@dataclass
class SyncPoint:
    """Represents a synchronization point"""
    name: str
    timestamp: float
    participants: List[str]
    synchronized: bool = False
    sync_tolerance: float = 0.1  # 100ms default tolerance


class ShiftSync:
    """Main synchronization manager for shifts and state transitions"""
    
    def __init__(self):
        self.state: SyncState = SyncState.IDLE
        self.sync_points: Dict[str, SyncPoint] = {}
        self.participants: Dict[str, Any] = {}
        self.sync_callbacks: List[Callable] = []
        self.master_clock: Optional[Z3r0CL0cK] = None
        self._lock = threading.Lock()
        self.sync_history: List[Dict[str, Any]] = []
        
    def register_participant(self, name: str, participant: Any) -> None:
        """Register a participant for synchronization"""
        with self._lock:
            self.participants[name] = participant
    
    def unregister_participant(self, name: str) -> bool:
        """Unregister a participant"""
        with self._lock:
            if name in self.participants:
                del self.participants[name]
                return True
        return False
    
    def set_master_clock(self, clock: Z3r0CL0cK) -> None:
        """Set the master clock for synchronization"""
        self.master_clock = clock
    
    def create_sync_point(self, name: str, participants: List[str], 
                         tolerance: float = 0.1) -> SyncPoint:
        """Create a new synchronization point"""
        sync_point = SyncPoint(
            name=name,
            timestamp=time.time(),
            participants=participants,
            sync_tolerance=tolerance
        )
        
        with self._lock:
            self.sync_points[name] = sync_point
        
        return sync_point
    
    def trigger_sync(self, sync_point_name: str) -> bool:
        """Trigger synchronization at a specific point"""
        if sync_point_name not in self.sync_points:
            return False
            
        sync_point = self.sync_points[sync_point_name]
        
        with self._lock:
            self.state = SyncState.SYNCING
            
        # Check if all participants are ready
        ready_participants = []
        for participant_name in sync_point.participants:
            if participant_name in self.participants:
                participant = self.participants[participant_name]
                
                # Check readiness based on participant type
                if isinstance(participant, StatesFlowWishes):
                    current_state = participant.get_current_state()
                    if current_state and current_state.state_type != StateType.ERROR:
                        ready_participants.append(participant_name)
                elif isinstance(participant, Z3r0CL0cK):
                    if participant.state.name in ['RUNNING', 'PAUSED']:
                        ready_participants.append(participant_name)
                else:
                    # Generic participant - assume ready
                    ready_participants.append(participant_name)
        
        # Perform synchronization if enough participants are ready
        sync_success = len(ready_participants) >= len(sync_point.participants) * 0.5
        
        if sync_success:
            self._perform_sync(sync_point, ready_participants)
            sync_point.synchronized = True
            self.state = SyncState.SYNCHRONIZED
        else:
            self.state = SyncState.DESYNC
            
        # Record sync attempt
        self.sync_history.append({
            'sync_point': sync_point_name,
            'timestamp': time.time(),
            'success': sync_success,
            'ready_participants': ready_participants,
            'total_participants': sync_point.participants
        })
        
        # Execute callbacks
        for callback in self.sync_callbacks:
            try:
                callback(sync_point_name, sync_success)
            except Exception as e:
                print(f"Error in sync callback: {e}")
        
        return sync_success
    
    def _perform_sync(self, sync_point: SyncPoint, ready_participants: List[str]) -> None:
        """Internal method to perform the actual synchronization"""
        master_time = None
        
        if self.master_clock:
            master_time = self.master_clock.get_elapsed_time()
        
        for participant_name in ready_participants:
            participant = self.participants[participant_name]
            
            try:
                if isinstance(participant, StatesFlowWishes):
                    # Sync state flow - could trigger a specific sync state
                    sync_state_name = f"sync_{sync_point.name}"
                    if sync_state_name in participant.states:
                        participant.transition_to(sync_state_name)
                
                elif isinstance(participant, Z3r0CL0cK):
                    # Sync clock - could adjust timing or trigger events
                    if master_time is not None:
                        # Schedule a sync event
                        participant.schedule_event(
                            f"sync_{sync_point.name}",
                            0.0,  # Immediate
                            lambda: None  # Sync marker
                        )
                
                # Generic sync operation for other participants
                if hasattr(participant, 'sync'):
                    participant.sync(sync_point.name)
                    
            except Exception as e:
                print(f"Error syncing participant '{participant_name}': {e}")
    
    def add_sync_callback(self, callback: Callable[[str, bool], None]) -> None:
        """Add a callback to be executed on sync events"""
        self.sync_callbacks.append(callback)
    
    def remove_sync_callback(self, callback: Callable[[str, bool], None]) -> None:
        """Remove a sync callback"""
        if callback in self.sync_callbacks:
            self.sync_callbacks.remove(callback)
    
    def get_sync_status(self) -> Dict[str, Any]:
        """Get comprehensive synchronization status"""
        return {
            'state': self.state.value,
            'participants': list(self.participants.keys()),
            'sync_points': {name: {
                'synchronized': sp.synchronized,
                'participants': sp.participants,
                'tolerance': sp.sync_tolerance,
                'timestamp': sp.timestamp
            } for name, sp in self.sync_points.items()},
            'sync_history': self.sync_history[-10:],  # Last 10 sync attempts
            'master_clock_info': self.master_clock.get_clock_info() if self.master_clock else None
        }
    
    def shift_sync_all(self) -> Dict[str, bool]:
        """Perform a shift synchronization across all registered sync points"""
        results = {}
        
        with self._lock:
            self.state = SyncState.SYNCING
            
        for sync_point_name in self.sync_points.keys():
            results[sync_point_name] = self.trigger_sync(sync_point_name)
        
        # Determine overall sync state
        if all(results.values()):
            self.state = SyncState.SYNCHRONIZED
        elif any(results.values()):
            self.state = SyncState.DESYNC
        else:
            self.state = SyncState.ERROR
            
        return results


class TemporalShiftManager:
    """Manages temporal shifts and synchronization across time-based operations"""
    
    def __init__(self, shift_sync: ShiftSync, zero_clock: Z3r0CL0cK):
        self.shift_sync = shift_sync
        self.zero_clock = zero_clock
        self.shifts: Dict[str, Dict[str, Any]] = {}
        
    def create_temporal_shift(self, name: str, duration: float, 
                            participants: List[str]) -> None:
        """Create a temporal shift operation"""
        shift_data = {
            'duration': duration,
            'participants': participants,
            'start_time': None,
            'end_time': None,
            'active': False
        }
        
        self.shifts[name] = shift_data
        
        # Create corresponding sync points
        self.shift_sync.create_sync_point(f"{name}_start", participants)
        self.shift_sync.create_sync_point(f"{name}_end", participants)
    
    def start_temporal_shift(self, name: str) -> bool:
        """Start a temporal shift"""
        if name not in self.shifts:
            return False
            
        shift = self.shifts[name]
        current_time = self.zero_clock.get_elapsed_time()
        
        shift['start_time'] = current_time
        shift['end_time'] = current_time + shift['duration']
        shift['active'] = True
        
        # Trigger start sync
        self.shift_sync.trigger_sync(f"{name}_start")
        
        # Schedule end sync
        self.zero_clock.schedule_event(
            f"shift_end_{name}",
            shift['duration'],
            lambda: self._end_temporal_shift(name)
        )
        
        return True
    
    def _end_temporal_shift(self, name: str) -> None:
        """Internal method to end a temporal shift"""
        if name in self.shifts:
            self.shifts[name]['active'] = False
            self.shift_sync.trigger_sync(f"{name}_end")
    
    def get_active_shifts(self) -> List[str]:
        """Get list of currently active shifts"""
        return [name for name, shift in self.shifts.items() if shift['active']]
    
    def get_shift_info(self, name: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific shift"""
        return self.shifts.get(name)