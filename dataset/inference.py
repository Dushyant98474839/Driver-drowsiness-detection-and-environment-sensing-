import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
import joblib

def load_model_and_scaler(model_path='isolation_forest_model.pkl', scaler_path='scaler.pkl'):
    """Load the trained Isolation Forest model and scaler."""
    try:
        model = joblib.load(model_path)
        scaler = joblib.load(scaler_path)
        print("Model and scaler loaded successfully.")
        return model, scaler
    except FileNotFoundError as e:
        print(f"Error: {e}. Ensure model and scaler files exist.")
        return None, None

def preprocess_data_point(data_point, scaler):
    """Preprocess a single data point for inference."""
    # Convert data point to DataFrame if it's a dictionary
    if isinstance(data_point, dict):
        df = pd.DataFrame([data_point])
    elif isinstance(data_point, pd.DataFrame):
        df = data_point.copy()
    else:
        raise ValueError("Input data_point must be a dictionary or DataFrame.")

    # Drop irrelevant columns (same as training)
    columns_to_drop = ['timestamp', 'sample_count', 'toluen_var', 'nh4_var', 'acetone_var',
                       'toluen_mean', 'nh4_mean', 'acetone_mean', 'co_var', 'co2_var', 'alcohol_var']
    features = df.drop(columns=[col for col in columns_to_drop if col in df.columns])

    # Apply scaling factor to gas features
    # gas_features = ['co_mean', 'alcohol_mean', 'co2_mean']
    # scaling_factor = 0.01  # Same as training
    # for col in gas_features:
    #     if col in features.columns:
    #         features[col] = features[col] * scaling_factor

    # Handle missing values
    if features.isnull().any().any():
        print("Warning: Missing values detected. Filling with 0.")
        features = features.fillna(0)

    # Convert to numpy array and scale
    X = features.values
    X_scaled = scaler.transform(X)
    return X_scaled

def predict_anomaly(model, X_scaled):
    """Predict whether the data point is an anomaly."""
    # Predict: -1 for anomaly, 1 for normal
    prediction = model.predict(X_scaled)
    # Get anomaly score (negative values indicate more anomalous)
    score = model.decision_function(X_scaled)
    # Map prediction to label
    label = 'Anomaly' if prediction[0] == -1 else 'Normal'
    return label, score[0]

def inference_pipeline(data_point, model_path='isolation_forest_model.pkl', scaler_path='scaler.pkl'):
    """Run the full inference pipeline for a single data point."""
    # Load model and scaler
    model, scaler = load_model_and_scaler(model_path, scaler_path)
    if model is None or scaler is None:
        return None, None

    # Preprocess data point
    X_scaled = preprocess_data_point(data_point, scaler)

    # Predict
    label, score = predict_anomaly(model, X_scaled)
    print(f"Prediction: {label}, Anomaly Score: {score:.6f}")
    return label, score

if __name__ == "__main__":
    # Sample data point (mimicking final.csv structure)
    sample_data_point = {
        'timestamp': '2025-04-17 12:50:00',
        'sample_count': 30,
        'Ax_mean': 1.0820,
        'Ay_mean': 0.0010,
        'Az_mean': -0.0150,
        'Gx_mean': -0.100,
        'Gy_mean': -0.09600,
        'Gz_mean': -0.2700,
        'Ax_var': 0.0070,
        'Ay_var': 0.0040,
        'Az_var': 0.0035,
        'Gx_var': 0.2000,
        'Gy_var': 0.4500,
        'Gz_var': 0.1600,
        'co_mean': 4.5000,
        'co2_mean': 405.0000,
        'alcohol_mean': 10.0000,
        'mean_bpm': 70.0000,
        'toluen_var': 0.0,
        'nh4_var': 0.0,
        'acetone_var': 0.0,
        'toluen_mean': 0.0,
        'nh4_mean': 0.0,
        'acetone_mean': 0.0,
        'co_var': 50.0,
        'co2_var': 0.0,
        'alcohol_var': 0.0
    }

    # Run inference
    label, score = inference_pipeline(sample_data_point)