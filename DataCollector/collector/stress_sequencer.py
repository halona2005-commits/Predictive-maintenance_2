"""
=========================================================
Predictive Maintenance - Automated Stress Sequencer
=========================================================
Runs CPU, Memory, Disk, and Combined stress back-to-back.
Each phase runs for exactly 30 minutes.
Total time: 2 Hours (Matches the data collector).
=========================================================
"""

import multiprocessing
import threading
import time
import os
import psutil
import sys

# ------------------- CPU STRESS -------------------
def cpu_stress_worker():
    while True:
        _ = 123456789 * 987654321 / 3.14159

def start_cpu_stress():
    print(f"🔥 CPU: Spawning {psutil.cpu_count(logical=True)} workers...")
    procs = []
    for _ in range(psutil.cpu_count(logical=True)):
        p = multiprocessing.Process(target=cpu_stress_worker)
        p.start()
        procs.append(p)
    return procs

def stop_cpu_stress(procs):
    for p in procs:
        p.terminate()
    print("   CPU workers terminated.")

# ------------------- MEMORY STRESS -------------------
_memory_holder = []
_memory_running = False

def start_memory_stress():
    global _memory_holder, _memory_running
    _memory_running = True
    total_ram = psutil.virtual_memory().total
    target_bytes = int(total_ram * 0.80)
    allocated = 0
    print(f"🧠 Memory: Targeting {target_bytes / (1024**3):.1f} GB ({int(0.80*100)}% of RAM)...")
    
    while _memory_running and allocated < target_bytes:
        chunk = bytearray(50 * 1024 * 1024)
        _memory_holder.append(chunk)
        allocated += len(chunk)
        time.sleep(0.05)
    print(f"   Stabilized at {allocated / (1024**3):.2f} GB")

def stop_memory_stress():
    global _memory_holder, _memory_running
    _memory_running = False
    _memory_holder.clear()
    print("   Memory released.")

# ------------------- DISK STRESS -------------------
_disk_running = False
_DISK_FILE = "stress_temp.bin"

def start_disk_stress():
    global _disk_running
    _disk_running = True
    chunk_size = 50 * 1024 * 1024  # 50 MB (SSD safe)
    print(f"💾 Disk: Writing/Deleting 50MB chunks rapidly...")
    while _disk_running:
        try:
            with open(_DISK_FILE, "wb") as f:
                f.write(os.urandom(chunk_size))
            os.remove(_DISK_FILE)
        except Exception:  # <-- FIXED: Catch specific exception
            pass

def stop_disk_stress():
    global _disk_running
    _disk_running = False
    time.sleep(0.5)
    if os.path.exists(_DISK_FILE):
        os.remove(_DISK_FILE)
    print("   Disk stress stopped and temp file cleaned.")

# ------------------- PHASE EXECUTOR -------------------
def run_phase(phase_name, duration_minutes, start_func, stop_func, start_args=None):
    print("\n" + "="*60)
    print(f"  ⏳ PHASE: {phase_name} (Duration: {duration_minutes} minutes)")
    print("="*60)
    
    if start_args:
        result = start_func(*start_args)
    else:
        result = start_func()
    
    for remaining in range(duration_minutes, 0, -1):
        if remaining % 5 == 0 or remaining <= 3:
            print(f"   [{phase_name}] {remaining} minute{'s' if remaining > 1 else ''} remaining...")
        time.sleep(60)
    
    # FIXED: Pass the result to the stop function if it exists
    if result is not None:
        stop_func(result)
    else:
        stop_func()
    
    print(f"   Cooling down for 5 seconds...")
    time.sleep(5)
# ------------------- MAIN SEQUENCER -------------------
def main():
    print("\n" + "="*60)
    print("     AUTOMATED STRESS SEQUENCER v2.1")
    print("     (4 Phases x 30 mins = 2 Hours Total)")
    print("="*60)
    print("""
    This will run the following phases automatically:

    1. CPU Stress      : 30 mins
    2. Memory Stress   : 30 mins
    3. Disk Stress     : 30 mins
    4. Combined Stress : 30 mins

    Total time: 2 Hours (Matches the data collector exactly).
    
    ⚠️  IMPORTANT: 
    Run your Data Collector (run.py) in a SEPARATE terminal NOW 
    and select 'Controlled High Load' before pressing ENTER here.
    """)
    
    input("Press ENTER to start the stress sequence...")

    try:
        # PHASE 1: CPU
        run_phase("CPU", 30, start_cpu_stress, stop_cpu_stress)
        print("   ✅ CPU Phase Completed. Proceeding to Memory...\n")
        
        # PHASE 2: MEMORY (Daemon thread)
        print("\n" + "="*60)
        print("  ⏳ PHASE: MEMORY (Duration: 30 minutes)")
        print("="*60)
        
        mem_thread = threading.Thread(target=start_memory_stress, daemon=True)  # <-- DAEMON
        mem_thread.start()
        
        for remaining in range(30, 0, -1):
            if remaining % 5 == 0 or remaining <= 3:
                print(f"   [MEMORY] {remaining} minute{'s' if remaining > 1 else ''} remaining...")
            time.sleep(60)
        
        stop_memory_stress()
        print("   Cooling down for 5 seconds...")
        time.sleep(5)
        print("   ✅ Memory Phase Completed. Proceeding to Disk...\n")
        
        # PHASE 3: DISK (Daemon thread)
        print("\n" + "="*60)
        print("  ⏳ PHASE: DISK (Duration: 30 minutes)")
        print("="*60)
        
        disk_thread = threading.Thread(target=start_disk_stress, daemon=True)  # <-- DAEMON
        disk_thread.start()
        
        for remaining in range(30, 0, -1):
            if remaining % 5 == 0 or remaining <= 3:
                print(f"   [DISK] {remaining} minute{'s' if remaining > 1 else ''} remaining...")
            time.sleep(60)
        
        stop_disk_stress()
        print("   Cooling down for 5 seconds...")
        time.sleep(5)
        print("   ✅ Disk Phase Completed. Proceeding to Combined...\n")
        
        # PHASE 4: COMBINED
        print("\n" + "="*60)
        print("  ⏳ PHASE: COMBINED (Duration: 30 minutes)")
        print("  🔥 Running CPU + Memory + Disk TOGETHER")
        print("="*60)
        
        cpu_procs = start_cpu_stress()
        mem_thread = threading.Thread(target=start_memory_stress, daemon=True)
        mem_thread.start()
        disk_thread = threading.Thread(target=start_disk_stress, daemon=True)
        disk_thread.start()
        
        for remaining in range(30, 0, -1):
            if remaining % 5 == 0 or remaining <= 3:
                print(f"   [COMBINED] {remaining} minute{'s' if remaining > 1 else ''} remaining...")
            time.sleep(60)
        
        stop_cpu_stress(cpu_procs)
        stop_memory_stress()
        stop_disk_stress()
        
        print("\n" + "="*60)
        print("  🎉 ALL STRESS PHASES COMPLETED SUCCESSFULLY!")
        print("  Total time elapsed: 2 Hours.")
        print("="*60)

    except KeyboardInterrupt:
        print("\n\n🛑 Interrupted by user. Force cleaning up...")
        stop_memory_stress()
        stop_disk_stress()
        try:
            for p in cpu_procs:
                p.terminate()
        except:
            pass
        print("   Cleanup complete. Exiting.")

if __name__ == "__main__":
    main()