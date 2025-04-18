import numpy as np
import pandas as pd
from scipy.signal import savgol_filter


df = pd.read_csv("final.csv") 


num_entries = len(df)
min_bpm = 60
max_bpm = 120

bpm_values = [np.random.randint(65, 75)]

for _ in range(num_entries - 1):
    delta = np.random.randint(-3, 4)  
    next_bpm = bpm_values[-1] + delta
    next_bpm = max(min_bpm, min(max_bpm, next_bpm))  
    bpm_values.append(next_bpm)


smooth_bpm = savgol_filter(bpm_values, window_length=51, polyorder=3)


df['mean_bpm'] = smooth_bpm


num_abrupt = int(0.05 * num_entries)
abrupt_indices = np.random.choice(num_entries, num_abrupt, replace=False)

for i in abrupt_indices:
    if np.random.rand() < 0.5:
        df.at[i, 'mean_bpm'] = np.random.randint(30, 40)  # Very low BPM
    else:
        df.at[i, 'mean_bpm'] = np.random.randint(181, 200)  # Very high BPM


df.to_csv("finalcopy copy.csv", index=False)
