# working.py
import smbus
import serial
import time
import numpy as np
import pandas as pd
from collections import deque
from sklearn.preprocessing import StandardScaler
import joblib
import queue

# Shared queue for alerts
#alert_queue = queue.Queue()

# --- Inference Functions ---
def load_model_and_scaler(model_path='backup2.pkl', scaler_path='scaler.pkl'):
    try:
        model = joblib.load(model_path)
        scaler = joblib.load(scaler_path)
        print("Model and scaler loaded successfully.")
        return model, scaler
    except FileNotFoundError as e:
        print(f"Error: {e}. Ensure model and scaler files exist.")
        return None, None

def preprocess_data_point(data_point, scaler):
    if isinstance(data_point, dict):
        df = pd.DataFrame([data_point])
    else:
        raise ValueError("Input data_point must be a dictionary.")

    columns_to_drop = ['timestamp', 'sample_count', 'toluen_var', 'nh4_var', 'acetone_var',
                       'toluen_mean', 'nh4_mean', 'acetone_mean', 'co_var', 'co2_var', 'alcohol_var']
    features = df.drop(columns=[col for col in columns_to_drop if col in df.columns])

    if features.isnull().any().any():
        print("Warning: Missing values detected. Filling with 0.")
        features = features.fillna(0)

    X = features.values
    X_scaled = scaler.transform(X)
    return X_scaled

def predict_anomaly(model, X_scaled):
    prediction = model.predict(X_scaled)
    score = model.decision_function(X_scaled)
    label = 'Anomaly' if prediction[0] == -1 else 'Normal'
    return label, score[0]

def inference_pipeline(data_point, model, scaler, alert_queue):
    if model is None or scaler is None:
        print("Model or scaler not loaded. Skipping inference.")
        return None, None
    X_scaled = preprocess_data_point(data_point, scaler)
    label, score = predict_anomaly(model, X_scaled)
    print(f"Prediction: {label}, Anomaly Score: {score:.6f}")
    if label == 'Anomaly':
        print("generating Alert")
        alert_queue.put(f"Anomaly detected at {time.strftime('%Y-%m-%d %H:%M:%S')}, Score: {score:.6f}")
    time.sleep(5)
    return label, score

# --- Sensor Data Collection ---
try:
    ser = serial.Serial('/dev/ttyACM0', 115200, timeout=1)
except serial.SerialException as e:
    print(f"Serial connection failed: {e}")
    exit(1)

PWR_MGMT_1 = 0x6B
SMPLRT_DIV = 0x19
CONFIG = 0x1A
GYRO_CONFIG = 0x1B
INT_ENABLE = 0x38
ACCEL_XOUT_H = 0x3B
ACCEL_YOUT_H = 0x3D
ACCEL_ZOUT_H = 0x3F
GYRO_XOUT_H = 0x43
GYRO_YOUT_H = 0x45
GYRO_ZOUT_H = 0x47

def MPU_Init():
    try:
        bus.write_byte_data(Device_Address, SMPLRT_DIV, 7)
        bus.write_byte_data(Device_Address, PWR_MGMT_1, 1)
        bus.write_byte_data(Device_Address, CONFIG, 0)
        bus.write_byte_data(Device_Address, GYRO_CONFIG, 24)
        bus.write_byte_data(Device_Address, INT_ENABLE, 1)
    except Exception as e:
        print(f"MPU6050 initialization failed: {e}")
        exit(1)

def read_raw_data(addr):
    try:
        high = bus.read_byte_data(Device_Address, addr)
        low = bus.read_byte_data(Device_Address, addr + 1)
        value = ((high << 8) | low)
        if value > 32768:
            value = value - 65536
        return value
    except Exception as e:
        print(f"Error reading MPU6050 data: {e}")
        return 0

bus = smbus.SMBus(1)
Device_Address = 0x68
MPU_Init()

# Load model and scaler at startup
model, scaler = load_model_and_scaler()

print("Reading Data of Gyroscope, Accelerometer, and Gas Sensors")

