import pandas as pd
import os

# 1. Define the file paths
# (Adjust these filenames to match what is exactly inside your 'datasets' folder)
files = [
    "datasets/normal/haripriya_utlra5_normal.csv", "datasets/high_load/haripriya_ultra5_high.csv",
    "datasets/normal/hemi_i7-1620_normal.csv", "datasets/high_load/hemi_i7-1620_high.csv",
    "datasets/normal/HI38_i5-6300U_normal.csv", "datasets/high_load/HI38_i5-6300U_highload.csv",
    "datasets/normal/yathiswar_i7-1355U_normal.csv", "datasets/high_load/yathiswar_i7-1355U_high.csv"
]

# 2. Keep ONLY the strictly numeric, non-SSD columns that exist in ALL systems
# We drop hostname, timestamp, SSD columns, and the process name/pids.
keep_columns = [
    'cpu_percent', 'cpu_frequency_mhz',
    'memory_percent', 'memory_available_mb',
    'disk_percent', 'disk_read_mbps', 'disk_write_mbps',
    'network_upload_mbps', 'network_download_mbps',
    'process_count'
]

combined_data = []

print("🔄 Cleaning and combining files...")

for filepath in files:
    if not os.path.exists(filepath):
        print(f"⚠️ Skipping missing file: {filepath}")
        continue
        
    df = pd.read_csv(filepath)
    
    # 3. Assign the Label (0 = Normal, 1 = High)
    if "normal" in filepath.lower():
        df['label'] = 0
    elif "high" in filepath.lower():
        df['label'] = 1
    else:
        print(f"⚠️ Could not determine label for {filepath}. Skipping.")
        continue
        
    # 4. Keep only the columns we actually need
    try:
        clean_df = df[keep_columns + ['label']]
        combined_data.append(clean_df)
        print(f"✅ Processed {os.path.basename(filepath)} with {len(clean_df)} rows.")
    except KeyError as e:
        print(f"❌ Column mismatch in {filepath}: {e}")

# 5. Save the combined clean dataset
if combined_data:
    final_df = pd.concat(combined_data, ignore_index=True)
    output_file = "datasets/combined_normal_high.csv"
    final_df.to_csv(output_file, index=False)
    print(f"\n🎯 Step 1 complete! Combined data saved to: {output_file}")
    print(f"Total rows: {len(final_df)} (Normal: {len(final_df[final_df['label']==0])}, High: {len(final_df[final_df['label']==1])})")
else:
    print("\n❌ No files were processed. Check your filenames in the script.")