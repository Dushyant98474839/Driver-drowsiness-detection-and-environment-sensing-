import pandas as pd
import numpy as np

# Load original data
df = pd.read_csv('final.csv')
df = df.iloc[10:].reset_index(drop=True)

# Bootstrap: sample with replacement
n_synthetic = 2507
bootstrap_indices = np.random.choice(len(df), size=n_synthetic, replace=True)
synthetic_df = df.iloc[bootstrap_indices].copy().reset_index(drop=True)

# Add small perturbations
for col in synthetic_df.columns:
    if col not in ['timestamp', 'anomaly', 'sample_count']:
        noise = np.random.normal(0, 0.01 * synthetic_df[col].std(), n_synthetic)
        synthetic_df[col] = synthetic_df[col] + noise
        synthetic_df[col] = synthetic_df[col].clip(df[col].min(), df[col].max())

# Update timestamps
synthetic_df['timestamp'] = [pd.to_datetime('2025-04-17 12:45:00') + pd.Timedelta(seconds=3*i)
                            for i in range(n_synthetic)]

synthetic_df.to_csv('synthetic_sensor_data.csv', index=False, float_format='%.6f')