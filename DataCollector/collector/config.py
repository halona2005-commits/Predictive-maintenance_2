"""
=========================================================
Predictive Maintenance - Data Collector Configuration
=========================================================
Author : Team
Purpose: Central configuration for the Data Collector
=========================================================
"""

from pathlib import Path

# =========================================================
# COLLECTION SETTINGS
# =========================================================

# Collect data every 5 seconds
COLLECTION_INTERVAL = 1

# Total collection time (2 Hours)
COLLECTION_DURATION = 2 * 60 * 60

# =========================================================
# PROJECT PATHS
# =========================================================

# DataCollector/
BASE_DIR = Path(__file__).resolve().parent.parent

# datasets/
DATASET_DIR = BASE_DIR / "datasets"

# datasets/normal/
NORMAL_DATASET_DIR = DATASET_DIR / "normal"

# datasets/high_load/
HIGHLOAD_DATASET_DIR = DATASET_DIR / "high_load"

# datasets/system_info/
SYSTEM_INFO_DIR = DATASET_DIR / "system_info"

# logs/
LOG_DIR = BASE_DIR / "logs"

# =========================================================
# DATASET TYPE
# =========================================================
# Change ONLY this when collecting a dataset.
#
# "normal"     -> Healthy laptop usage
# "high_load"  -> Controlled stress
#

DATASET_TYPE = "normal"

# =========================================================
# CSV HEADERS
# =========================================================

CSV_HEADERS = [
    "timestamp",
    "hostname",
    "cpu_percent",
    "cpu_frequency_mhz",
    "memory_percent",
    "memory_available_mb",
    "disk_percent",
    "disk_read_mbps",
    "disk_write_mbps",
    "network_upload_mbps",
    "network_download_mbps",
    "process_count",
    "top_cpu_process",
    "top_cpu_pid",
    "top_mem_process",
    "top_mem_pid",
    # SSD Health Metrics
    "ssd_model",
    "ssd_health_status",
    "ssd_percentage_used",
    "ssd_available_spare",
    "ssd_temperature",
    "ssd_data_written_tb",
    "ssd_power_on_hours",
    "ssd_media_errors"
]