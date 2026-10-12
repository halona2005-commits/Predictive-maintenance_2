"""
Pre-Run Inspection — verifies model, main.py, and file integrity.
"""
import joblib
import re
from pathlib import Path

BACKEND = Path(r"D:\projects\Predictive-maintenance_2\backend\app")
MODEL = BACKEND / "xgboost_model.pkl"
SCALER = BACKEND / "scaler.pkl"
LE = BACKEND / "label_encoder.pkl"
MAIN = BACKEND / "main.py"

print("=" * 80)
print("  PRE-RUN INSPECTION")
print("=" * 80)

# 1. Model files
print("\n[1] MODEL FILES")
print("-" * 80)
for f in [MODEL, SCALER, LE]:
    if f.exists():
        print(f"  OK  {f.name:30s}  {f.stat().st_size:8d} bytes")
    else:
        print(f"  MISSING  {f.name}")

# 2. Load and inspect model
print("\n[2] MODEL INTERNALS")
print("-" * 80)
try:
    model = joblib.load(MODEL)
    scaler = joblib.load(SCALER)
    le = joblib.load(LE)
    print(f"  Model type:     {type(model).__name__}")
    print(f"  Features:       {model.n_features_in_}")
    print(f"  Classes:        {list(le.classes_)}")
    print(f"  Scaler mean:    {list(scaler.mean_.round(2))}")
    print(f"  Scaler std:     {list(scaler.scale_.round(2))}")
except Exception as e:
    print(f"  ERROR loading model: {e}")
    exit(1)

# 3. Check main.py features
print("\n[3] main.py FEATURE LIST")
print("-" * 80)
main_text = MAIN.read_text(encoding='utf-8', errors='ignore')

# Find feature list block
feature_block = re.search(
    r"inputs = pd\.DataFrame\(\[\[(.*?)\]\]",
    main_text, re.DOTALL
)
if feature_block:
    features_used = re.findall(r"latest_metric\.(\w+)", feature_block.group(1))
    print(f"  Features in inputs: {features_used}")
    print(f"  Count: {len(features_used)}")
else:
    print("  Could not find inputs DataFrame block")

# Find columns
col_block = re.search(
    r"columns=\[(.*?)\]",
    main_text, re.DOTALL
)
if col_block:
    cols = re.findall(r"['\"](\w+)['\"]", col_block.group(1))
    print(f"  Columns list:       {cols}")
    print(f"  Count: {len(cols)}")

# 4. Check if OLD features still present
print("\n[4] LEFTOVER OLD FEATURES")
print("-" * 80)
old_features = ['cpu_frequency_mhz', 'memory_available_mb', 'disk_percent',
                'disk_read_mbps', 'network_upload_mbps', 'network_download_mbps',
                'process_count']

found_old = []
for feat in old_features:
    # Look for `latest_metric.<feat>` inside inputs block
    if feature_block and f"latest_metric.{feat}" in feature_block.group(1):
        found_old.append(feat)

if found_old:
    print(f"  WARNING: Old features still in input block: {found_old}")
    print(f"  → main.py needs editing")
else:
    print(f"  OK  No old features in input block")

# 5. Compare with model expectation
print("\n[5] COMPATIBILITY CHECK")
print("-" * 80)
if feature_block:
    input_count = len(features_used)
    model_count = model.n_features_in_
    if input_count == model_count:
        print(f"  OK  Input features ({input_count}) == Model expects ({model_count})")
    else:
        print(f"  ERROR: Input features ({input_count}) != Model expects ({model_count})")

print("\n" + "=" * 80)
print("  INSPECTION COMPLETE")
print("=" * 80)