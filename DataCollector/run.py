"""
=========================================================
Predictive Maintenance - Data Collector
=========================================================
Run this file to collect datasets.
=========================================================
"""

from collector.collector import start_collection

from collector.hardware import get_hardware_info

from collector.config import (
    NORMAL_DATASET_DIR,
    HIGHLOAD_DATASET_DIR,
    COLLECTION_INTERVAL,
    COLLECTION_DURATION
)


def main():

    hardware = get_hardware_info()

    print("\n" + "=" * 60)
    print("      Predictive Maintenance Data Collector")
    print("=" * 60)

    print(f"\nDetected Computer : {hardware['hostname']}")
    print(f"Processor         : {hardware['processor']}")
    print(f"Operating System  : {hardware['os']}")
    print(f"RAM               : {hardware['total_ram_gb']} GB")

    print("\nSelect Dataset Type\n")

    print("1. Normal Behaviour")
    print("2. Controlled High Load")

    while True:

        choice = input("\nEnter choice (1/2): ").strip()

        if choice == "1":

            dataset_dir = NORMAL_DATASET_DIR
            dataset_name = "Normal Behaviour"
            break

        elif choice == "2":

            dataset_dir = HIGHLOAD_DATASET_DIR
            dataset_name = "Controlled High Load"
            break

        else:

            print("Invalid choice. Please enter 1 or 2.")

    print("\n" + "-" * 60)
    print(f"Dataset            : {dataset_name}")
    print(f"Collection Time    : {COLLECTION_DURATION // 3600} Hour(s)")
    print(f"Collection Interval: {COLLECTION_INTERVAL} Seconds")
    print(f"Expected Samples   : {COLLECTION_DURATION // COLLECTION_INTERVAL}")
    print("-" * 60)

    input("\nPress ENTER to start collection...")

    start_collection(dataset_dir)


if __name__ == "__main__":
    main()