"""
=========================================================
MERGE, LABEL, AND BALANCE DATASET
=========================================================
Loads all Normal and High Load CSVs from your folders,
adds labels, merges them, and creates balanced datasets.
=========================================================
"""

import pandas as pd
import glob
import os

# ---------------------------------------------------------
# Step 1: Find and Load ALL CSV files
# ---------------------------------------------------------
print("="*60)
print("STEP 1: Loading all CSV files...")
print("="*60)

# Paths to your folders
normal_path = "datasets/normal/*.csv"
highload_path = "datasets/high_load/*.csv"

# Load Normal CSVs (Label = 0)
normal_files = glob.glob(normal_path)
normal_dfs = []
for f in normal_files:
    df = pd.read_csv(f)
    df['Label'] = 0  # Normal
    normal_dfs.append(df)
    print(f"   Loaded Normal: {os.path.basename(f)} -> {len(df)} rows")

# Load High Load CSVs (Label = 1)
high_files = glob.glob(highload_path)
high_dfs = []
for f in high_files:
    df = pd.read_csv(f)
    df['Label'] = 1  # High Load
    high_dfs.append(df)
    print(f"   Loaded High Load: {os.path.basename(f)} -> {len(df)} rows")

# Merge into one master DataFrame
master_df = pd.concat(normal_dfs + high_dfs, ignore_index=True)
print(f"\n✅ TOTAL ROWS LOADED: {len(master_df)}")

# ---------------------------------------------------------
# Step 2: Separate classes for balancing
# ---------------------------------------------------------
print("\n" + "="*60)
print("STEP 2: Balancing Dataset...")
print("="*60)

normal_df = master_df[master_df['Label'] == 0]    # 28,800 rows
highload_df = master_df[master_df['Label'] == 1]  # 8,366 rows

print(f"Original Normal: {len(normal_df)}")
print(f"Original High Load: {len(highload_df)}")

# Downsample Normal to match High Load count
normal_sampled = normal_df.sample(n=len(highload_df), random_state=42)

# Combine and Shuffle
balanced_df = pd.concat([normal_sampled, highload_df])
balanced_df = balanced_df.sample(frac=1, random_state=42).reset_index(drop=True)

print(f"\n✅ Balanced Dataset Created!")
print(f"   New Normal: {len(balanced_df[balanced_df['Label'] == 0])}")
print(f"   New High Load: {len(balanced_df[balanced_df['Label'] == 1])}")
print(f"   Total: {len(balanced_df)}")

# ---------------------------------------------------------
# Step 3: Save the outputs
# ---------------------------------------------------------
print("\n" + "="*60)
print("STEP 3: Saving Datasets...")
print("="*60)

# Ensure the 'datasets' folder exists
os.makedirs("datasets", exist_ok=True)

# Save Balanced (For Supervised: RF, XGB, LSTM)
balanced_df.to_csv("datasets/training_balanced_supervised.csv", index=False)
print("✅ Saved: datasets/training_balanced_supervised.csv (16,732 rows)")

# Save Full (For Unsupervised: Isolation Forest, etc.)
master_df.to_csv("datasets/training_full_unsupervised.csv", index=False)
print("✅ Saved: datasets/training_full_unsupervised.csv (37,166 rows)")

print("\n" + "="*60)
print("🎉 DATASET PREPARATION COMPLETE!")
print("="*60)