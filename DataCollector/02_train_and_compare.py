import pandas as pd
import joblib
import time
import numpy as np
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

# ==========================================================
# 1. LOAD THE DATASET
# ==========================================================
print("📂 Loading the balanced training dataset...")
df = pd.read_csv("datasets/final_training_data_3class.csv")

# Drop process_id, keep features and label
X = df.drop(['label', 'process_id'], axis=1)
y = df['label']

# Encode string labels to numbers
le = LabelEncoder()
y_encoded = le.fit_transform(y)

# ==========================================================
# 2. 80/20 SPLIT & SCALING
# ==========================================================
X_train, X_test, y_train, y_test = train_test_split(
    X, y_encoded, test_size=0.2, random_state=42, stratify=y_encoded
)

scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# ==========================================================
# 3. MODELS (with fixed Logistic Regression)
# ==========================================================
models = {
    'Random Forest': RandomForestClassifier(n_estimators=100, random_state=42),
    'XGBoost': XGBClassifier(objective='multi:softprob', num_class=3, random_state=42),
    'MLP Neural Net': MLPClassifier(hidden_layer_sizes=(64,32), max_iter=500, random_state=42),
    'Logistic Regression': LogisticRegression(solver='lbfgs', max_iter=1000, random_state=42)
}

results = []
print("\n🔬 Training 4 models and evaluating both Training (80%) and Testing (20%) sets...\n")

# ==========================================================
# 4. TRAIN & EVALUATE
# ==========================================================
for name, model in models.items():
    start_train = time.perf_counter()
    model.fit(X_train_scaled, y_train)
    train_time = time.perf_counter() - start_train

    # --- Training metrics (80%) ---
    y_pred_train = model.predict(X_train_scaled)
    acc_train = accuracy_score(y_train, y_pred_train)
    prec_train = precision_score(y_train, y_pred_train, average='weighted')
    rec_train = recall_score(y_train, y_pred_train, average='weighted')
    f1_train = f1_score(y_train, y_pred_train, average='weighted')

    # --- Testing metrics (20%) + latency ---
    start_infer = time.perf_counter()
    y_pred_test = model.predict(X_test_scaled)
    infer_time = (time.perf_counter() - start_infer) / len(y_test) * 1_000_000

    acc_test = accuracy_score(y_test, y_pred_test)
    prec_test = precision_score(y_test, y_pred_test, average='weighted')
    rec_test = recall_score(y_test, y_pred_test, average='weighted')
    f1_test = f1_score(y_test, y_pred_test, average='weighted')

    results.append({
        'Model': name,
        'Train Acc': round(acc_train, 4),
        'Train F1': round(f1_train, 4),
        'Train Prec': round(prec_train, 4),
        'Train Recall': round(rec_train, 4),
        'Test Acc': round(acc_test, 4),
        'Test F1': round(f1_test, 4),
        'Test Prec': round(prec_test, 4),
        'Test Recall': round(rec_test, 4),
        'Latency (μs)': round(infer_time, 2),
        'Train Time (s)': round(train_time, 2)
    })

# ==========================================================
# 5. TERMINAL OUTPUT
# ==========================================================
print("=" * 125)
print(f"{'Model':<20} | {'Train Acc':<9} | {'Train F1':<9} | {'Train Prec':<9} | {'Train Rec':<9} | {'Test Acc':<9} | {'Test F1':<9} | {'Test Prec':<9} | {'Test Rec':<9} | {'Latency (μs)':<12}")
print("-" * 125)
for r in results:
    print(f"{r['Model']:<20} | {r['Train Acc']:<9.4f} | {r['Train F1']:<9.4f} | {r['Train Prec']:<9.4f} | {r['Train Recall']:<9.4f} | {r['Test Acc']:<9.4f} | {r['Test F1']:<9.4f} | {r['Test Prec']:<9.4f} | {r['Test Recall']:<9.4f} | {r['Latency (μs)']:<12.2f}")
print("=" * 125)