window_size = 60
data_window = {
    'Ax': deque(maxlen=window_size), 'Ay': deque(maxlen=window_size), 'Az': deque(maxlen=window_size),
    'Gx': deque(maxlen=window_size), 'Gy': deque(maxlen=window_size), 'Gz': deque(maxlen=window_size),
    'co': deque(maxlen=window_size), 'co2': deque(maxlen=window_size), 'alcohol': deque(maxlen=window_size),
    'toluen': deque(maxlen=window_size), 'nh4': deque(maxlen=window_size), 'acetone': deque(maxlen=window_size),
}

csv_filename = 'test_data.csv'
columns = [
    'timestamp',
    'Ax_mean', 'Ay_mean', 'Az_mean', 'Gx_mean', 'Gy_mean', 'Gz_mean',
    'co_mean', 'co2_mean', 'alcohol_mean', 'toluen_mean', 'nh4_mean', 'acetone_mean',
    'Ax_var', 'Ay_var', 'Az_var', 'Gx_var', 'Gy_var', 'Gz_var',
    'co_var', 'co2_var', 'alcohol_var', 'toluen_var', 'nh4_var', 'acetone_var',
    'mean_bpm', 'sample_count'
]

if not pd.io.common.file_exists(csv_filename):
    pd.DataFrame(columns=columns).to_csv(csv_filename, index=False)

last_save_time = time.time()
fixed_bpm = 70.0

def reset_data_window():
    """Reset the data window to clear anomalous data."""
    global data_window
    data_window = {
        'Ax': deque(maxlen=window_size), 'Ay': deque(maxlen=window_size), 'Az': deque(maxlen=window_size),
        'Gx': deque(maxlen=window_size), 'Gy': deque(maxlen=window_size), 'Gz': deque(maxlen=window_size),
        'co': deque(maxlen=window_size), 'co2': deque(maxlen=window_size), 'alcohol': deque(maxlen=window_size),
        'toluen': deque(maxlen=window_size), 'nh4': deque(maxlen=window_size), 'acetone': deque(maxlen=window_size),
    }
    print("Data window reset after anomaly detection.")

