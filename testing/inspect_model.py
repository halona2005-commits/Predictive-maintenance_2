"""
Model Inspection — Reveals how CPU, memory, and disk features affect predictions.
"""
import joblib
import numpy as np
import pandas as pd
from pathlib import Path

# ---------- PATHS ----------
MODEL_DIR = Path(r"D:\projects\Predictive-maintenance_2\backend\app")
TRAIN_CSV = Path(r"D:\projects\Predictive-maintenance_2\DataCollector\datasets\final_training_data_3class.csv")

FEATURES = [
    'cpu_percent', 'cpu_frequency_mhz', 'memory_percent', 'memory_available_mb',
    'disk_percent', 'disk_read_mbps', 'disk_write_mbps',
    'network_upload_mbps', 'network_download_mbps', 'process_count'
]

print("=" * 90)
print("  MODEL INSPECTION — How Features Drive Predictions")
print("=" * 90)

# ---------- LOAD ----------
m = joblib.load(MODEL_DIR / "xgboost_model.pkl")
s = joblib.load(MODEL_DIR / "scaler.pkl")
le = joblib.load(MODEL_DIR / "label_encoder.pkl")

print(f"\n✅ Model loaded: {type(m).__name__}")
print(f"✅ Features: {m.n_features_in_}")
print(f"✅ Classes: {list(le.classes_)}")

# ---------- 1. FEATURE IMPORTANCE ----------
print("\n" + "=" * 90)
print("  1. FEATURE IMPORTANCE — Which features matter most")
print("=" * 90)

importances = m.feature_importances_
sorted_idx = np.argsort(importances)[::-1]
for i in sorted_idx:
    bar = '█' * int(importances[i] * 100)
    print(f"  {FEATURES[i]:25s} {importances[i]:.4f}  {bar}")

# ---------- 2. TRAINING DATA RANGES PER CLASS ----------
print("\n" + "=" * 90)
print("  2. TRAINING DATA RANGES — What values each class has")
print("=" * 90)

df = pd.read_csv(TRAIN_CSV)

for feature in ['cpu_percent', 'memory_percent', 'memory_available_mb',
                'disk_write_mbps', 'disk_read_mbps', 'disk_percent', 'process_count']:
    print(f"\n  ── {feature} ──")
    print(f"  {'Class':10s}  {'Mean':>10s}  {'Std':>10s}  {'Min':>10s}  {'Max':>10s}")
    for label in ['Normal', 'Moderate', 'High']:
        subset = df[df['label'] == label][feature]
        print(f"  {label:10s}  {subset.mean():10.2f}  {subset.std():10.2f}  "
              f"{subset.min():10.2f}  {subset.max():10.2f}")

# ---------- 3. SCALER MEAN/SCALE ----------
print("\n" + "=" * 90)
print("  3. SCALER STATS — How features are normalized")
print("=" * 90)

print(f"\n  {'Feature':25s}  {'Mean':>12s}  {'Std':>12s}")
for i, f in enumerate(FEATURES):
    print(f"  {f:25s}  {s.mean_[i]:12.4f}  {s.scale_[i]:12.4f}")

# ---------- 4. CONTROLLED FEATURE SWEEP ----------
print("\n" + "=" * 90)
print("  4. FEATURE SWEEP — Vary one feature, keep others at training mean")
print("=" * 90)

# Use training means (in scaled space, that's 0)
baseline = s.mean_.reshape(1, -1)

def predict_proba_row(scaled_row):
    proba = m.predict_proba(scaled_row)[0]
    pred_class = int(m.predict(scaled_row)[0])
    return le.inverse_transform([pred_class])[0], proba

# Sweep each key feature from its min to max
sweep_features = {
    'cpu_percent': [0, 10, 20, 30, 50, 70, 90, 100],
    'memory_percent': [30, 40, 50, 60, 70, 80, 90, 95],
    'disk_write_mbps': [0, 1, 5, 20, 50, 100, 150, 200],
    'memory_available_mb': [2000, 4000, 6000, 8000, 10000, 12000],
    'process_count': [150, 200, 250, 300, 350, 400]
}

