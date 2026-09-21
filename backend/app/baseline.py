# backend/app/baseline.py
"""
Baseline computation and post-processing for per-machine adaptation.
- Computed ONCE after 1 hour of data
- Stored in baseline.json
- Used to post-process XGBoost predictions
- Never recomputed (frozen baseline)
"""

import json
import os
from statistics import mean, stdev
import socket

BASELINE_FILE = f"baseline_{socket.gethostname()}.json"
MIN_SAMPLES = 3200          # 1.5 hours at 1 Hz
SIGMA_THRESHOLD = 2.0       # 2 standard deviations
CPU_SAFETY_FLOOR = 95.0     # force HIGH if CPU > 95%


FEATURES = [
    'cpu_percent', 'cpu_frequency_mhz', 'memory_percent', 'memory_available_mb',
    'disk_percent', 'disk_read_mbps', 'disk_write_mbps',
    'network_upload_mbps', 'network_download_mbps', 'process_count'
]


def compute_baseline(db_session, min_samples=MIN_SAMPLES):
    """
    Compute baseline stats ONCE after enough data is collected.
    Returns None if not enough data yet OR if baseline already exists.
    """
    from app.models import Metric

    # If baseline already exists → never recompute
    if os.path.exists(BASELINE_FILE):
        return None

    metrics = db_session.query(Metric).order_by(Metric.id.desc()).limit(min_samples).all()
    if len(metrics) < min_samples:
        return None  # not enough data yet

    baseline = {}
    for feature in FEATURES:
        values = [getattr(m, feature) for m in metrics if getattr(m, feature) is not None]
        if not values:
            continue
        baseline[feature] = {
            "mean": float(mean(values)),
            "std": float(stdev(values)) if len(values) > 1 else 1.0
        }

    # Ensure std is never zero (avoid divide-by-zero later)
    for feature, stats in baseline.items():
        if stats["std"] <= 0:
            stats["std"] = 1.0

    with open(BASELINE_FILE, 'w') as f:
        json.dump(baseline, f, indent=2)

    print(f"✅ Baseline computed for {len(baseline)} features and frozen")
    return baseline


def load_baseline():
    """Load baseline from disk. Returns None if not yet learned."""
    if not os.path.exists(BASELINE_FILE):
        return None
    try:
        with open(BASELINE_FILE) as f:
            return json.load(f)
    except Exception:
        return None


def is_within_baseline(features, baseline, sigma=SIGMA_THRESHOLD):
    """Check if all features are within ±sigma of baseline."""
    if baseline is None:
        return False

    for feature, stats in baseline.items():
        value = features.get(feature)
        if value is None:
            continue
        deviation = abs(value - stats["mean"]) / stats["std"]
        if deviation > sigma:
            return False
    return True


def adjust_prediction(xgb_level, features, baseline):
    """
    Post-process the XGBoost prediction.

    Rules:
    1. If CPU > 95% → force HIGH (safety floor, overrides baseline)
    2. If baseline not ready → return "CALIBRATING"
    3. If XGBoost says HIGH → keep HIGH
    4. If XGBoost says MODERATE and features within baseline → downgrade to NORMAL
    5. Otherwise → keep XGBoost's prediction
    """
    # Safety floor — CPU overrides everything
    cpu = features.get('cpu_percent', 0)
    if cpu and cpu > CPU_SAFETY_FLOOR:
        return "HIGH"

    # Not learned yet
    if baseline is None:
        return "CALIBRATING"

    # HIGH is never downgraded
    if xgb_level == "HIGH":
        return "HIGH"

    # MODERATE + within baseline → NORMAL
    if xgb_level == "MODERATE" and is_within_baseline(features, baseline):
        return "NORMAL"

    return xgb_level