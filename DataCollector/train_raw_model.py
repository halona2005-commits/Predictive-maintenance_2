import pandas as pd
import joblib
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from xgboost import XGBClassifier

# 1. Load the UN-ENGINEERED dataset
df = pd.read_csv("datasets/training_balanced_supervised.csv")

print("✅ Training on columns:")
print(df.columns.tolist())
print("-" * 50)

# 2. Define the 5 RAW features (Exact match from your CSV output)
features = [
    'cpu_percent', 
    'memory_percent', 
    'disk_write_mbps', 
    'process_count', 
    'ssd_percentage_used'
]

# 3. Check if columns exist
missing = [f for f in features if f not in df.columns]
if missing:
    print(f"\n❌ ERROR: These columns were not found: {missing}")
    exit()

X = df[features]

# 4. Fix: The target column is 'Label' (Capital L), not 'label'
# It represents anomalies (0 or 1)
y = df['Label']  

# 5. Train/Test Split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# 6. Scale and Fit
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)

# 7. Train XGBoost
model = XGBClassifier(n_estimators=100, learning_rate=0.1, random_state=42)
model.fit(X_train_scaled, y_train)

# 8. Save the new model files
joblib.dump(model, "xgboost_model_raw.pkl")
joblib.dump(scaler, "scaler_raw.pkl")

print("\n✅ True AI Model (5 Features) trained successfully!")
print(f"Validation Accuracy: {model.score(scaler.transform(X_test), y_test) * 100:.2f}%")