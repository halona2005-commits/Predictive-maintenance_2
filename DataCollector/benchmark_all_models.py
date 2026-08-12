"""
=========================================================
ULTIMATE MODEL BENCHMARK: 8 Models + Auto-Save Results
=========================================================
Saves:
  1. model_comparison_results.csv (raw numbers)
  2. model_comparison_plot.png (visual comparison)
"""

import pandas as pd
import numpy as np
import time
import warnings
import matplotlib.pyplot as plt
warnings.filterwarnings('ignore')

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

# --- Supervised ---
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier
from sklearn.neural_network import MLPClassifier

# --- Unsupervised ---
from sklearn.ensemble import IsolationForest
from sklearn.svm import OneClassSVM

# --- Deep Learning ---
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, RepeatVector, TimeDistributed
from tensorflow.keras.callbacks import EarlyStopping

# =========================================================
# 1. LOAD DATA
# =========================================================
print("="*70)
print("  LOADING BALANCED DATASET")
print("="*70)

df = pd.read_csv("datasets/engineered_balanced_final.csv")
print(f"Total rows: {len(df)} | Normal: {len(df[df['Label']==0])} | High: {len(df[df['Label']==1])}")

X = df.drop('Label', axis=1)
y = df['Label']

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# =========================================================
# 2. HELPER: Threshold tuning for unsupervised models
# =========================================================
def find_best_threshold(scores_train, y_train, scores_test, y_test):
    best_f1 = 0
    best_thresh = 0.0
    for thresh in np.linspace(scores_train.min(), scores_train.max(), 100):
        preds = (scores_train > thresh).astype(int)
        f1 = f1_score(y_train, preds)
        if f1 > best_f1:
            best_f1 = f1
            best_thresh = thresh
    preds_test = (scores_test > best_thresh).astype(int)
    return preds_test

# =========================================================
# 3. HELPER: LSTM Sequences
# =========================================================
SEQ_LEN = 10
def create_sequences(data, seq_len=SEQ_LEN):
    X_seq = []
    for i in range(len(data) - seq_len):
        X_seq.append(data[i:i+seq_len])
    return np.array(X_seq)

normal_train = X_train_scaled[y_train == 0]
normal_train_seq = create_sequences(normal_train)
X_test_seq = create_sequences(X_test_scaled)
y_test_seq = y_test.iloc[SEQ_LEN:].values

# =========================================================
# 4. RESULTS STORAGE
# =========================================================
results = []

# =========================================================
# 5. TRAIN SUPERVISED MODELS
# =========================================================
print("\n" + "="*70)
print("  [1/8] Training Supervised Models...")
print("="*70)

supervised_models = {
    "Logistic Regression": LogisticRegression(max_iter=1000, random_state=42),
    "Random Forest": RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1),
    "XGBoost": XGBClassifier(n_estimators=100, random_state=42, eval_metric='logloss', use_label_encoder=False, verbosity=0),
    "MLP Neural Network": MLPClassifier(hidden_layer_sizes=(64, 32), max_iter=300, random_state=42, early_stopping=True)
}

for name, model in supervised_models.items():
    print(f"   Training {name}...", end=" ", flush=True)
    start_train = time.perf_counter()
    model.fit(X_train_scaled, y_train)
    train_time = time.perf_counter() - start_train
    
    start_infer = time.perf_counter()
    y_pred = model.predict(X_test_scaled)
    infer_time = time.perf_counter() - start_infer
    latency_us = (infer_time / len(X_test)) * 1_000_000
    
    results.append({
        "Model": name, "Type": "Supervised",
        "Accuracy": accuracy_score(y_test, y_pred),
        "Precision": precision_score(y_test, y_pred),
        "Recall": recall_score(y_test, y_pred),
        "F1": f1_score(y_test, y_pred),
        "Latency (μs)": latency_us,
        "Train Time (s)": train_time
    })
    print(f"✅ Acc: {results[-1]['Accuracy']:.4f}")

# =========================================================
# 6. TRAIN UNSUPERVISED MODELS
# =========================================================
print("\n" + "="*70)
print("  [2/8] Training Unsupervised Models...")
print("="*70)

# --- Isolation Forest ---
print("   Training Isolation Forest...", end=" ", flush=True)
iso = IsolationForest(contamination=0.5, random_state=42, n_jobs=-1)
start_train = time.perf_counter()
iso.fit(X_train_scaled)
train_time = time.perf_counter() - start_train

start_infer = time.perf_counter()
scores_train = -iso.decision_function(X_train_scaled)
scores_test = -iso.decision_function(X_test_scaled)
infer_time = time.perf_counter() - start_infer
y_pred = find_best_threshold(scores_train, y_train, scores_test, y_test)

