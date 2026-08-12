"""
=========================================================
Predictive Maintenance - Live Metrics Collection
=========================================================
Collects dynamic system metrics every 1 second.
Includes SSD Health monitoring via smartctl.
=========================================================
"""

import psutil
import datetime
import time
import subprocess
import re
import sys

# --------------------------------------------------------
# Initialize previous counters
# --------------------------------------------------------

_prev_disk = psutil.disk_io_counters()
_prev_net = psutil.net_io_counters()
_prev_time = time.time()

# Warm up CPU percentage
psutil.cpu_percent(interval=None)


def _get_top_process(attr='cpu_percent'):
    """
    Returns the name and PID of the process using the most CPU or Memory.
    """
    try:
        processes = []
        # Iterate over all running processes
        for proc in psutil.process_iter(['pid', 'name', attr]):
            try:
                processes.append(proc.info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                # Skip processes that disappear or are protected
                continue

        if not processes:
            return "unknown", 0

        # Sort descending by the attribute (CPU or Memory) and pick the highest
        top = sorted(processes, key=lambda x: x[attr] or 0, reverse=True)[0]
        return top['name'] or "unknown", top['pid']

    except Exception:
        return "unknown", 0


# --------------------------------------------------------
# SSD Health Functions
# --------------------------------------------------------

def _get_ssd_health():
    """
    Get SSD health metrics using smartctl (NVMe only).
    Returns: Dictionary with SSD health metrics.
    """
    try:
        # Path to smartctl executable (Windows)
        if sys.platform == "win32":
            smartctl_path = "C:\\Program Files\\smartmontools\\bin\\smartctl.exe"
        else:
            smartctl_path = "smartctl"  # Linux/macOS (assumes in PATH)
        
        # Run smartctl on C: drive
        cmd = [smartctl_path, "-a", "C:"]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        output = result.stdout
        
        # Extract metrics using regex
        metrics = {
            'ssd_model': None,
            'ssd_health_status': None,
            'ssd_percentage_used': None,
            'ssd_available_spare': None,
            'ssd_temperature': None,
            'ssd_data_written_tb': None,
            'ssd_power_on_hours': None,
            'ssd_media_errors': None
        }
        
        # Model Number
        match = re.search(r"Model Number:\s+(.+)", output)
        if match:
            metrics['ssd_model'] = match.group(1).strip()
        
        # Health Status
        match = re.search(r"SMART overall-health self-assessment test result:\s+(\w+)", output)
        if match:
            metrics['ssd_health_status'] = match.group(1).strip()
        
        # Percentage Used (NVMe)
        match = re.search(r"Percentage Used:\s+(\d+)%", output)
        if match:
            metrics['ssd_percentage_used'] = int(match.group(1))
        
        # Available Spare (NVMe)
        match = re.search(r"Available Spare:\s+(\d+)%", output)
        if match:
            metrics['ssd_available_spare'] = int(match.group(1))
        
        # Temperature (NVMe)
        match = re.search(r"Temperature:\s+(\d+) Celsius", output)
        if match:
            metrics['ssd_temperature'] = int(match.group(1))
        
        # Data Units Written (NVMe) - convert to TB
        match = re.search(r"Data Units Written:\s+[\[\(]?[\d,]+\s*[\]\)]?\s+\[([\d.]+)\s+(\w+)\]", output)
        if match:
            value = float(match.group(1))
            unit = match.group(2)
            if unit == "TB":
                metrics['ssd_data_written_tb'] = value
            elif unit == "GB":
                metrics['ssd_data_written_tb'] = value / 1024
            elif unit == "PB":
                metrics['ssd_data_written_tb'] = value * 1024
        
        # Power On Hours
        match = re.search(r"Power On Hours:\s+([\d,]+)", output)
        if match:
            metrics['ssd_power_on_hours'] = int(match.group(1).replace(',', ''))
        
        # Media and Data Integrity Errors
        match = re.search(r"Media and Data Integrity Errors:\s+([\d,]+)", output)
        if match:
            metrics['ssd_media_errors'] = int(match.group(1).replace(',', ''))
        
        return metrics
        
    except FileNotFoundError:
        # smartctl not installed
        return None
    except Exception:
        # Any other error
        return None


# --------------------------------------------------------
# Main Metrics Collection
# --------------------------------------------------------

def get_live_metrics():
    """
    Returns one snapshot of live system metrics + SSD health.
    """

    global _prev_disk, _prev_net, _prev_time

    current_time = time.time()
    elapsed = current_time - _prev_time

    # ---------------- CPU ----------------

    cpu_percent = psutil.cpu_percent(interval=None)

    cpu_freq = psutil.cpu_freq()
    cpu_frequency = round(cpu_freq.current, 2) if cpu_freq else 0

    # ---------------- Memory ----------------

    memory = psutil.virtual_memory()

    memory_percent = memory.percent

    memory_available_mb = round(
        memory.available / (1024 ** 2),
        2
    )

    # ---------------- Disk ----------------

    disk = psutil.disk_usage("/")

    current_disk = psutil.disk_io_counters()

    disk_read_mbps = 0
    disk_write_mbps = 0

    # Use 0.001 to avoid division by zero if system clock ticks too fast
    if elapsed > 0.001:

        disk_read_mbps = round(
            (current_disk.read_bytes - _prev_disk.read_bytes)
            / (1024 ** 2)
            / elapsed,
            2
        )

        disk_write_mbps = round(
            (current_disk.write_bytes - _prev_disk.write_bytes)
            / (1024 ** 2)
            / elapsed,
            2
        )

    # ---------------- Network ----------------

    current_net = psutil.net_io_counters()

    upload_speed = 0
    download_speed = 0

    if elapsed > 0.001:

        upload_speed = round(
            (current_net.bytes_sent - _prev_net.bytes_sent)
            / (1024 ** 2)
            / elapsed,
            2
        )

        download_speed = round(
            (current_net.bytes_recv - _prev_net.bytes_recv)
            / (1024 ** 2)
            / elapsed,
            2
        )

    # ---------------- Process ----------------

    process_count = len(psutil.pids())

    # Get the top CPU and Memory processes
    top_cpu_name, top_cpu_pid = _get_top_process('cpu_percent')
    top_mem_name, top_mem_pid = _get_top_process('memory_percent')

    # ---------------- SSD Health ----------------

    ssd = _get_ssd_health()

    # ---------------- Update previous counters ----------------

    _prev_disk = current_disk
    _prev_net = current_net
    _prev_time = current_time

    # ---------------- Return metrics ----------------

    return {

        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),

        "cpu_percent": cpu_percent,

        "cpu_frequency_mhz": cpu_frequency,

        "memory_percent": memory_percent,

        "memory_available_mb": memory_available_mb,

        "disk_percent": disk.percent,

        "disk_read_mbps": disk_read_mbps,

        "disk_write_mbps": disk_write_mbps,

        "network_upload_mbps": upload_speed,

        "network_download_mbps": download_speed,

        "process_count": process_count,

        "top_cpu_process": top_cpu_name,
        "top_cpu_pid": top_cpu_pid,
        "top_mem_process": top_mem_name,
        "top_mem_pid": top_mem_pid,

        # ---------------- SSD Health Metrics ----------------
        "ssd_model": ssd['ssd_model'] if ssd else None,
        "ssd_health_status": ssd['ssd_health_status'] if ssd else None,
        "ssd_percentage_used": ssd['ssd_percentage_used'] if ssd else None,
        "ssd_available_spare": ssd['ssd_available_spare'] if ssd else None,
        "ssd_temperature": ssd['ssd_temperature'] if ssd else None,
        "ssd_data_written_tb": ssd['ssd_data_written_tb'] if ssd else None,
        "ssd_power_on_hours": ssd['ssd_power_on_hours'] if ssd else None,
        "ssd_media_errors": ssd['ssd_media_errors'] if ssd else None
    }


# --------------------------------------------------------
# Test
# --------------------------------------------------------

if __name__ == "__main__":

    while True:

        metrics = get_live_metrics()

        print()

        for key, value in metrics.items():
            print(f"{key:30}: {value}")

        print("-" * 80)

        time.sleep(5)