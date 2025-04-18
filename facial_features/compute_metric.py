import pandas as pd
import numpy as np

np.random.seed(42)

def calculate_metrics(file_path):
    data = pd.read_csv(file_path)
    TP = data['True_Positive'].sum()
    TN = data['True_Negative'].sum()
    FP = data['False_Positive'].sum()
    FN = data['False_Negative'].sum()

    precision = TP / (TP + FP) if (TP + FP) > 0 else 0
    recall = TP / (TP + FN) if (TP + FN) > 0 else 0
    f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0

    print(f"File: {file_path}")
    print(f"TP: {TP}, TN: {TN}, FP: {FP}, FN: {FN}")
    print(f"Precision: {precision:.4f}, Recall: {recall:.4f}, F1 Score: {f1_score:.4f}\n")

print("Drowsiness Detection Data saved to drowsiness_data.csv")
print("Yawn Detection Data saved to yawn_data.csv")
print("Red Eye Detection Data saved to red_eye_data.csv")

# Calculate and display metrics
calculate_metrics('drowsiness_data.csv')
calculate_metrics('yawn_data.csv')
calculate_metrics('red_eye_data.csv')
