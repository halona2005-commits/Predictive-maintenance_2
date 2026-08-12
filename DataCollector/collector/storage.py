"""
=========================================================
Predictive Maintenance - Storage Module
=========================================================
Creates and manages CSV files.
=========================================================
"""

import csv
from pathlib import Path
from datetime import datetime

from collector.config import CSV_HEADERS


class CSVStorage:

    def __init__(self, dataset_directory, hostname):

        self.dataset_directory = Path(dataset_directory)

        self.dataset_directory.mkdir(
            parents=True,
            exist_ok=True
        )

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        self.file_path = (
            self.dataset_directory /
            f"{hostname}_{timestamp}.csv"
        )

        self.file = open(
            self.file_path,
            mode="w",
            newline="",
            encoding="utf-8"
        )

        self.writer = csv.DictWriter(
            self.file,
            fieldnames=CSV_HEADERS
        )

        self.writer.writeheader()

    # -----------------------------------------------------

    def write(self, row):

        self.writer.writerow(row)

    # -----------------------------------------------------

    def close(self):

        self.file.close()

    # -----------------------------------------------------

    @property
    def filename(self):

        return self.file_path