for feat_name, values in sweep_features.items():
    idx = FEATURES.index(feat_name)
    print(f"\n  ── Sweeping {feat_name} ──")
    print(f"  {'Value':>10s}  {'→ Prediction':>15s}  {'Normal':>8s}  {'Moderate':>8s}  {'High':>8s}")
    for v in values:
        # Build raw feature row: training mean except the swept feature
        raw = s.mean_.copy()
        raw[idx] = v
        scaled = s.transform(raw.reshape(1, -1))
        pred, proba = predict_proba_row(scaled)
        print(f"  {v:>10.2f}  {pred:>15s}  {proba[le.transform(['Normal'])[0]]:8.4f}  "
              f"{proba[le.transform(['Moderate'])[0]]:8.4f}  "
              f"{proba[le.transform(['High'])[0]]:8.4f}")

# ---------- 5. LIVE-STYLE SIMULATIONS ----------
print("\n" + "=" * 90)
print("  5. LIVE-STYLE SCENARIOS — Real-world configurations")
print("=" * 90)

scenarios = [
    ("Idle (ThinkPad-style)",     {'cpu_percent': 3,  'memory_percent': 51, 'memory_available_mb': 6000, 'disk_write_mbps': 0.1, 'process_count': 220}),
    ("Idle (high-RAM machine)",   {'cpu_percent': 3,  'memory_percent': 51, 'memory_available_mb': 12000, 'disk_write_mbps': 0.1, 'process_count': 220}),
    ("Moderate workload",         {'cpu_percent': 25, 'memory_percent': 65, 'memory_available_mb': 4000, 'disk_write_mbps': 1.0, 'process_count': 260}),
    ("CPU stress only",           {'cpu_percent': 100,'memory_percent': 40, 'memory_available_mb': 7000, 'disk_write_mbps': 0.0, 'process_count': 220}),
    ("CPU + disk stress",         {'cpu_percent': 90, 'memory_percent': 55, 'memory_available_mb': 4000, 'disk_write_mbps': 150, 'process_count': 260}),
    ("CPU + memory + disk",       {'cpu_percent': 90, 'memory_percent': 85, 'memory_available_mb': 1000, 'disk_write_mbps': 150, 'process_count': 350}),
]

print(f"\n  {'Scenario':30s}  {'→ Prediction':>15s}  {'Normal':>8s}  {'Moderate':>8s}  {'High':>8s}")
for name, vals in scenarios:
    raw = s.mean_.copy()
    for k, v in vals.items():
        raw[FEATURES.index(k)] = v
    scaled = s.transform(raw.reshape(1, -1))
    pred, proba = predict_proba_row(scaled)
    print(f"  {name:30s}  {pred:>15s}  {proba[le.transform(['Normal'])[0]]:8.4f}  "
          f"{proba[le.transform(['Moderate'])[0]]:8.4f}  "
          f"{proba[le.transform(['High'])[0]]:8.4f}")

# ---------- 6. WHAT DOES TRAINING HIGH LOOK LIKE? ----------
print("\n" + "=" * 90)
print("  6. WHAT THE MODEL NEEDS FOR 'HIGH' — Training HIGH samples")
print("=" * 90)

high_df = df[df['label'] == 'High']
print(f"\n  High-class samples: {len(high_df)}")
print(f"\n  Distribution of disk_write_mbps in High class:")
print(f"    Mean: {high_df['disk_write_mbps'].mean():.1f}")
print(f"    Median: {high_df['disk_write_mbps'].median():.1f}")
print(f"    % samples with disk_write > 10 MB/s: {(high_df['disk_write_mbps'] > 10).mean()*100:.1f}%")
print(f"    % samples with disk_write > 50 MB/s: {(high_df['disk_write_mbps'] > 50).mean()*100:.1f}%")
print(f"    % samples with disk_write < 1 MB/s:  {(high_df['disk_write_mbps'] < 1).mean()*100:.1f}%")

print(f"\n  Distribution of cpu_percent in High class:")
print(f"    Mean: {high_df['cpu_percent'].mean():.1f}")
print(f"    % samples with cpu > 50%: {(high_df['cpu_percent'] > 50).mean()*100:.1f}%")

print("\n" + "=" * 90)
print("  DONE — Copy the output above for analysis")
print("=" * 90)