"""
=========================================================
DEBUGGING SCRIPT - Find why rows are becoming NaN
=========================================================
"""

import pandas as pd
import numpy as np

# Load one file
df = pd.read_csv("datasets/normal/HI38_i5-6300U_normal.csv")

print("="*60)
print("DATA INSPECTION")
print("="*60)

print(f"\nTotal rows: {len(df)}")
print(f"Columns: {list(df.columns)}")

print("\n" + "="*60)
print("FIRST 5 ROWS")
print("="*60)
print(df.head())

print("\n" + "="*60)
print("NULL/NaN VALUES PER COLUMN")
print("="*60)
print(df.isnull().sum())

print("\n" + "="*60)
print("DATA TYPES")
print("="*60)
print(df.dtypes)

print("\n" + "="*60)
print("CHECKING SSD COLUMNS (Common culprit)")
print("="*60)

# Check specific columns
ssd_cols = ['ssd_percentage_used', 'ssd_available_spare', 'ssd_temperature', 
            'ssd_data_written_tb', 'ssd_power_on_hours', 'ssd_media_errors']

for col in ssd_cols:
    if col in df.columns:
        unique_vals = df[col].unique()[:10]
        print(f"\n{col}:")
        print(f"  Unique values: {unique_vals}")
        print(f"  Null count: {df[col].isnull().sum()}")
        print(f"  Type: {df[col].dtype}")

print("\n" + "="*60)
print("TESTING ROLLING WINDOW")
print("="*60)

# Test rolling window on CPU
cpu_rolling_mean = df['cpu_percent'].rolling(window=300).mean()
cpu_rolling_std = df['cpu_percent'].rolling(window=300).std()

print(f"\nCPU Rolling Mean:")
print(f"  First 10 values: {cpu_rolling_mean.head(10).tolist()}")
print(f"  Null count: {cpu_rolling_mean.isnull().sum()}")

print(f"\nCPU Rolling Std:")
print(f"  First 10 values: {cpu_rolling_std.head(10).tolist()}")
print(f"  Null count: {cpu_rolling_std.isnull().sum()}")

# Test Z-Score
cpu_zscore = (df['cpu_percent'] - cpu_rolling_mean) / cpu_rolling_std
print(f"\nCPU Z-Score:")
print(f"  First 10 values: {cpu_zscore.head(10).tolist()}")
print(f"  Null count: {cpu_zscore.isnull().sum()}")

print("\n" + "="*60)
print("FINDING FIRST NON-NAN ROW")
print("="*60)

# Find where all rolling columns become non-NaN
for i in range(300, 320):
    if not pd.isna(cpu_rolling_mean.iloc[i]):
        print(f"First valid row index: {i}")
        print(f"  CPU Rolling Mean at {i}: {cpu_rolling_mean.iloc[i]}")
        print(f"  CPU Rolling Std at {i}: {cpu_rolling_std.iloc[i]}")
        break