"""
=========================================================
FEATURE ENGINEERING PIPELINE (DEBUG + FALLBACK)
=========================================================
"""

import pandas as pd
import numpy as np
import os
import glob
import sys

WINDOW_SIZE = 300
MIN_ROWS_FOR_ROLLING = 300

print("="*60)
print("  FEATURE ENGINEERING PIPELINE (DEBUG + FALLBACK)")
print("="*60)
print(f"Window Size: {WINDOW_SIZE} seconds (5 minutes)")
print(f"Minimum rows for rolling window: {MIN_ROWS_FOR_ROLLING}")

# ---------------------------------------------------------
# STEP 1: Load all CSV files individually
# ---------------------------------------------------------
print("\n[1/4] Loading individual CSV files...")

def load_all_files():
    all_dfs = []
    normal_files = glob.glob("datasets/normal/*.csv")
    for f in normal_files:
        df = pd.read_csv(f)
        df['Label'] = 0
        df['source_file'] = os.path.basename(f)
        all_dfs.append(df)
        print(f"   Loaded: {os.path.basename(f)} -> {len(df)} rows")
    
    high_files = glob.glob("datasets/high_load/*.csv")
    for f in high_files:
        df = pd.read_csv(f)
        df['Label'] = 1
        df['source_file'] = os.path.basename(f)
        all_dfs.append(df)
        print(f"   Loaded: {os.path.basename(f)} -> {len(df)} rows")
    return all_dfs

all_dfs = load_all_files()

if not all_dfs:
    print("❌ No CSV files found!")
    sys.exit(1)

# ---------------------------------------------------------
# STEP 2: Clean missing values
# ---------------------------------------------------------
print("\n[2/4] Cleaning missing values...")

def clean_nans(df):
    ssd_cols = ['ssd_percentage_used', 'ssd_available_spare', 
                'ssd_temperature', 'ssd_data_written_tb', 
                'ssd_power_on_hours', 'ssd_media_errors']
    for col in ssd_cols:
        if col in df.columns:
            df[col] = df[col].replace('', 0).fillna(0)
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
    numeric_cols = ['cpu_percent', 'memory_percent', 'disk_percent', 
                    'disk_read_mbps', 'disk_write_mbps',
                    'network_upload_mbps', 'network_download_mbps',
                    'process_count']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    return df

for i, df in enumerate(all_dfs):
    all_dfs[i] = clean_nans(df)

# ---------------------------------------------------------
# STEP 3: Engineer features per file with diagnostics
# ---------------------------------------------------------
print("\n[3/4] Engineering features per file...")

