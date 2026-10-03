"""
Moderate Workload — reliable 30-50% CPU + 65% memory allocation
Replaces original moderate_data.py which was too gentle.
"""
import multiprocessing
import threading
import time
import os
import psutil
import sys

# --- CONFIG ---
TARGET_CPU_FRACTION = 0.15   # aim for ~35% CPU across cores
TARGET_MEM_PCT = 15        # aim for ~65% memory usage
DISK_MB_PER_SEC = 1        # moderate disk write

# --- CPU WORKER ---
def cpu_worker():
    """Runs continuously with duty cycle."""
    cycle = 0.05  # 50ms cycles
    busy = cycle * TARGET_CPU_FRACTION
    idle = cycle * (1 - TARGET_CPU_FRACTION)
    while True:
        t0 = time.time()
        while time.time() - t0 < busy:
            _ = sum(i * i for i in range(3000))
        time.sleep(idle)

def start_cpu():
    n = max(2, psutil.cpu_count(logical=True) // 3)  # 1/3 of cores
    procs = []
    for _ in range(n):
        p = multiprocessing.Process(target=cpu_worker)
        p.start()
        procs.append(p)
    print(f"[CPU] Spawned {n} workers at ~{TARGET_CPU_FRACTION*100:.0f}% duty each")
    return procs

def stop_cpu(procs):
    for p in procs:
        p.terminate()
    print("   CPU workers terminated.")

# --- MEMORY ---
_mem_holder = []
_mem_running = False

def memory_worker():
    global _mem_holder, _mem_running
    _mem_running = True
    total = psutil.virtual_memory().total
    target = int(total * TARGET_MEM_PCT / 100)
    allocated = 0
    while _mem_running and allocated < target:
        try:
            chunk = bytearray(50 * 1024 * 1024)  # 50 MB
            _mem_holder.append(chunk)
            allocated += len(chunk)
            time.sleep(0.05)
        except MemoryError:
            break
    print(f"[MEM] Allocated {allocated/(1024**3):.1f} GB")

def stop_memory():
    global _mem_holder, _mem_running
    _mem_running = False
    _mem_holder.clear()
    print("   Memory released.")

# --- DISK ---
_disk_running = False
DISK_FILE = "moderate_temp.bin"

def disk_worker():
    global _disk_running
    _disk_running = True
    chunk = b'0' * (1024 * 1024)  # 1 MB
    while _disk_running:
        try:
            with open(DISK_FILE, 'ab') as f:
                for _ in range(DISK_MB_PER_SEC):
                    f.write(chunk)
                f.flush()
            os.remove(DISK_FILE)
            time.sleep(1)
        except Exception:
            pass

def stop_disk():
    global _disk_running
    _disk_running = False
    time.sleep(0.5)
    if os.path.exists(DISK_FILE):
        try:
            os.remove(DISK_FILE)
        except:
            pass
    print("   Disk stress stopped.")

# --- MAIN ---
def main():
    print("="*60)
    print("  MODERATE WORKLOAD GENERATOR (reliable version)")
    print(f"  Target: ~{TARGET_CPU_FRACTION*100:.0f}% CPU, ~{TARGET_MEM_PCT}% MEM, {DISK_MB_PER_SEC} MB/s disk")
    print("="*60)
    input("Press ENTER to start...")

    cpu_procs = start_cpu()
    mem_thread = threading.Thread(target=memory_worker, daemon=True)
    mem_thread.start()
    disk_thread = threading.Thread(target=disk_worker, daemon=True)
    disk_thread.start()

    try:
        print("\nWorkload running. Press Ctrl+C to stop.\n")
        while True:
            cpu = psutil.cpu_percent(interval=2)
            mem = psutil.virtual_memory().percent
            print(f"  Live: CPU={cpu:.1f}%  MEM={mem:.1f}%")
            time.sleep(3)
    except KeyboardInterrupt:
        print("\nStopping workload...")
    finally:
        stop_cpu(cpu_procs)
        stop_memory()
        stop_disk()
        print("Cleanup done.")

if __name__ == "__main__":
    main()