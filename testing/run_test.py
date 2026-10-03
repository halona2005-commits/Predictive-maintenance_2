"""
Predictive Maintenance — Full Test Runner
Runs NORMAL → MODERATE → HIGH tests sequentially.
Workloads (moderate_data.py, stress_sequencer.py) launch in NEW cmd windows
so you can answer their prompts manually.

USAGE:
  python run_tests.py
"""
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
WORKLOAD_DIR = Path(r"D:\projects\Predictive_maintenance_project\DataCollector\collector")
TESTS_DIR = Path(__file__).resolve().parent
LOGS_DIR = TESTS_DIR / "logs"
MASTER = TESTS_DIR / "master_results.csv"
API = "http://127.0.0.1:8000/predict"
POLL_INTERVAL = 5

# ---------- AUTO-DETECT SPECS ----------
def get_cpu_name():
    try:
        out = subprocess.run(
            ["wmic", "cpu", "get", "name"],
            capture_output=True, text=True, timeout=5
        ).stdout
        lines = [l.strip() for l in out.splitlines() if l.strip() and "Name" not in l]
        if lines:
            return lines[0]
    except Exception:
        pass
    return platform.processor() or "Unknown CPU"

def get_ram_gb():
    try:
        return f"{round(psutil.virtual_memory().total / (1024**3))}GB"
    except Exception:
        return "Unknown"

def get_specs():
    cpu = get_cpu_name()
    ram = get_ram_gb()
    print(f"🔍 Auto-detected specs:")
    print(f"   CPU: {cpu}")
    print(f"   RAM: {ram}")
    return cpu, ram

# ---------- API ----------
def poll():
    try:
        with urllib.request.urlopen(API, timeout=5) as r:
            return json.loads(r.read())
    except Exception as e:
        return {"error": str(e)}

def sanity_check():
    r = poll()
    if "error" in r:
        print("❌ Backend not responding:", r["error"])
        print(r"   Start backend first: cd backend && ..\.venv\Scripts\python.exe -m uvicorn app.main:app --reload")
        sys.exit(1)
    print(f"✅ Backend alive | Current: {r.get('risk_level')} ({r.get('confidence')}%)")

def launch_workload(script_name):
    """Open workload in a new cmd window. User answers prompts manually."""
    script_path = WORKLOAD_DIR / script_name
    if not script_path.exists():
        print(f"❌ Not found: {script_path}")
        return False
    # Use 'start' to spawn a new cmd window
    cmd = f'start "Workload: {script_name}" cmd /k "cd /d {WORKLOAD_DIR} && ..\\.venv\\Scripts\\python.exe {script_name}"'
    subprocess.Popen(cmd, shell=True)
    print(f"▶️  Launched {script_name} in new window — answer its prompts there.")
    return True

