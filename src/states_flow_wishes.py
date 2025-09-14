"""
StatesFlowWishes - Core state flow management system
Handles state transitions, workflows, and flow control
"""

import time
from typing import Dict, List, Any, Callable, Optional
from enum import Enum
from dataclasses import dataclass


class StateType(Enum):
    """Enumeration of possible state types"""
    INITIAL = "initial"
    ACTIVE = "active"
    WAITING = "waiting"
    COMPLETED = "completed"
    ERROR = "error"


@dataclass
class State:
    """Represents a single state in the flow"""
    name: str
    state_type: StateType
    data: Dict[str, Any]
    timestamp: float
    transitions: List[str]
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = time.time()


class StatesFlowWishes:
    """Main class for managing state flows and wishes"""
    
    def __init__(self):
        self.states: Dict[str, State] = {}
        self.current_state: Optional[str] = None
        self.flow_history: List[str] = []
        self.wishes: Dict[str, Callable] = {}
        self.flow_start_time: Optional[float] = None
        
    def create_state(self, name: str, state_type: StateType, 
                    data: Dict[str, Any] = None, 
                    transitions: List[str] = None) -> State:
        """Create a new state in the flow"""
        if data is None:
            data = {}
        if transitions is None:
            transitions = []
            
        state = State(
            name=name,
            state_type=state_type,
            data=data,
            timestamp=time.time(),
            transitions=transitions
        )
        self.states[name] = state
        return state
    
    def add_wish(self, name: str, wish_function: Callable) -> None:
        """Add a wish (callback function) to be executed at state transitions"""
        self.wishes[name] = wish_function
    
    def transition_to(self, target_state: str) -> bool:
        """Transition from current state to target state"""
        if target_state not in self.states:
            raise ValueError(f"Target state '{target_state}' does not exist")
            
        current = self.states.get(self.current_state) if self.current_state else None
        
        # Check if transition is allowed
        if current and target_state not in current.transitions:
            return False
            
        # Execute any wishes for this transition
        wish_key = f"{self.current_state}_to_{target_state}"
        if wish_key in self.wishes:
            self.wishes[wish_key]()
            
        # Perform transition
        if self.current_state:
            self.flow_history.append(self.current_state)
        
        self.current_state = target_state
        self.states[target_state].timestamp = time.time()
        
        if not self.flow_start_time:
            self.flow_start_time = time.time()
            
        return True
    
    def get_current_state(self) -> Optional[State]:
        """Get the current active state"""
        if self.current_state:
            return self.states[self.current_state]
        return None
    
    def get_flow_duration(self) -> float:
        """Get the total duration of the flow"""
        if not self.flow_start_time:
            return 0.0
        return time.time() - self.flow_start_time
    
    def get_flow_summary(self) -> Dict[str, Any]:
        """Get a summary of the entire flow"""
        return {
            'current_state': self.current_state,
            'flow_history': self.flow_history,
            'total_states': len(self.states),
            'flow_duration': self.get_flow_duration(),
            'start_time': self.flow_start_time,
            'states': {name: {
                'type': state.state_type.value,
                'timestamp': state.timestamp,
                'data': state.data
            } for name, state in self.states.items()}
        }