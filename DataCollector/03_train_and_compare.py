import pandas as pd
import joblib
import time
import numpy as np
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score

# 1. Load your perfectly balanced dataset
print("📂 Loading dataset...")
df = pd.read_csv("datasets/training_data_3class.csv")
X = df.drop('label', axis=1)
y = df['label']  # 0=Normal, 1=High, 2=Moderate

# 2. Train/Test Split and Scale
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# 3. Define the models we want to compare
models = {
    'XGBoost': XGBClassifier(objective='multi:softprob', num_class=3, random_state=42),
    'Random Forest': RandomForestClassifier(n_estimators=100, random_state=42),
    'MLP Neural Net': MLPClassifier(hidden_layer_sizes=(64,32), max_iter=500, random_state=42),
    'Logistic Regression': LogisticRegression(solver='lbfgs', max_iter=1000, random_state=42)  # <-- Fixed
}

results = []

print("\n🔬 Training and evaluating all models...\n")

# 4. Train, Predict, and Measure Latency for each model
for name, model in models.items():
    # Train
    start_train = time.perf_counter()
    model.fit(X_train_scaled, y_train)
    train_time = time.perf_counter() - start_train

    # Predict and measure inference time
    start_infer = time.perf_counter()
    y_pred = model.predict(X_test_scaled)
    infer_time = (time.perf_counter() - start_infer) / len(y_test) * 1_000_000  # microseconds

    # Calculate Metrics
    acc = accuracy_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred, average='weighted')

    results.append({
        'Model': name,
        'Accuracy': acc,
        'F1': f1,
        'Latency_us': infer_time,
        'Train_Time': train_time,
        'ModelObj': model
    })

# ========================================================
# 5. PRINT THE COMPARISON TABLE TO TERMINAL
# ========================================================
print("=" * 85)
print(f"{'Model':<20} | {'Accuracy':<10} | {'F1-Score':<10} | {'Latency (μs)':<15} | {'Train Time (s)':<15}")
print("-" * 85)
for res in results:
    print(f"{res['Model']:<20} | {res['Accuracy']:.4f}     | {res['F1']:.4f}     | {res['Latency_us']:<15.2f} | {res['Train_Time']:<15.2f}")
print("=" * 85)

# 6. Pick the winner (Best F1-Score)
best_model_info = max(results, key=lambda x: x['F1'])
print(f"\n🏆 Best model: **{best_model_info['Model']}** with F1 = {best_model_info['F1']:.4f}")

# 7. Save the best model and scaler for deployment
joblib.dump(best_model_info['ModelObj'], "best_model.pkl")
joblib.dump(scaler, "scaler.pkl")
print("✅ Saved best model as 'best_model.pkl' and scaler as 'scaler.pkl'")

# ========================================================
# 8. GENERATE THE COMPARISON GRAPH (FIXED Y-AXIS LIMITS)
# ========================================================
print("\n📊 Generating comparison graph...")

model_names = [res['Model'] for res in results]
accuracies = [res['Accuracy'] for res in results]
latencies = [res['Latency_us'] for res in results]

# Normalize latency for the dual-axis graph
max_lat = max(latencies)
# Add a tiny baseline (0.05) so extremely small bars are visible
min_bar_height = 0.05
norm_lat = [max(l / max_lat, min_bar_height) for l in latencies]

x = np.arange(len(model_names))
width = 0.35

fig, ax1 = plt.subplots(figsize=(12, 6))

# Accuracy Bars (Left Axis)
bars1 = ax1.bar(x - width/2, accuracies, width, label='Accuracy', color='#2b6cb0')
ax1.set_ylabel('Accuracy (0 to 1)', color='#2b6cb0')
ax1.tick_params(axis='y', labelcolor='#2b6cb0')

# ---- CRITICAL FIX ----
# Change the Y-axis limits to show Logistic Regression (0.8367)
ax1.set_ylim(0.75, 1.01)
# ---------------------

ax1.set_title('3-Class Model Comparison: Accuracy vs Inference Latency', fontsize=14)

# Latency Bars (Right Axis)
ax2 = ax1.twinx()
bars2 = ax2.bar(x + width/2, norm_lat, width, label='Latency (Normalized)', color='#f59e0b')
ax2.set_ylabel(f'Inference Latency (Normalized; Max = {max_lat:.1f} μs)', color='#f59e0b')
ax2.tick_params(axis='y', labelcolor='#f59e0b')
ax2.set_ylim(0, 1.2)

ax1.set_xticks(x)
ax1.set_xticklabels(model_names)

# Add value labels on top of the bars
for bar in bars1:
    h = bar.get_height()
    ax1.text(bar.get_x() + bar.get_width()/2., h, f'{h:.4f}', ha='center', va='bottom', fontsize=9)

for bar in bars2:
    h = bar.get_height()
    # Only display the real latency label (don't show the fake baseline)
    real_val = h * max_lat
    # Don't label the 0.05 baseline
    if h > 0.06: 
        ax2.text(bar.get_x() + bar.get_width()/2., h, f'{real_val:.1f} μs', ha='center', va='bottom', fontsize=9)

# Adjust layout to prevent clipping
fig.tight_layout()
plt.savefig("model_comparison_final.png", dpi=300)
plt.close()
print("✅ Graph saved as 'model_comparison_final.png'")