def kill_workload():
    """Kill all python processes spawned by workload (not backend)."""
    try:
        subprocess.run(
            'taskkill /F /FI "WINDOWTITLE eq Workload:*" /T',
            shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
    except Exception:
        pass

def run_phase(state, duration_min, out_path, workload_script=None):
    end_time = time.time() + duration_min * 60
    correct = total = 0
    buffer = []
    last_progress = time.time()

    if workload_script:
        launch_workload(workload_script)

    os.makedirs(out_path.parent, exist_ok=True)
    with open(out_path, "w", newline="") as f:
        csv.writer(f).writerow(["timestamp", "expected", "predicted", "confidence", "correct"])

    print(f"⏱️  Running for {duration_min} min | Ctrl+C to stop early\n")

    try:
        while time.time() < end_time:
            r = poll()
            if "error" in r:
                time.sleep(POLL_INTERVAL)
                continue

            pred = (r.get("risk_level") or "UNKNOWN").upper()
            conf = r.get("confidence", 0.0) or 0.0
            ts = datetime.now().strftime("%H:%M:%S")
            ok = 1 if pred == state else 0

            correct += ok
            total += 1
            buffer.append([ts, state, pred, conf, ok])

            if len(buffer) >= 5:
                with open(out_path, "a", newline="") as f:
                    csv.writer(f).writerows(buffer)
                buffer = []

            if time.time() - last_progress >= 30:
                acc = correct / total * 100 if total else 0
                rem = int(end_time - time.time())
                print(f"   [{ts}] expected={state} acc={acc:5.1f}%  remaining={rem//60}m{rem%60}s")
                last_progress = time.time()

            time.sleep(POLL_INTERVAL)

    except KeyboardInterrupt:
        print("\n⚠️ Phase stopped early by user.")

    finally:
        if buffer:
            with open(out_path, "a", newline="") as f:
                csv.writer(f).writerows(buffer)
        if workload_script:
            kill_workload()
            time.sleep(1)

    acc = correct / total * 100 if total else 0
    print(f"\n✅ {state}: {total} samples | {correct} correct | accuracy = {acc:.2f}%")
    return {"total": total, "correct": correct, "acc": acc}

def append_master(pc, cpu, ram, n, m, h):
    o_total = n["total"] + m["total"] + h["total"]
    o_correct = n["correct"] + m["correct"] + h["correct"]
    overall = o_correct / o_total * 100 if o_total else 0

    row = [pc, cpu, ram,
           f"{n['acc']:.2f}%", f"{m['acc']:.2f}%", f"{h['acc']:.2f}%",
           f"{overall:.2f}%"]

    header_needed = not MASTER.exists()
    with open(MASTER, "a", newline="") as f:
        w = csv.writer(f)
        if header_needed:
            w.writerow(["PC", "CPU", "RAM", "Normal Acc", "Mod Acc", "High Acc", "Overall Acc"])
        w.writerow(row)

    print(f"\n📊 Master results updated: {MASTER}")
    print("   " + " | ".join(row))

# ---------- MAIN ----------
def main():
    print("=" * 70)
    print("  Predictive Maintenance — Full Test Runner")
    print("=" * 70)
    sanity_check()

    cpu, ram = get_specs()
    pc = input("\nPC label (e.g. CollegePC1) [auto: hostname]: ").strip() or platform.node()
    dur_raw = input("Duration per state in minutes [30]: ").strip()
    dur = int(dur_raw) if dur_raw else 30

    print(f"\n📋 Plan: 3 tests × {dur} min = ~{dur*3} min total")
    print(f"   PC:  {pc}")
    print(f"   CPU: {cpu}")
    print(f"   RAM: {ram}")
    input("\nPress ENTER to start (Ctrl+C to cancel)...")

    # ---- TEST 1: NORMAL ----
    print("\n" + "=" * 70)
    print(f"  TEST 1/3 — NORMAL ({dur} min idle)")
    print("=" * 70)
    input("Close heavy apps now, then press ENTER...")
    n = run_phase("NORMAL", dur, LOGS_DIR / f"{pc}_normal.csv")

    # ---- TEST 2: MODERATE ----
    print("\n" + "=" * 70)
    print(f"  TEST 2/3 — MODERATE ({dur} min moderate_data.py)")
    print("=" * 70)
    input("Press ENTER to launch moderate workload (opens new window)...")
    print("   ➜ In the new window: enter PC label, then 'y' to start.")
    m = run_phase("MODERATE", dur, LOGS_DIR / f"{pc}_moderate.csv",
                  workload_script="moderate_data.py")

    # ---- TEST 3: HIGH ----
    print("\n" + "=" * 70)
    print(f"  TEST 3/3 — HIGH ({dur} min stress_sequencer.py)")
    print("=" * 70)
    input("Press ENTER to launch stress workload (opens new window)...")
    print("   ➜ In the new window: press ENTER to start.")
    h = run_phase("HIGH", dur, LOGS_DIR / f"{pc}_high.csv",
                  workload_script="high.py")

    # ---- SUMMARY ----
    print("\n" + "=" * 70)
    print("  ✅ ALL TESTS COMPLETE")
    print("=" * 70)
    append_master(pc, cpu, ram, n, m, h)
    print(f"\n📁 Per-phase logs: {LOGS_DIR}")
    print(f"📊 Master file: {MASTER}")

if __name__ == "__main__":
    main()