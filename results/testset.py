import csv
from datetime import datetime, timedelta

# Input log file path
log_file_path = "alerts_not_drowsy_normal.txt"

# Output structure
output_rows = []

# Function to extract timestamp and condition
def parse_log_line(line):
    timestamp_str = line.split(" - ")[0].strip()
    condition = line.split(" - ")[1].split(" detected")[0].strip()
    timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
    return timestamp, condition

# Read and parse log file
with open(log_file_path, "r") as file:
    log_lines = [line.strip() for line in file if line.strip()]

prev_time = None

for line in log_lines:
    curr_time, condition = parse_log_line(line)

    # Fill intermediate "normal" entries if needed
    if prev_time is not None:
        diff = (curr_time - prev_time).seconds
        if diff > 3:
            for i in range(1, diff // 3):
                new_time = prev_time + timedelta(seconds=3 * i)
                output_rows.append({
                    "timestamp": new_time.strftime("%Y-%m-%d %H:%M:%S"),
                    "condition": "normal",
                    "label": 0,
                    "pred": 0
                })
        # elif diff % 3 != 0:
        #     new_time = prev_time + timedelta(seconds=3)
        #     output_rows.append({
        #         "timestamp": new_time.strftime("%Y-%m-%d %H:%M:%S"),
        #         "condition": "normal",
        #         "label": 0,
        #         "pred": 0
        #     })

    # Add current event
    pred = 1 if condition.lower() in ["drowsiness", "yawn", "anomaly"] else 0
    output_rows.append({
        "timestamp": curr_time.strftime("%Y-%m-%d %H:%M:%S"),
        "condition": condition,
        "label": 0,
        "pred": pred
    })

    prev_time = curr_time

# Write to CSV
with open("drowsiness_log.csv", "a", newline="") as csvfile:
    fieldnames = ["timestamp", "condition", "label", "pred"]
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(output_rows)

print("CSV file 'drowsiness_log.csv' generated successfully from 'drowsiness.log'.")

