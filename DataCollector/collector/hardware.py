"""
=========================================================
Predictive Maintenance - Hardware Information
=========================================================
Collects static hardware information of the system.
This information is collected only once per session.
=========================================================
"""

import socket
import platform
import psutil


def get_hardware_info():
    """
    Returns static hardware information of the system.
    """

    memory = psutil.virtual_memory()

    info = {
        "hostname": socket.gethostname(),
        "processor": platform.processor(),
        "os": platform.system(),
        "os_version": platform.version(),
        "architecture": platform.machine(),
        "physical_cores": psutil.cpu_count(logical=False),
        "logical_cores": psutil.cpu_count(logical=True),
        "total_ram_gb": round(memory.total / (1024 ** 3), 2),
    }

    return info


if __name__ == "__main__":
    hardware = get_hardware_info()

    print("\n========== Hardware Information ==========\n")

    for key, value in hardware.items():
        print(f"{key:20}: {value}")