results.append({
    "Model": "Isolation Forest", "Type": "Unsupervised",
    "Accuracy": accuracy_score(y_test, y_pred),
    "Precision": precision_score(y_test, y_pred),
    "Recall": recall_score(y_test, y_pred),
    "F1": f1_score(y_test, y_pred),
    "Latency (μs)": (infer_time / len(X_test)) * 1_000_000,
    "Train Time (s)": train_time
})
print(f"✅ Acc: {results[-1]['Accuracy']:.4f}")

# --- Compressed IF (PCA+IF) ---
print("   Training Compressed IF (PCA+IF)...", end=" ", flush=True)
pca = PCA(n_components=0.95)
X_train_pca = pca.fit_transform(X_train_scaled)
X_test_pca = pca.transform(X_test_scaled)
comp_if = IsolationForest(contamination=0.5, random_state=42, n_jobs=-1)
start_train = time.perf_counter()
comp_if.fit(X_train_pca)
train_time = time.perf_counter() - start_train

start_infer = time.perf_counter()
scores_train = -comp_if.decision_function(X_train_pca)
scores_test = -comp_if.decision_function(X_test_pca)
infer_time = time.perf_counter() - start_infer
y_pred = find_best_threshold(scores_train, y_train, scores_test, y_test)

results.append({
    "Model": "Compressed IF (PCA+IF)", "Type": "Unsupervised",
    "Accuracy": accuracy_score(y_test, y_pred),
    "Precision": precision_score(y_test, y_pred),
    "Recall": recall_score(y_test, y_pred),
    "F1": f1_score(y_test, y_pred),
    "Latency (μs)": (infer_time / len(X_test)) * 1_000_000,
    "Train Time (s)": train_time
})
print(f"✅ Acc: {results[-1]['Accuracy']:.4f}")

# --- One-Class SVM ---
print("   Training One-Class SVM...", end=" ", flush=True)
ocsvm = OneClassSVM(nu=0.5, kernel='rbf', gamma='scale')
start_train = time.perf_counter()
ocsvm.fit(X_train_scaled)
train_time = time.perf_counter() - start_train

start_infer = time.perf_counter()
scores_train = -ocsvm.decision_function(X_train_scaled)
scores_test = -ocsvm.decision_function(X_test_scaled)
infer_time = time.perf_counter() - start_infer
y_pred = find_best_threshold(scores_train, y_train, scores_test, y_test)

results.append({
    "Model": "One-Class SVM", "Type": "Unsupervised",
    "Accuracy": accuracy_score(y_test, y_pred),
    "Precision": precision_score(y_test, y_pred),
    "Recall": recall_score(y_test, y_pred),
    "F1": f1_score(y_test, y_pred),
    "Latency (μs)": (infer_time / len(X_test)) * 1_000_000,
    "Train Time (s)": train_time
})
print(f"✅ Acc: {results[-1]['Accuracy']:.4f}")

# --- LSTM Autoencoder ---
print("\n" + "="*70)
print("  [3/8] Training LSTM Autoencoder (takes ~1 min)...")
print("="*70)
print("   Training LSTM AE...", end=" ", flush=True)

n_features = X_train_scaled.shape[1]
lstm_model = Sequential([
    LSTM(32, activation='relu', input_shape=(SEQ_LEN, n_features)),
    RepeatVector(SEQ_LEN),
    LSTM(32, activation='relu', return_sequences=True),
    TimeDistributed(Dense(n_features))
])
lstm_model.compile(optimizer='adam', loss='mse')
early_stop = EarlyStopping(monitor='loss', patience=5, restore_best_weights=True)

start_train = time.perf_counter()
lstm_model.fit(normal_train_seq, normal_train_seq, epochs=30, batch_size=64, callbacks=[early_stop], verbose=0)
train_time = time.perf_counter() - start_train

start_infer = time.perf_counter()
reconstructed = lstm_model.predict(X_test_seq, verbose=0)
infer_time = time.perf_counter() - start_infer

mse_test = np.mean(np.square(X_test_seq - reconstructed), axis=(1, 2))
normal_recon = lstm_model.predict(normal_train_seq, verbose=0)
mse_normal = np.mean(np.square(normal_train_seq - normal_recon), axis=(1, 2))
threshold = np.mean(mse_normal) + 3 * np.std(mse_normal)

y_pred = (mse_test > threshold).astype(int)
latency_us = (infer_time / len(X_test_seq)) * 1_000_000

