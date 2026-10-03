"""
HIGH Workload — combined CPU + Memory + Disk from the start.
Matches training HIGH signature (high CPU + high disk).
"""
import multiprocessing
import threading
import time
import os
import psutil

def cpu_worker():
    while True:
        _ = sum(i * i for i in range(10000))

def disk_worker():
    chunk = os.urandom(50 * 1024 * 1024)  # 50 MB
    fn = "high_temp.bin"
    while True:
        try:
            with open(fn, "wb") as f:
                f.write(chunk)
            os.remove(fn)
        except Exception:
            pass

_mem_holder = []
_mem_running = True

def memory_worker():
    global _mem_holder
    total = psutil.virtual_memory().total
    target = int(total * 0.30)  # allocate 30% of RAM
    allocated = 0
    while _mem_running and allocated < target:
        try:
            chunk = bytearray(50 * 1024 * 1024)
            _mem_holder.append(chunk)
            allocated += len(chunk)
            time.sleep(0.05)
        except MemoryError:
            break

def main():
    print("="*60)
    print("  HIGH WORKLOAD — CPU + Memory + Disk combined")
    print("="*60)
    input("Press ENTER to start...")

    # CPU
    cpu_procs = []
    for _ in range(psutil.cpu_count(logical=True)):
        p = multiprocessing.Process(target=cpu_worker)
        p.daemon = True
        p.start()
        cpu_procs.append(p)
    print(f"[CPU] Spawned {len(cpu_procs)} workers")

    # Disk
    for _ in range(3):
        t = threading.Thread(target=disk_worker, daemon=True)
        t.start()
    print(f"[DISK] Started 3 disk writers")

    # Memory
    t = threading.Thread(target=memory_worker, daemon=True)
    t.start()
    print(f"[MEM] Allocating 30% RAM")

    try:
        while True:
            cpu = psutil.cpu_percent(interval=2)
            mem = psutil.virtual_memory().percent
            print(f"  Live: CPU={cpu:.1f}%  MEM={mem:.1f}%")
            time.sleep(3)
    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        for p in cpu_procs:
            p.terminate()
        _mem_holder.clear()
        if os.path.exists("high_temp.bin"):
            os.remove("high_temp.bin")
        print("Cleanup done.")

if __name__ == "__main__":
    main()