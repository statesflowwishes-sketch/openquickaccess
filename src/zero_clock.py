"""
Z3r0CL0cK - Zero Clock timing and synchronization utilities
Handles precise timing, clock management, and time-based operations
"""

import time
import threading
from typing import Dict, List, Callable, Optional
from dataclasses import dataclass
from enum import Enum


class ClockState(Enum):
    """Clock state enumeration"""
    STOPPED = "stopped"
    RUNNING = "running"
    PAUSED = "paused"
    RESET = "reset"


@dataclass
class TimeEvent:
    """Represents a timed event"""
    name: str
    target_time: float
    callback: Callable
    executed: bool = False
    recurring: bool = False
    interval: float = 0.0


class Z3r0CL0cK:
    """Zero Clock - High precision timing and event scheduling"""
    
    def __init__(self):
        self.start_time: Optional[float] = None
        self.pause_time: Optional[float] = None
        self.state: ClockState = ClockState.STOPPED
        self.events: Dict[str, TimeEvent] = {}
        self.elapsed_offset: float = 0.0
        self.tick_callbacks: List[Callable[[float], None]] = []
        self._running: bool = False
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
        
    def start(self) -> None:
        """Start the zero clock"""
        with self._lock:
            if self.state == ClockState.RUNNING:
                return
                
            current_time = time.time()
            
            if self.state == ClockState.PAUSED and self.pause_time:
                # Resume from pause
                self.elapsed_offset += current_time - self.pause_time
            else:
                # Fresh start
                self.start_time = current_time
                self.elapsed_offset = 0.0
                
            self.state = ClockState.RUNNING
            self.pause_time = None
            self._running = True
            
            # Start the clock thread
            if not self._thread or not self._thread.is_alive():
                self._thread = threading.Thread(target=self._clock_loop, daemon=True)
                self._thread.start()
    
    def pause(self) -> None:
        """Pause the zero clock"""
        with self._lock:
            if self.state != ClockState.RUNNING:
                return
                
            self.pause_time = time.time()
            self.state = ClockState.PAUSED
            self._running = False
    
    def stop(self) -> None:
        """Stop the zero clock"""
        with self._lock:
            self.state = ClockState.STOPPED
            self.start_time = None
            self.pause_time = None
            self.elapsed_offset = 0.0
            self._running = False
    
    def reset(self) -> None:
        """Reset the zero clock to initial state"""
        self.stop()
        with self._lock:
            self.state = ClockState.RESET
            self.events.clear()
    
    def get_elapsed_time(self) -> float:
        """Get elapsed time since clock started"""
        if not self.start_time:
            return 0.0
            
        current_time = time.time()
        
        if self.state == ClockState.RUNNING:
            return current_time - self.start_time - self.elapsed_offset
        elif self.state == ClockState.PAUSED and self.pause_time:
            return self.pause_time - self.start_time - self.elapsed_offset
        else:
            return 0.0
    
    def schedule_event(self, name: str, delay: float, callback: Callable, 
                      recurring: bool = False, interval: float = 0.0) -> None:
        """Schedule a timed event"""
        target_time = self.get_elapsed_time() + delay
        
        event = TimeEvent(
            name=name,
            target_time=target_time,
            callback=callback,
            recurring=recurring,
            interval=interval if recurring else 0.0
        )
        
        with self._lock:
            self.events[name] = event
    
    def cancel_event(self, name: str) -> bool:
        """Cancel a scheduled event"""
        with self._lock:
            if name in self.events:
                del self.events[name]
                return True
        return False
    
    def add_tick_callback(self, callback: Callable[[float], None]) -> None:
        """Add a callback that gets called on each clock tick"""
        self.tick_callbacks.append(callback)
    
    def remove_tick_callback(self, callback: Callable[[float], None]) -> None:
        """Remove a tick callback"""
        if callback in self.tick_callbacks:
            self.tick_callbacks.remove(callback)
    
    def _clock_loop(self) -> None:
        """Internal clock loop that runs in a separate thread"""
        while self._running:
            current_elapsed = self.get_elapsed_time()
            
            # Execute tick callbacks
            for callback in self.tick_callbacks:
                try:
                    callback(current_elapsed)
                except Exception as e:
                    print(f"Error in tick callback: {e}")
            
            # Check and execute scheduled events
            events_to_execute = []
            events_to_reschedule = []
            
            with self._lock:
                for event_name, event in list(self.events.items()):
                    if not event.executed and current_elapsed >= event.target_time:
                        events_to_execute.append(event)
                        
                        if event.recurring:
                            events_to_reschedule.append((event_name, event))
                        else:
                            event.executed = True
            
            # Execute events outside the lock
            for event in events_to_execute:
                try:
                    event.callback()
                except Exception as e:
                    print(f"Error executing event '{event.name}': {e}")
            
            # Reschedule recurring events
            with self._lock:
                for event_name, event in events_to_reschedule:
                    event.target_time = current_elapsed + event.interval
                    event.executed = False
            
            # Small sleep to prevent excessive CPU usage
            time.sleep(0.001)  # 1ms precision
    
    def get_clock_info(self) -> Dict[str, any]:
        """Get comprehensive clock information"""
        return {
            'state': self.state.value,
            'elapsed_time': self.get_elapsed_time(),
            'start_time': self.start_time,
            'pause_time': self.pause_time,
            'scheduled_events': len(self.events),
            'tick_callbacks': len(self.tick_callbacks),
            'events': {name: {
                'target_time': event.target_time,
                'executed': event.executed,
                'recurring': event.recurring,
                'interval': event.interval
            } for name, event in self.events.items()}
        }