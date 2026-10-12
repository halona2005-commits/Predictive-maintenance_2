import joblib
import pandas as pd
from pathlib import Path

BACKEND = Path(r"D:\projects\Predictive-maintenance_2\backend\app")

model = joblib.load(BACKEND / "xgboost_model.pkl")
scaler = joblib.load(BACKEND / "scaler.pkl")
le = joblib.load(BACKEND / "label_encoder.pkl")

print("Scaler mean:", scaler.mean_.round(2))
print("Scaler std: ", scaler.scale_.round(2))
print()

tests = [
    (13.3, 59.0, 0.11, "LIVE current"),
    (5.0, 55.0, 0.34, "Training Normal"),
    (42.0, 75.0, 0.18, "Training Moderate"),
    (71.7, 86.9, 120.8, "Training High"),
]

for cpu, mem, disk, label in tests:
    X = pd.DataFrame([[cpu, mem, disk]],
                     columns=['cpu_percent', 'memory_percent', 'disk_write_mbps'])
    X_scaled = scaler.transform(X)
    pred = model.predict(X_scaled)[0]
    proba = model.predict_proba(X_scaled)[0]
    pred_label = le.inverse_transform([pred])[0]
    print(f"{label}: CPU={cpu}, Mem={mem}, Disk={disk}")
    print(f"  Scaled: {X_scaled[0].round(3)}")
    print(f"  Predicted: {pred_label}")
    print(f"  N={proba[2]:.4f} M={proba[1]:.4f} H={proba[0]:.4f}")
    print()