def engineer_single_file(df, file_name):
    df = df.copy()
    df = df.sort_values('timestamp').reset_index(drop=True)
    
    # --- Derived Raw Metrics ---
    df['Disk_IO'] = df['disk_read_mbps'] + df['disk_write_mbps']
    df['Network_Total'] = df['network_upload_mbps'] + df['network_download_mbps']
    df['SSD_Health'] = 100 - df['ssd_percentage_used']
    
    # --- Rolling Z-Scores (CPU, Memory, Disk, Network) ---
    # We do NOT compute SSD Z-score here because it's constant → division by zero.
    if len(df) >= MIN_ROWS_FOR_ROLLING:
        cpu_rolling_mean = df['cpu_percent'].rolling(window=WINDOW_SIZE).mean()
        cpu_rolling_std = df['cpu_percent'].rolling(window=WINDOW_SIZE).std()
        df['CPU_Zscore'] = (df['cpu_percent'] - cpu_rolling_mean) / cpu_rolling_std
        
        mem_rolling_mean = df['memory_percent'].rolling(window=WINDOW_SIZE).mean()
        mem_rolling_std = df['memory_percent'].rolling(window=WINDOW_SIZE).std()
        df['Memory_Zscore'] = (df['memory_percent'] - mem_rolling_mean) / mem_rolling_std
        
        disk_rolling_mean = df['Disk_IO'].rolling(window=WINDOW_SIZE).mean()
        disk_rolling_std = df['Disk_IO'].rolling(window=WINDOW_SIZE).std()
        df['Disk_Zscore'] = (df['Disk_IO'] - disk_rolling_mean) / disk_rolling_std
        
        net_rolling_mean = df['Network_Total'].rolling(window=WINDOW_SIZE).mean()
        net_rolling_std = df['Network_Total'].rolling(window=WINDOW_SIZE).std()
        df['Network_Zscore'] = (df['Network_Total'] - net_rolling_mean) / net_rolling_std
    else:
        df['CPU_Zscore'] = 0
        df['Memory_Zscore'] = 0
        df['Disk_Zscore'] = 0
        df['Network_Zscore'] = 0
    
    # ✅ KEY FIX: Set SSD_Health_Zscore to 0 (since it's constant)
    # Do NOT include this in dropna()!
    df['SSD_Health_Zscore'] = 0
    
    # --- Domain-Knowledge Features ---
    df['Memory_Pressure'] = df['memory_percent'] * (1 + df['disk_write_mbps'].clip(lower=0) / 10)
    df['CPU_Efficiency'] = df['cpu_percent'] / (df['process_count'].clip(lower=1))
    df['System_Saturation'] = (df['cpu_percent'] / 100) + (df['memory_percent'] / 100) + (df['Disk_IO'].clip(lower=0) / 500)
    df['SSD_Wear'] = (100 - df['SSD_Health']) / 100
    
    # Replace infinity with NaN
    df = df.replace([np.inf, -np.inf], np.nan)
    
    # ✅ CRITICAL: Drop NaNs ONLY for the 4 main Z-scores.
    # SSD_Health_Zscore is NOT in this list!
    zscore_cols = ['CPU_Zscore', 'Memory_Zscore', 'Disk_Zscore', 'Network_Zscore']
    initial_rows = len(df)
    df = df.dropna(subset=zscore_cols)
    dropped = initial_rows - len(df)
    
    # Fallback (just in case, though it won't trigger now)
    if len(df) == 0:
        for col in zscore_cols:
            df[col] = 0
        print(f"   ⚠️  {file_name}: All rows dropped! Filled Z-scores with 0.")
    
    print(f"   {file_name}: {initial_rows} -> {len(df)} rows (dropped {dropped} rows)")
    
    # --- Final feature selection ---
    feature_columns = [
        'CPU_Zscore', 'Memory_Zscore', 'Disk_Zscore', 'Network_Zscore', 'SSD_Health_Zscore',
        'Memory_Pressure', 'CPU_Efficiency', 'System_Saturation', 'SSD_Wear',
        'Label'
    ]
    
    # Ensure all columns exist
    for col in feature_columns:
        if col not in df.columns:
            df[col] = 0
    
    return df[feature_columns]

engineered_dfs = []
for df in all_dfs:
    file_name = df['source_file'].iloc[0]
    engineered = engineer_single_file(df, file_name)
    if len(engineered) > 0:
        engineered_dfs.append(engineered)
        print(f"   ✅ {file_name}: {len(engineered)} rows kept")
    else:
        print(f"   ❌ {file_name}: 0 rows kept - skipping")

# ---------------------------------------------------------
# STEP 4: Concatenate and Save
# ---------------------------------------------------------
print("\n[4/4] Concatenating and saving...")

if not engineered_dfs:
    print("❌ ERROR: No data was engineered!")
    sys.exit(1)

full_engineered = pd.concat(engineered_dfs, ignore_index=True)
print(f"   ✅ Full Engineered: {len(full_engineered)} rows")
full_engineered.to_csv("datasets/engineered_full_final.csv", index=False)

normal_engineered = full_engineered[full_engineered['Label'] == 0]
highload_engineered = full_engineered[full_engineered['Label'] == 1]

print(f"\n   Normal: {len(normal_engineered)} rows")
print(f"   High Load: {len(highload_engineered)} rows")

if len(normal_engineered) > 0 and len(highload_engineered) > 0:
    normal_sampled = normal_engineered.sample(n=len(highload_engineered), random_state=42)
    balanced_engineered = pd.concat([normal_sampled, highload_engineered])
    balanced_engineered = balanced_engineered.sample(frac=1, random_state=42).reset_index(drop=True)
    balanced_engineered.to_csv("datasets/engineered_balanced_final.csv", index=False)
    print(f"   ✅ Saved: datasets/engineered_balanced_final.csv ({len(balanced_engineered)} rows)")
else:
    print("   ⚠️  Not enough data to create balanced dataset")

print("\n" + "="*60)
print("  ✅ FEATURE ENGINEERING COMPLETE!")
print("="*60)
print(f"\n📊 Final Summary:")
print(f"   Full Engineered: {len(full_engineered)} rows")
print(f"   Balanced Engineered: {len(balanced_engineered) if len(highload_engineered) > 0 else 0} rows")
print("="*60)