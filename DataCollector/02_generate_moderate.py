import pandas as pd
import numpy as np

# 1. Load the cleaned combined data
data = pd.read_csv("datasets/combined_normal_high.csv")

# 2. Separate Normal and High data
normal = data[data['label'] == 0]
high = data[data['label'] == 1]

# 3. Define the number of Moderate samples we want
# We'll match the number of High samples (since High is the minority class)
# This gives a balanced 3‑class dataset (Normal: 8366, Moderate: 8366, High: 8366)
n_moderate = len(high)

print(f"Generating {n_moderate} Moderate samples...")

# 4. Randomly sample Normal and High pairs to create Moderate data
# We sample with replacement to ensure we get enough pairs
normal_sampled = normal.sample(n=n_moderate, replace=True)
high_sampled = high.sample(n=n_moderate, replace=True)

# 5. Average the features and add slight random noise
# Only average the numeric feature columns (drop the label column)
feature_cols = [col for col in data.columns if col != 'label']

moderate_features = (normal_sampled[feature_cols].values + high_sampled[feature_cols].values) / 2

# Add small Gaussian noise to make it realistic
noise = np.random.normal(0, 0.5, moderate_features.shape)  
moderate_features = moderate_features + noise

# 6. Create a DataFrame for Moderate class
moderate_df = pd.DataFrame(moderate_features, columns=feature_cols)
moderate_df['label'] = 2   # 2 = Moderate

# 7. Combine all three classes into one balanced dataset
# We'll downsample Normal to match the size of High and Moderate
normal_downsampled = normal.sample(n=n_moderate, replace=False)

final_df = pd.concat([normal_downsampled, moderate_df, high], ignore_index=True)

# 8. Shuffle the dataset
final_df = final_df.sample(frac=1, random_state=42).reset_index(drop=True)

# 9. Save the final balanced 3‑class dataset
output_file = "datasets/training_data_3class.csv"
final_df.to_csv(output_file, index=False)

print(f"\n✅ Step 2 complete! Balanced 3‑class data saved to: {output_file}")
print(f"Total rows: {len(final_df)}")
print(f"Normal: {len(final_df[final_df['label']==0])}")
print(f"Moderate: {len(final_df[final_df['label']==2])}")
print(f"High: {len(final_df[final_df['label']==1])}")