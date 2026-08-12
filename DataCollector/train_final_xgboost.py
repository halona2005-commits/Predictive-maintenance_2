"""
=========================================================
FINAL PRODUCTION MODEL: XGBoost
=========================================================
- Trains on entire balanced dataset
- Saves model (xgboost_model.pkl)
- Plots Feature Importance
- Demo prediction on a new sample
"""

import pandas as pd
import numpy as np
import joblib
import matplotlib.pyplot as plt
from xgboost import XGBClassifier
from sklearn.preprocessing import StandardScaler

# =========================================================
# 1. LOAD FULL BALANCED DATASET
# =========================================================
print("="*60)
print("  TRAINING FINAL XGBOOST MODEL")
print("="*60)

df = pd.read_csv("datasets/engineered_balanced_final.csv")
print(f"Total rows: {len(df)}")
print(f"Normal (0): {len(df[df['Label']==0])}")
print(f"High Load (1): {len(df[df['Label']==1])}")

X = df.drop('Label', axis=1)
y = df['Label']

# Feature names (for plotting later)
feature_names = X.columns.tolist()

# =========================================================
# 2. SCALE DATA (XGBoost doesn't require scaling, but it's good practice)
# =========================================================
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# =========================================================
# 3. TRAIN XGBOOST ON 100% OF THE DATA
# =========================================================
print("\nTraining XGBoost on full dataset...")

model = XGBClassifier(
    n_estimators=100,
    random_state=42,
    eval_metric='logloss',
    use_label_encoder=False,
    verbosity=0
)

model.fit(X_scaled, y)

print("✅ Model trained successfully!")

# =========================================================
# 4. SAVE MODEL AND SCALER
# =========================================================
joblib.dump(model, "xgboost_model.pkl")
joblib.dump(scaler, "scaler.pkl")
print("✅ Saved: xgboost_model.pkl")
print("✅ Saved: scaler.pkl")

# =========================================================
# 5. FEATURE IMPORTANCE PLOT (CRITICAL FOR VIVA)
# =========================================================
print("\nGenerating Feature Importance Plot...")

importance = model.feature_importances_
importance_df = pd.DataFrame({
    'Feature': feature_names,
    'Importance': importance
}).sort_values('Importance', ascending=False)

# Plot
plt.figure(figsize=(10, 6))
plt.barh(importance_df['Feature'], importance_df['Importance'], color='royalblue')
plt.xlabel('Importance Score')
plt.title('XGBoost Feature Importance\n(Which Z-scores matter most?)')
plt.gca().invert_yaxis()  # Highest at top
plt.tight_layout()
plt.savefig('feature_importance.png', dpi=300, bbox_inches='tight')
print("✅ Saved: feature_importance.png")

# Print top features
print("\n📊 Top 5 Most Important Features:")
for i, row in importance_df.head(5).iterrows():
    print(f"   {i+1}. {row['Feature']}: {row['Importance']:.4f}")

# =========================================================
# 6. DEMO: Predict a New Sample
# =========================================================
print("\n" + "="*60)
print("  DEMO: Predicting a New Sample")
print("="*60)

# Take the first row of the dataset as a "new" sample
sample = X.iloc[0].values.reshape(1, -1)
true_label = y.iloc[0]

# Scale it
sample_scaled = scaler.transform(sample)

# Predict
pred_proba = model.predict_proba(sample_scaled)[0]
pred_class = model.predict(sample_scaled)[0]

print(f"Sample features (first 5): {X.iloc[0].head().to_dict()}")
print(f"True Label: {'High Load' if true_label == 1 else 'Normal'}")
print(f"Predicted: {'High Load' if pred_class == 1 else 'Normal'}")
print(f"Confidence: Normal={pred_proba[0]:.2%}, High Load={pred_proba[1]:.2%}")

print("\n" + "="*60)
print("  ✅ FINAL MODEL READY FOR DEPLOYMENT!")
print("="*60)
print("\n📁 Files saved:")
print("   ✅ xgboost_model.pkl (the trained model)")
print("   ✅ scaler.pkl (scaler to preprocess new data)")
print("   ✅ feature_importance.png (Viva-ready chart)")
print("\n💡 To predict a new sample, load the model and scaler:")
print("   model = joblib.load('xgboost_model.pkl')")
print("   scaler = joblib.load('scaler.pkl')")
print("   sample_scaled = scaler.transform(your_new_data)")
print("   pred = model.predict(sample_scaled)")
print("="*60)