results.append({
    "Model": "LSTM Autoencoder", "Type": "Unsupervised (DL)",
    "Accuracy": accuracy_score(y_test_seq, y_pred),
    "Precision": precision_score(y_test_seq, y_pred, zero_division=0),
    "Recall": recall_score(y_test_seq, y_pred, zero_division=0),
    "F1": f1_score(y_test_seq, y_pred, zero_division=0),
    "Latency (μs)": latency_us,
    "Train Time (s)": train_time
})
print(f"✅ Acc: {results[-1]['Accuracy']:.4f}")

# =========================================================
# 7. SAVE RESULTS AS CSV TABLE
# =========================================================
results_df = pd.DataFrame(results)
results_df = results_df.sort_values('Accuracy', ascending=False)

# Save to CSV for your report
results_df.to_csv("model_comparison_results.csv", index=False)
print("\n✅ Saved: model_comparison_results.csv")

# =========================================================
# 8. PLOT COMPARISON (Accuracy vs Latency)
# =========================================================
fig, ax1 = plt.subplots(figsize=(12, 6))

# Bar plot for Accuracy
x = np.arange(len(results_df))
width = 0.35

bars1 = ax1.bar(x - width/2, results_df['Accuracy'], width, label='Accuracy', color='royalblue')
ax1.set_xlabel('Model')
ax1.set_ylabel('Accuracy', color='royalblue')
ax1.tick_params(axis='y', labelcolor='royalblue')
ax1.set_xticks(x)
ax1.set_xticklabels(results_df['Model'], rotation=45, ha='right')
ax1.set_ylim(0.9, 1.0)

# Secondary y-axis for Latency (log scale to see differences)
ax2 = ax1.twinx()
bars2 = ax2.bar(x + width/2, results_df['Latency (μs)'], width, label='Latency (μs)', color='coral', alpha=0.7)
ax2.set_ylabel('Latency (μs per sample)', color='coral')
ax2.tick_params(axis='y', labelcolor='coral')
ax2.set_yscale('log')

# Add value labels on bars
for bar in bars1:
    height = bar.get_height()
    ax1.annotate(f'{height:.4f}', xy=(bar.get_x() + bar.get_width()/2, height),
                xytext=(0, 3), textcoords="offset points", ha='center', va='bottom', fontsize=8)

for bar in bars2:
    height = bar.get_height()
    ax2.annotate(f'{height:.2f}', xy=(bar.get_x() + bar.get_width()/2, height),
                xytext=(0, 3), textcoords="offset points", ha='center', va='bottom', fontsize=8)

plt.title('Model Comparison: Accuracy vs Inference Latency\n(Log scale for Latency)', fontsize=14)
fig.tight_layout()
plt.grid(axis='y', linestyle='--', alpha=0.3)
plt.savefig('model_comparison_plot.png', dpi=300, bbox_inches='tight')
print("✅ Saved: model_comparison_plot.png")

# =========================================================
# 9. TERMINAL OUTPUT (Formatted Table)
# =========================================================
print("\n" + "="*70)
print("  📊 FINAL COMPARISON (All 8 Models)")
print("="*70)
print(results_df[['Model', 'Type', 'Accuracy', 'F1', 'Latency (μs)', 'Train Time (s)']].to_string(index=False, float_format=lambda x: f"{x:.4f}"))

# =========================================================
# 10. RECOMMENDATION
# =========================================================
best_acc = results_df.loc[results_df['Accuracy'].idxmax()]
fastest = results_df.loc[results_df['Latency (μs)'].idxmin()]
threshold_acc = best_acc['Accuracy'] * 0.95
candidates = results_df[results_df['Accuracy'] >= threshold_acc]
fastest_good = candidates.loc[candidates['Latency (μs)'].idxmin()]

print("\n" + "="*70)
print("  🏆 RECOMMENDATION (For Deployment)")
print("="*70)
print(f"🥇 Best Accuracy:  {best_acc['Model']} ({best_acc['Accuracy']:.4f})")
print(f"⚡ Fastest Overall: {fastest['Model']} ({fastest['Latency (μs)']:.2f} μs)")
print(f"\n💡 **Final Choice**: **{fastest_good['Model']}**")
print(f"   → Accuracy: {fastest_good['Accuracy']:.4f}")
print(f"   → Latency: {fastest_good['Latency (μs)']:.2f} μs per sample")
print(f"   → Type: {fastest_good['Type']}")
print("\n📁 Files saved for Viva:")
print("   ✅ model_comparison_results.csv (table for your report)")
print("   ✅ model_comparison_plot.png (visual comparison chart)")
print("="*70)