def run_sensor_loop(alert_queue):
    global last_save_time, model, scaler
    while True:
        try:
            acc_x = read_raw_data(ACCEL_XOUT_H)
            acc_y = read_raw_data(ACCEL_YOUT_H)
            acc_z = read_raw_data(ACCEL_ZOUT_H)
            gyro_x = read_raw_data(GYRO_XOUT_H)
            gyro_y = read_raw_data(GYRO_YOUT_H)
            gyro_z = read_raw_data(GYRO_ZOUT_H)

            Ax = acc_x / 16384.0
            Ay = acc_y / 16384.0
            Az = acc_z / 16384.0
            Gx = gyro_x / 131.0
            Gy = gyro_y / 131.0
            Gz = gyro_z / 131.0

            read_serial = ser.readline()
            gases = read_serial.decode('utf-8').strip()
            try:
                co, co2, alcohol, toluen, nh4, acetone = map(float, gases.split(','))
            except ValueError:
                print(f"Invalid gas sensor data: {gases}")
                time.sleep(0.05)
                continue

            data_window['Ax'].append(Ax)
            data_window['Ay'].append(Ay)
            data_window['Az'].append(Az)
            data_window['Gx'].append(Gx)
            data_window['Gy'].append(Gy)
            data_window['Gz'].append(Gz)
            data_window['co'].append(co)
            data_window['co2'].append(co2)
            data_window['alcohol'].append(alcohol)
            data_window['toluen'].append(toluen)
            data_window['nh4'].append(nh4)
            data_window['acetone'].append(acetone)

            current_time = time.time()
            if current_time - last_save_time >= 3.0:
                sample_count = len(data_window['Ax'])
                if sample_count > 0:
                    means = {
                        'Ax_mean': np.mean(data_window['Ax']),
                        'Ay_mean': np.mean(data_window['Ay']),
                        'Az_mean': np.mean(data_window['Az']),
                        'Gx_mean': np.mean(data_window['Gx']),
                        'Gy_mean': np.mean(data_window['Gy']),
                        'Gz_mean': np.mean(data_window['Gz']),
                        'co_mean': np.mean(data_window['co']),
                        'co2_mean': np.mean(data_window['co2']),
                        'alcohol_mean': np.mean(data_window['alcohol']),
                        'toluen_mean': np.mean(data_window['toluen']),
                        'nh4_mean': np.mean(data_window['nh4']),
                        'acetone_mean': np.mean(data_window['acetone']),
                        'mean_bpm': fixed_bpm
                    }
                    variances = {
                        'Ax_var': np.var(data_window['Ax'], ddof=1) if sample_count > 1 else 0.0,
                        'Ay_var': np.var(data_window['Ay'], ddof=1) if sample_count > 1 else 0.0,
                        'Az_var': np.var(data_window['Az'], ddof=1) if sample_count > 1 else 0.0,
                        'Gx_var': np.var(data_window['Gx'], ddof=1) if sample_count > 1 else 0.0,
                        'Gy_var': np.var(data_window['Gy'], ddof=1) if sample_count > 1 else 0.0,
                        'Gz_var': np.var(data_window['Gz'], ddof=1) if sample_count > 1 else 0.0,
                        'co_var': np.var(data_window['co'], ddof=1) if sample_count > 1 else 0.0,
                        'co2_var': np.var(data_window['co2'], ddof=1) if sample_count > 1 else 0.0,
                        'alcohol_var': np.var(data_window['alcohol'], ddof=1) if sample_count > 1 else 0.0,
                        'toluen_var': np.var(data_window['toluen'], ddof=1) if sample_count > 1 else 0.0,
                        'nh4_var': np.var(data_window['nh4'], ddof=1) if sample_count > 1 else 0.0,
                        'acetone_var': np.var(data_window['acetone'], ddof=1) if sample_count > 1 else 0.0,
                    }

                    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
                    row = {
                        'timestamp': timestamp,
                        'Ax_mean': means['Ax_mean'],
                        'Ay_mean': means['Ay_mean'],
                        'Az_mean': means['Az_mean'],
                        'Gx_mean': means['Gx_mean'],
                        'Gy_mean': means['Gy_mean'],
                        'Gz_mean': means['Gz_mean'],
                        'Ax_var': variances['Ax_var'],
                        'Ay_var': variances['Ay_var'],
                        'Az_var': variances['Az_var'],
                        'Gx_var': variances['Gx_var'],
                        'Gy_var': variances['Gy_var'],
                        'Gz_var': variances['Gz_var'],
                        'co_mean': means['co_mean'],
                        'co2_mean': means['co2_mean'],
                        'alcohol_mean': means['alcohol_mean'],
                        'toluen_mean': means['toluen_mean'],
                        'nh4_mean': means['nh4_mean'],
                        'acetone_mean': means['acetone_mean'],
                        'co_var': variances['co_var'],
                        'co2_var': variances['co2_var'],
                        'alcohol_var': variances['alcohol_var'],
                        'toluen_var': variances['toluen_var'],
                        'nh4_var': variances['nh4_var'],
                        'acetone_var': variances['acetone_var'],
                        'sample_count': sample_count,
                        'mean_bpm': fixed_bpm
                    }

                    df = pd.DataFrame([row])
                    df.to_csv(csv_filename, mode='a', header=False, index=False)

                    label, score = inference_pipeline(row, model, scaler, alert_queue)
                    if label == 'Anomaly':
                        print("Anomaly detected. Resetting data window and model...")
                        reset_data_window()
                        # Optionally reload model and scaler to reset state
                        model, scaler = load_model_and_scaler()

                last_save_time += 3.0

            time.sleep(0.05)

        except Exception as e:
            print(f"Error in sensor loop: {e}")
            time.sleep(0.1)

if __name__ == "__main__":
    try:
        run_sensor_loop(queue.Queue())
    except KeyboardInterrupt:
        print("Sensor program terminated")
        ser.close()
