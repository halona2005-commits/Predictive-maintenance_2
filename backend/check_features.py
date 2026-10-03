import pandas as pd

df = pd.read_csv(r'D:\projects\Predictive_maintenance_project\DataCollector\datasets\final_training_data_3class.csv')

features = [
    'cpu_percent', 'cpu_frequency_mhz', 'memory_percent', 'memory_available_mb',
    'disk_percent', 'disk_read_mbps', 'disk_write_mbps',
    'network_upload_mbps', 'network_download_mbps', 'process_count'
]

for f in features:
    print(f"\n=== {f} ===")
    print(df.groupby('label')[f].describe()[['mean', 'std', 'min', 'max']].round(2))