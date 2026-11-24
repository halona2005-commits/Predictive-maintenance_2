import multiprocessing
import threading
import time
import os
import psutil

def cpu_worker():
    while True:
        # Busy loop to max out CPU
        _ = sum(i * i for i in range(10000))

def memory_worker():
    hog = []
    try:
        while True:
            # Allocate 50MB chunks until we hit 88% memory usage
            if psutil.virtual_memory().percent < 88:
                hog.append(bytearray(50 * 1024 * 1024))
            time.sleep(0.1)
    except MemoryError:
        pass

def disk_worker():
    chunk = b'0' * (10 * 1024 * 1024) # 10 MB chunk
    file_name = "stress_temp.bin"
    while True:
        try:
            with open(file_name, 'ab') as f:
                for _ in range(20): # Write 200MB rapidly
                    f.write(chunk)
                f.flush()
            # Delete file if it gets too large to avoid filling the hard drive
            if os.path.getsize(file_name) > 500 * 1024 * 1024: 
                os.remove(file_name)
        except Exception:
            pass

if __name__ == "__main__":
    print("=" * 60)
    print("🔥 STARTING COMBINED HIGH-RISK STRESS")
    print("   (CPU + Memory + Disk simultaneously)")
    print("=" * 60)
    print("Press Ctrl+C to stop.\n")
    
    # 1. Start CPU Stress
    cpu_procs = []
    for _ in range(psutil.cpu_count(logical=True)):
        p = multiprocessing.Process(target=cpu_worker)
        p.daemon = True
        p.start()
        cpu_procs.append(p)

    # 2. Start Memory Stress
    mem_thread = threading.Thread(target=memory_worker, daemon=True)
    mem_thread.start()

    # 3. Start Disk Stress
    for _ in range(3):
        disk_thread = threading.Thread(target=disk_worker, daemon=True)
        disk_thread.start()

    try:
        while True:
            # Print live stats every 3 seconds
            cpu = psutil.cpu_percent(interval=None)
            mem = psutil.virtual_memory().percent
            print(f"[Live] CPU: {cpu:.1f}% | Memory: {mem:.1f}%")
            time.sleep(3)
    except KeyboardInterrupt:
        print("\nStopping stress...")
        for p in cpu_procs:
            p.terminate()
        if os.path.exists("stress_temp.bin"):
            try:
                os.remove("stress_temp.bin")
            except:
                pass
        print("✅ Cleanup done. Exiting.")