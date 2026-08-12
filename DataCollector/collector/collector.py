"""
=========================================================
Predictive Maintenance - Data Collector Engine
=========================================================
Coordinates hardware, metrics and storage.
=========================================================
"""

import time

from collector.config import (
    COLLECTION_INTERVAL,
    COLLECTION_DURATION,
)

from collector.hardware import get_hardware_info
from collector.metrics import get_live_metrics
from collector.storage import CSVStorage


def start_collection(dataset_directory):

    # ---------------------------------------------
    # Hardware Information
    # ---------------------------------------------

    hardware = get_hardware_info()

    hostname = hardware["hostname"]

    # ---------------------------------------------
    # Create CSV
    # ---------------------------------------------

    storage = CSVStorage(
        dataset_directory,
        hostname
    )

    total_samples = COLLECTION_DURATION // COLLECTION_INTERVAL

    print("\n=========================================")
    print("Collection Started")
    print("=========================================")
    print(f"Computer      : {hostname}")
    print(f"Total Samples : {total_samples}")
    print(f"Interval      : {COLLECTION_INTERVAL} sec")
    print("=========================================\n")

    try:

        for sample in range(total_samples):

            metrics = get_live_metrics()

            # Add hostname into every row
            metrics["hostname"] = hostname

            storage.write(metrics)

            print(
                f"[{sample+1}/{total_samples}] "
                f"CPU:{metrics['cpu_percent']:5.1f}%   "
                f"MEM:{metrics['memory_percent']:5.1f}%   "
                f"DiskW:{metrics['disk_write_mbps']:6.2f} MB/s"
            )

            time.sleep(COLLECTION_INTERVAL)

    except KeyboardInterrupt:

        print("\n\nCollection stopped by user.")

    finally:

        storage.close()

        print("\n=========================================")
        print("Collection Finished")
        print("=========================================")
        print(f"Dataset Saved : {storage.filename}")
        print("=========================================\n")

    return hardware