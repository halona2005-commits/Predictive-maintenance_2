import os
import sys
import csv
import time
import json
import platform
import subprocess
import urllib.request
from datetime import datetime
from pathlib import Path
import psutil

# ---------- CONFIG ----------
# Auto-detect the DataCollector folder relative to the testing folder
PROJECT = Path(__file__).resolve().parent.parent / "DataCollector" / "collector"
TESTS_DIR = Path(__file__).resolve().parent
LOGS_DIR = TESTS_DIR / "logs"
MASTER = TESTS_DIR / "master_results.csv"
API = "http://127.0.0.1:8000/predict"
POLL_INTERVAL = 5

def get_cpu_name():
    try:
        out = subprocess.run(["wmic", "cpu", "get", "name"], capture_output=True, text=True, timeout=5).stdout
        lines = [l.strip() for l in out.splitlines() if l.strip() and "Name" not in l]
        if lines: return lines[0]
    except Exception: pass
    return platform.processor() or "Unknown CPU"

def get_ram_gb():
    try: return f"{round(psutil.virtual_memory().total / (1024**3))}GB"
    except Exception: return "Unknown"

def poll():
    try:
        with urllib.request.urlopen(API, timeout=5) as r: return json.loads(r.read())
    except Exception as e: return {"error": str(e)}

def sanity_check():
    r = poll()
    if "error" in r:
        print("❌ Backend not responding:", r["error"])
        sys.exit(1)
    print(f"✅ Backend alive | Current: {r.get('risk_level')}")

def kill_tree(pid):
    subprocess.run(["taskkill", "/F", "/T", "/PID", str(pid)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)

def run_phase(state, duration_min, out_path, workload_cmd=None, workload_input=None):
    end_time = time.time() + duration_min * 60
    correct = total = 0
    buffer = []
    last_progress = time.time()
    workload = None

    if workload_cmd:
        print(f"\n▶️  Launching: {' '.join(workload_cmd)}")
        try:
            workload = subprocess.Popen(
                workload_cmd, 
                cwd=str(PROJECT), 
                stdin=subprocess.PIPE, 
                stdout=subprocess.DEVNULL, 
                stderr=subprocess.DEVNULL
            )
            time.sleep(2)
            # Check if the process crashed instantly (e.g., missing psutil)
            if workload.poll() is not None:
                print(f"   ⚠️ Workload crashed immediately. Missing library? (Check 'pip install psutil')")
            elif workload_input:
                try:
                    workload.stdin.write(workload_input.encode())
                    workload.stdin.flush()
                except OSError:
                    pass # Ignore broken pipe if process died during write
        except Exception as e:
            print(f"   ❌ Failed to launch workload. Check path: {PROJECT}")
            print(f"   Error: {e}")
            return {"total": 0, "correct": 0, "acc": 0}

    os.makedirs(out_path.parent, exist_ok=True)
    with open(out_path, "w", newline="") as f:
        csv.writer(f).writerow(["timestamp", "expected", "predicted", "confidence", "correct"])

    print(f"⏱️  Running for {duration_min} min | Ctrl+C to stop early\n")

    try:
        while time.time() < end_time:
            r = poll()
            if "error" in r:
                time.sleep(POLL_INTERVAL); continue

            pred = (r.get("risk_level") or "UNKNOWN").upper()
            conf = r.get("confidence", 0.0)
            ts = datetime.now().strftime("%H:%M:%S")
            ok = 1 if pred == state else 0

            correct += ok; total += 1
            buffer.append([ts, state, pred, conf, ok])

            if len(buffer) >= 5:
                with open(out_path, "a", newline="") as f: csv.writer(f).writerows(buffer)
                buffer = []

            if time.time() - last_progress >= 30:
                acc = correct / total * 100 if total else 0
                rem = int(end_time - time.time())
                print(f"   [{ts}] expected={state} acc={acc:5.1f}%  remaining={rem//60}m{rem%60}s")
                last_progress = time.time()
            time.sleep(POLL_INTERVAL)
    except KeyboardInterrupt:
        print("\n⚠️ Phase stopped early.")
    finally:
        if buffer:
            with open(out_path, "a", newline="") as f: csv.writer(f).writerows(buffer)
        if workload:
            kill_tree(workload.pid); time.sleep(1)

    acc = correct / total * 100 if total else 0
    print(f"\n✅ {state}: {total} samples | {correct} correct | accuracy = {acc:.2f}%")
    return {"total": total, "correct": correct, "acc": acc}

def append_master(pc, cpu, ram, n, m, h):
    o_total = n["total"] + m["total"] + h["total"]
    o_correct = n["correct"] + m["correct"] + h["correct"]
    overall = o_correct / o_total * 100 if o_total else 0
    row = [pc, cpu, ram, f"{n['acc']:.2f}%", f"{m['acc']:.2f}%", f"{h['acc']:.2f}%", f"{overall:.2f}%"]
    header_needed = not MASTER.exists()
    with open(MASTER, "a", newline="") as f:
        w = csv.writer(f)
        if header_needed: w.writerow(["PC", "CPU", "RAM", "Normal Acc", "Mod Acc", "High Acc", "Overall Acc"])
        w.writerow(row)
    print(f"\n📊 Master results updated: {MASTER}")

def main():
    print("=" * 70); print("  Predictive Maintenance — Test Runner"); print("=" * 70)
    sanity_check()
    cpu = get_cpu_name(); ram = get_ram_gb()
    print(f"🔍 CPU: {cpu} | RAM: {ram}")
    
    pc = input("\nPC label [auto: hostname]: ").strip() or platform.node()
    dur_raw = input("Duration per state [3]: ").strip()
    dur = int(dur_raw) if dur_raw else 3

    input("\nPress ENTER to start...")

    # 1. NORMAL
    print("\n" + "=" * 70 + "\n  TEST 1/3 — NORMAL\n" + "=" * 70)
    input("Close heavy apps now, then press ENTER...")
    n = run_phase("NORMAL", dur, LOGS_DIR / f"{pc}_normal.csv")

    # 2. MODERATE
    print("\n" + "=" * 70 + "\n  TEST 2/3 — MODERATE\n" + "=" * 70)
    input("Press ENTER to launch moderate workload...")
    m = run_phase("MODERATE", dur, LOGS_DIR / f"{pc}_moderate.csv", workload_cmd=[sys.executable, "moderate_data.py"], workload_input=f"{pc}\ny\n")

    # 3. HIGH
    print("\n" + "=" * 70 + "\n  TEST 3/3 — HIGH\n" + "=" * 70)
    input("Press ENTER to launch combined stress workload...")
    h = run_phase("HIGH", dur, LOGS_DIR / f"{pc}_high.csv", workload_cmd=[sys.executable, "combined_stress.py"], workload_input="\n")

    print("\n" + "=" * 70 + "\n  ✅ ALL TESTS COMPLETE\n" + "=" * 70)
    append_master(pc, cpu, ram, n, m, h)

if __name__ == "__main__":
    main()