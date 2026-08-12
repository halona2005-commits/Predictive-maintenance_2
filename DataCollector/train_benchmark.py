"""
=========================================================
MODEL BENCHMARKING: Accuracy vs Latency
=========================================================
Compares 4 models on the balanced dataset.
Criteria: Highest Accuracy + Lowest Prediction Latency.
"""

import pandas as pd
import numpy as np
import time
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix

# --- Models ---
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier
from sklearn.neural_network import MLPClassifier

# =========================================================
# 1. LOAD DATA
# =========================================================
print("="*60)
print("  LOADING BALANCED DATASET")
print("="*60)

df = pd.read_csv("datasets/engineered_balanced_final.csv")
print(f"Total rows: {len(df)}")
print(f"Normal (0): {len(df[df['Label']==0])}")
print(f"High Load (1): {len(df[df['Label']==1])}")

# =========================================================
# 2. TRAIN/TEST SPLIT (Stratified to keep 50/50 in both)
# =========================================================
X = df.drop('Label', axis=1)
y = df['Label']

X_train, X_test, y_train, y_test = train_test_split(
    X, y, 
    test_size=0.2, 
    random_state=42, 
    stratify=y  # Ensures both train and test are 50/50
)

print(f"\nTrain set: {len(X_train)} rows (Normal: {sum(y_train==0)}, High: {sum(y_train==1)})")
print(f"Test set:  {len(X_test)} rows (Normal: {sum(y_test==0)}, High: {sum(y_test==1)})")

# =========================================================
# 3. SCALING (Needed for Logistic Regression & MLP)
# =========================================================
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# =========================================================
# 4. DEFINE MODELS TO BENCHMARK
# =========================================================
models = {
    "Logistic Regression": LogisticRegression(max_iter=1000, random_state=42),
    "Random Forest": RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1),
    "XGBoost": XGBClassifier(n_estimators=100, random_state=42, eval_metric='logloss', use_label_encoder=False),
    "Neural Network (MLP)": MLPClassifier(hidden_layer_sizes=(64, 32), max_iter=300, random_state=42, early_stopping=True)
}

results = []

print("\n" + "="*60)
print("  TRAINING & BENCHMARKING")
print("="*60)

# =========================================================
# 5. TRAIN, EVALUATE, AND MEASURE LATENCY
# =========================================================
for name, model in models.items():
    print(f"\n🔄 Training {name}...")
    
    # --- Training Time (just for info) ---
    start_train = time.perf_counter()
    model.fit(X_train_scaled, y_train)
    train_time = time.perf_counter() - start_train
    
    # --- Prediction Latency (MOST IMPORTANT) ---
    # We measure the time to predict the entire test set, then divide.
    start_infer = time.perf_counter()
    y_pred = model.predict(X_test_scaled)
    infer_time = time.perf_counter() - start_infer
    
    # Calculate per-sample latency (microseconds)
    latency_per_sample_us = (infer_time / len(X_test)) * 1_000_000
    
    # --- Metrics ---
    acc = accuracy_score(y_test, y_pred)
    prec = precision_score(y_test, y_pred)
    rec = recall_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred)
    
    # Store results
    results.append({
        "Model": name,
        "Accuracy": acc,
        "Precision": prec,
        "Recall": rec,
        "F1-Score": f1,
        "Train Time (s)": train_time,
        "Inference Latency (μs/sample)": latency_per_sample_us
    })
    
    print(f"   ✅ Accuracy: {acc:.4f} | Latency: {latency_per_sample_us:.2f} μs per sample")

# =========================================================
# 6. DISPLAY COMPARISON TABLE
# =========================================================
results_df = pd.DataFrame(results)

# Sort by Accuracy (highest first) and show Latency
results_df_sorted = results_df.sort_values(by="Accuracy", ascending=False)

print("\n" + "="*60)
print("  📊 FINAL COMPARISON (Sorted by Accuracy)")
print("="*60)
print(results_df_sorted[["Model", "Accuracy", "F1-Score", "Inference Latency (μs/sample)", "Train Time (s)"]].to_string(index=False))

# =========================================================
# 7. RECOMMENDATION LOGIC
# =========================================================
print("\n" + "="*60)
print("  🏆 RECOMMENDATION")
print("="*60)

# Find the best accuracy model
best_acc_model = results_df.loc[results_df['Accuracy'].idxmax()]
# Find the fastest model (lowest latency) among those with accuracy >= 95% of best accuracy
threshold_acc = best_acc_model['Accuracy'] * 0.95
candidates = results_df[results_df['Accuracy'] >= threshold_acc]
fastest_candidate = candidates.loc[candidates['Inference Latency (μs/sample)'].idxmin()]

print(f"🥇 Best Accuracy:  {best_acc_model['Model']} ({best_acc_model['Accuracy']:.4f})")
print(f"⚡ Fastest among top performers (within 5% of best accuracy): {fastest_candidate['Model']}")
print(f"   → Accuracy: {fastest_candidate['Accuracy']:.4f}")
print(f"   → Latency: {fastest_candidate['Inference Latency (μs/sample)']:.2f} μs per sample")

print("\n💡 Recommendation: Use **{}** for deployment!".format(fastest_candidate['Model']))
print("="*60)