'''
Read Gyro and Accelerometer by Interfacing Raspberry Pi with MPU6050 using Python
http://www.electronicwings.com
'''
import smbus
import serial
import time
import numpy as np
import pandas as pd
from collections import deque

# Set up serial connection
try:
    ser = serial.Serial('/dev/ttyACM0', 115200, timeout=1)
except serial.SerialException as e:
    print(f"Serial connection failed: {e}")
    exit(1)

# MPU6050 Registers and their Address
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

print("Reading Data of Gyroscope, Accelerometer, and Gas Sensors")

# Initialize data storage for a 3-second window (20Hz * 3s = 60 samples max)
window_size = 60  # Max samples expected in 3 seconds
data_window = {
    'Ax': deque(maxlen=window_size),
    'Ay': deque(maxlen=window_size),
    'Az': deque(maxlen=window_size),
    'Gx': deque(maxlen=window_size),
    'Gy': deque(maxlen=window_size),
    'Gz': deque(maxlen=window_size),
    'co': deque(maxlen=window_size),
    'co2': deque(maxlen=window_size),
    'alcohol': deque(maxlen=window_size),
    'toluen': deque(maxlen=window_size),
    'nh4': deque(maxlen=window_size),
    'acetone': deque(maxlen=window_size),
}

# Initialize CSV file
csv_filename = 'train_data.csv'
columns = [
    'timestamp',
    'Ax_mean', 'Ay_mean', 'Az_mean',
    'Gx_mean', 'Gy_mean', 'Gz_mean',
    'co_mean', 'co2_mean', 'alcohol_mean', 'toluen_mean', 'nh4_mean', 'acetone_mean',
    'Ax_var', 'Ay_var', 'Az_var',
    'Gx_var', 'Gy_var', 'Gz_var',
    'co_var', 'co2_var', 'alcohol_var', 'toluen_var', 'nh4_var', 'acetone_var',
    'sample_count'
]

# Create CSV with headers if it doesn't exist
if not pd.io.common.file_exists(csv_filename):
    pd.DataFrame(columns=columns).to_csv(csv_filename, index=False)

# Track time for 3-second intervals
last_save_time = time.time()

while True:
    try:
        # Read Accelerometer raw value
        acc_x = read_raw_data(ACCEL_XOUT_H)
        acc_y = read_raw_data(ACCEL_YOUT_H)
        acc_z = read_raw_data(ACCEL_ZOUT_H)
        
        # Read Gyroscope raw value
        gyro_x = read_raw_data(GYRO_XOUT_H)
        gyro_y = read_raw_data(GYRO_YOUT_H)
        gyro_z = read_raw_data(GYRO_ZOUT_H)
        
        # Convert to physical units
        Ax = acc_x / 16384.0
        Ay = acc_y / 16384.0
        Az = acc_z / 16384.0
        Gx = gyro_x / 131.0
        Gy = gyro_y / 131.0
        Gz = gyro_z / 131.0
        
        # Read gas sensor data from Arduino
        read_serial = ser.readline()
        gases = read_serial.decode('utf-8').strip()
        try:
            co, co2, alcohol, toluen, nh4, acetone = map(float, gases.split(','))
        except ValueError:
            print(f"Invalid gas sensor data: {gases}")
            time.sleep(0.05)
            continue
        
        # Append data to window
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
        
        # Check if 3 seconds have passed
        current_time = time.time()
        if current_time - last_save_time >= 3.0:
            # Use available samples (may be <60 if delays occur)
            sample_count = len(data_window['Ax'])
            if sample_count > 0:  # Only compute if there’s data
                # Compute means
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
                }
                # Compute variances
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
                
                # Save to CSV
                timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
                row = {
                    'timestamp': timestamp,
                    **means,
                    **variances,
                    'sample_count': sample_count
                }
                df = pd.DataFrame([row])
                #df.to_csv(csv_filename, mode='a', header=False, index=False)
                
                print(f"Saved to CSV at {timestamp}: Ax_mean={means['Ax_mean']:.3f}, "
                      f"Ax_var={variances['Ax_var']:.3e}, Samples={sample_count}")
            
            # Update last save time to next 3-second boundary
            last_save_time += 3.0
            # Do NOT clear window to maintain sliding window behavior
        
        # Print current readings
        print(f"Gx={Gx:.2f}°/s\tGy={Gy:.2f}°/s\tGz={Gz:.2f}°/s\t"
              f"Ax={Ax:.2f}g\tAy={Ay:.2f}g\tAz={Az:.2f}g")
        print(f"CO: {co}, CO2: {co2}, Alcohol: {alcohol}, Toluen: {toluen}, "
              f"NH4: {nh4}, Acetone: {acetone}")
        
        time.sleep(0.05)
    
    except KeyboardInterrupt:
        print("Program terminated")
        ser.close()
        break
    except Exception as e:
        print(f"Error: {e}")
        time.sleep(0.05)
        continue
