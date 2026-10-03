import joblib
import sqlite3
import pandas as pd

m = joblib.load(r'D:\projects\Predictive_maintenance_project\backend\app\xgboost_model.pkl')
s = joblib.load(r'D:\projects\Predictive_maintenance_project\backend\app\scaler.pkl')

features = ['cpu_percent','cpu_frequency_mhz','memory_percent','memory_available_mb',
            'disk_percent','disk_read_mbps','disk_write_mbps',
            'network_upload_mbps','network_download_mbps','process_count']

print("=== SCALER TRAINING STATS ===")
for i, f in enumerate(features):
    print(f"{f:25s} mean={s.mean_[i]:10.2f}  std={s.scale_[i]:10.2f}")

conn = sqlite3.connect(r'D:\projects\Predictive_maintenance_project\backend\predictive_maintenance.db')
row = pd.read_sql(
    'SELECT cpu_percent, cpu_frequency_mhz, memory_percent, memory_available_mb, '
    'disk_percent, disk_read_mbps, disk_write_mbps, network_upload_mbps, '
    'network_download_mbps, process_count FROM metrics ORDER BY id DESC LIMIT 1',
    conn)
conn.close()

print()
print("=== CURRENT LIVE VALUES ===")
for f in features:
    print(f"{f:25s} {row[f].iloc[0]:10.2f}")

scaled = s.transform(row)
print()
print("=== SCALED VALUES (z-score) ===")
for i, f in enumerate(features):
    z = scaled[0][i]
    flag = "  <-- OUTLIER" if abs(z) > 2 else ""
    print(f"{f:25s} {z:10.2f}{flag}")

print()
pred = m.predict(scaled)[0]
proba = m.predict_proba(scaled)[0]
print("Prediction (numeric):", pred)
print("Probabilities:", proba.round(4))