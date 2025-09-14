#!/usr/bin/env python3
"""
StatesFlowWishes · Z3r0CL0cK · sH1FTSyNc
Main application demonstrating the integrated system
"""

import time
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src import create_integrated_system, StateType


def demo_states_flow_wishes():
    """Demonstrate StatesFlowWishes functionality"""
    print("=== StatesFlowWishes Demo ===")
    
    states_flow, zero_clock, shift_sync, temporal_manager = create_integrated_system()
    
    # Create states for a workflow
    states_flow.create_state("init", StateType.INITIAL, transitions=["processing"])
    states_flow.create_state("processing", StateType.ACTIVE, transitions=["completed", "error"])
    states_flow.create_state("completed", StateType.COMPLETED, transitions=[])
    states_flow.create_state("error", StateType.ERROR, transitions=["processing"])
    
    # Add wishes (callbacks)
    states_flow.add_wish("init_to_processing", lambda: print("📋 Starting processing..."))
    states_flow.add_wish("processing_to_completed", lambda: print("✅ Processing completed!"))
    states_flow.add_wish("processing_to_error", lambda: print("❌ Error occurred!"))
    
    # Demonstrate state transitions
    print("Initial state:", states_flow.get_current_state())
    
    states_flow.transition_to("init")
    print(f"Current state: {states_flow.get_current_state().name}")
    
    states_flow.transition_to("processing")
    print(f"Current state: {states_flow.get_current_state().name}")
    
    states_flow.transition_to("completed")
    print(f"Current state: {states_flow.get_current_state().name}")
    
    print("Flow summary:", states_flow.get_flow_summary())
    print()


def demo_zero_clock():
    """Demonstrate Z3r0CL0cK functionality"""
    print("=== Z3r0CL0cK Demo ===")
    
    states_flow, zero_clock, shift_sync, temporal_manager = create_integrated_system()
    
    # Start the clock
    zero_clock.start()
    print(f"Clock started. State: {zero_clock.state.value}")
    
    # Schedule some events
    zero_clock.schedule_event("event1", 1.0, lambda: print("⏰ Event 1 triggered!"))
    zero_clock.schedule_event("event2", 2.0, lambda: print("⏰ Event 2 triggered!"))
    zero_clock.schedule_event("recurring", 0.5, lambda: print("🔄 Recurring event!"), 
                            recurring=True, interval=0.5)
    
    # Let it run for a bit
    print("Waiting for events...")
    time.sleep(3.5)
    
    # Pause and show info
    zero_clock.pause()
    print(f"Clock paused. Elapsed time: {zero_clock.get_elapsed_time():.2f}s")
    print("Clock info:", zero_clock.get_clock_info())
    
    zero_clock.stop()
    print()


def demo_shift_sync():
    """Demonstrate sH1FTSyNc functionality"""
    print("=== sH1FTSyNc Demo ===")
    
    states_flow, zero_clock, shift_sync, temporal_manager = create_integrated_system()
    
    # Set up states for synchronization demo
    states_flow.create_state("sync_ready", StateType.ACTIVE, transitions=["sync_complete"])
    states_flow.create_state("sync_complete", StateType.COMPLETED, transitions=[])
    
    # Create sync points
    sync_point = shift_sync.create_sync_point("demo_sync", ["states_flow", "zero_clock"])
    
    # Add sync callback
    def sync_callback(sync_point_name, success):
        status = "✅ Success" if success else "❌ Failed"
        print(f"🔄 Sync '{sync_point_name}' completed: {status}")
    
    shift_sync.add_sync_callback(sync_callback)
    
    # Start components
    zero_clock.start()
    states_flow.transition_to("sync_ready")
    
    # Trigger synchronization
    print("Triggering synchronization...")
    result = shift_sync.trigger_sync("demo_sync")
    print(f"Sync result: {result}")
    
    # Show sync status
    print("Sync status:", shift_sync.get_sync_status())
    
    zero_clock.stop()
    print()


def demo_temporal_shift():
    """Demonstrate TemporalShiftManager functionality"""
    print("=== Temporal Shift Demo ===")
    
    states_flow, zero_clock, shift_sync, temporal_manager = create_integrated_system()
    
    # Start the clock
    zero_clock.start()
    
    # Create temporal shift
    temporal_manager.create_temporal_shift("demo_shift", 2.0, ["states_flow", "zero_clock"])
    
    # Add sync callbacks to see shift events
    def shift_callback(sync_point_name, success):
        if "demo_shift" in sync_point_name:
            phase = "START" if "_start" in sync_point_name else "END"
            print(f"🚀 Temporal shift {phase}: {sync_point_name}")
    
    shift_sync.add_sync_callback(shift_callback)
    
    # Start the temporal shift
    print("Starting temporal shift...")
    temporal_manager.start_temporal_shift("demo_shift")
    
    # Wait for the shift to complete
    time.sleep(2.5)
    
    print("Active shifts:", temporal_manager.get_active_shifts())
    print("Shift info:", temporal_manager.get_shift_info("demo_shift"))
    
    zero_clock.stop()
    print()


def main():
    """Main application entry point"""
    print("🎯 StatesFlowWishes · Z3r0CL0cK · sH1FTSyNc")
    print("=" * 50)
    print()
    
    try:
        demo_states_flow_wishes()
        demo_zero_clock()
        demo_shift_sync()
        demo_temporal_shift()
        
        print("🎉 All demos completed successfully!")
        
    except KeyboardInterrupt:
        print("\n👋 Demo interrupted by user")
    except Exception as e:
        print(f"❌ Error during demo: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()