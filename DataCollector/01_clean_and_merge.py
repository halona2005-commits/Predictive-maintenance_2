import pandas as pd
import os

base = "datasets"
combined = []

# Define your state folders
state_folders = {
    "normal": "Normal",
    "moderate": "Moderate",
    "high": "High",
    "high_load": "High"  # Just in case your folder is named 'high_load'
}

# Loop through each state folder
for folder, label_name in state_folders.items():
    path = os.path.join(base, folder)
    if not os.path.isdir(path):
        continue  # Skip if folder doesn't exist
    
    print(f"📂 Reading folder: {folder}")
    files = [f for f in os.listdir(path) if f.endswith('.csv')]
    
    for file in files:
        file_path = os.path.join(path, file)
        df = pd.read_csv(file_path)

        features_to_keep = [
            'cpu_percent', 'cpu_frequency_mhz', 'memory_percent', 'memory_available_mb',
            'disk_percent', 'disk_read_mbps', 'disk_write_mbps',
            'network_upload_mbps', 'network_download_mbps', 'process_count'
        ]

        try:
            df_clean = df[features_to_keep].copy()
            df_clean['label'] = label_name   # <-- Adds the 'label' column
            combined.append(df_clean)
            print(f"✅ Added {len(df_clean)} rows from {file} (Label: {label_name})")
        except KeyError as e:
            print(f"❌ Skipping {file}: Missing column {e}")

# Merge all the data
full_df = pd.concat(combined, ignore_index=True)

# Add process ID
full_df['process_id'] = range(1, len(full_df) + 1)

# ============================================================
# BALANCING – robust loop
# ============================================================
target_samples = 8366
balanced_list = []

for label in full_df['label'].unique():
    subset = full_df[full_df['label'] == label]
    # If fewer rows, sample with replacement; else without
    sampled = subset.sample(
        n=target_samples,
        replace=len(subset) < target_samples,
        random_state=42
    )
    balanced_list.append(sampled)

balanced = pd.concat(balanced_list, ignore_index=True)

# Save
output_path = os.path.join(base, "final_training_data_3class.csv")
balanced.to_csv(output_path, index=False)

print(f"\n✅ Balanced dataset saved to: {output_path}")
print(f"Total rows: {len(balanced)} (8366 per class)")
print(f"Process IDs: {balanced['process_id'].min()} to {balanced['process_id'].max()}")

# Verify the columns
print("\n📋 Columns in saved CSV:")
print(balanced.columns.tolist())