# ==========================================================
# 6. SAVE CSV
# ==========================================================
results_df = pd.DataFrame(results)
results_df.to_csv("model_comparison_results.csv", index=False)
print("\n✅ Comparison table saved as 'model_comparison_results.csv'")

# ==========================================================
# 7. DEPLOYMENT FILES
# ==========================================================
joblib.dump(models['XGBoost'], "xgboost_deployment_model.pkl")
joblib.dump(scaler, "scaler_deployment.pkl")
joblib.dump(le, "label_encoder.pkl")
print("✅ XGBoost, Scaler, and Label Encoder saved for deployment.")

# ==========================================================
# 8. GENERATE BOTH TRAINING AND TESTING GRAPHS
# ==========================================================
model_names = [r['Model'] for r in results]

# --- Training Graph ---
train_acc = [r['Train Acc'] for r in results]
latencies = [r['Latency (μs)'] for r in results]

x = np.arange(len(model_names))
width = 0.35

fig, ax1 = plt.subplots(figsize=(10, 6))
bars1 = ax1.bar(x - width/2, train_acc, width, label='Training Accuracy', color='#2b6cb0')
ax1.set_ylabel('Training Accuracy (0 to 1)', color='#2b6cb0')
ax1.tick_params(axis='y', labelcolor='#2b6cb0')
ax1.set_ylim(0.90, 1.03) # FIX: Creates space for the label
ax1.set_title('4-Model Comparison: Training Accuracy vs Inference Latency')

ax2 = ax1.twinx()
bars2 = ax2.bar(x + width/2, latencies, width, label='Latency (μs)', color='#f59e0b')
ax2.set_ylabel('Latency (μs)', color='#f59e0b')
ax2.tick_params(axis='y', labelcolor='#f59e0b')

ax1.set_xticks(x)
ax1.set_xticklabels(model_names)

# FIX: Offset text slightly upwards
for bar in bars1:
    h = bar.get_height()
    ax1.text(bar.get_x() + bar.get_width()/2., h + 0.003, f'{h:.4f}', ha='center', va='bottom', fontsize=9)

for bar in bars2:
    h = bar.get_height()
    ax2.text(bar.get_x() + bar.get_width()/2., h, f'{h:.1f} μs', ha='center', va='bottom', fontsize=9)

plt.tight_layout()
plt.savefig("model_comparison_train.png", dpi=300)
print("✅ Training graph saved as 'model_comparison_train.png'")

# --- Testing Graph ---
test_acc = [r['Test Acc'] for r in results]
fig, ax1 = plt.subplots(figsize=(10, 6))
bars1 = ax1.bar(x - width/2, test_acc, width, label='Testing Accuracy', color='#2b6cb0')
ax1.set_ylabel('Testing Accuracy (0 to 1)', color='#2b6cb0')
ax1.tick_params(axis='y', labelcolor='#2b6cb0')
ax1.set_ylim(0.90, 1.03) # FIX: Creates space for the label
ax1.set_title('4-Model Comparison: Testing Accuracy vs Inference Latency')

ax2 = ax1.twinx()
bars2 = ax2.bar(x + width/2, latencies, width, label='Latency (μs)', color='#f59e0b')
ax2.set_ylabel('Latency (μs)', color='#f59e0b')
ax2.tick_params(axis='y', labelcolor='#f59e0b')

ax1.set_xticks(x)
ax1.set_xticklabels(model_names)

# FIX: Offset text slightly upwards
for bar in bars1:
    h = bar.get_height()
    ax1.text(bar.get_x() + bar.get_width()/2., h + 0.003, f'{h:.4f}', ha='center', va='bottom', fontsize=9)

for bar in bars2:
    h = bar.get_height()
    ax2.text(bar.get_x() + bar.get_width()/2., h, f'{h:.1f} μs', ha='center', va='bottom', fontsize=9)

plt.tight_layout()
plt.savefig("model_comparison_test.png", dpi=300)
print("✅ Testing graph saved as 'model_comparison_test.png'")