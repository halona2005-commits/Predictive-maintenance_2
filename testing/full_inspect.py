import joblib
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.metrics import accuracy_score, classification_report

BACKEND = Path(r"D:\projects\Predictive-maintenance_2\backend\app")
TRAIN_CSV = Path(r"D:\projects\Predictive-maintenance_2\DataCollector\datasets\final_training_data_3class.csv")

FEATURES = ['cpu_percent', 'cpu_frequency_mhz', 'memory_percent', 'memory_available_mb',
            'disk_percent', 'disk_read_mbps', 'disk_write_mbps',
            'network_upload_mbps', 'network_download_mbps', 'process_count']

print("FULL PROJECT INSPECTION")
print("=" * 70)

df = pd.read_csv(TRAIN_CSV)
model = joblib.load(BACKEND / "xgboost_model.pkl")
scaler = joblib.load(BACKEND / "scaler.pkl")
le = joblib.load(BACKEND / "label_encoder.pkl")

print(f"\nRows: {len(df)}")
print(f"Classes: {list(le.classes_)}")

print("\nFEATURE IMPORTANCE:")
for i, imp in sorted(enumerate(model.feature_importances_), key=lambda x: -x[1]):
    print(f"  {FEATURES[i]:25s} {imp:.4f}")

print("\nCLASS DISTRIBUTIONS:")
for feat in ['cpu_percent', 'memory_percent', 'memory_available_mb', 'disk_write_mbps']:
    print(f"\n  {feat}:")
    for label in ['Normal', 'Moderate', 'High']:
        s = df[df['label'] == label][feat]
        print(f"    {label:10s} mean={s.mean():8.2f} std={s.std():8.2f} min={s.min():8.2f} max={s.max():8.2f}")

print("\nMODEL SELF-TEST:")
X = df[FEATURES]
y_pred = le.inverse_transform(model.predict(scaler.transform(X)))
print(f"  Accuracy on training data: {accuracy_score(df['label'], y_pred)*100:.2f}%")
print("\n" + classification_report(df['label'], y_pred, zero_division=0))

print("\nSEPARABILITY:")
for feat in ['cpu_percent', 'memory_percent', 'disk_write_mbps']:
    means = df.groupby('label')[feat].mean()
    spread = (means.max() - means.min()) / df[feat].std()
    print(f"  {feat:25s} spread={spread:.3f}")