import serial
import csv
import time

PORT = "COM5"
BAUDRATE = 115200
CSV_FILENAME = "mpu6050_train.csv"

ser = serial.Serial(PORT, BAUDRATE, timeout=1)
print(f"[INFO] Connected to {PORT}")

print("[INFO] Waiting for START signal...")
while True:
    line = ser.readline().decode(errors="ignore").strip()
    if line == "START":
        print("[INFO] START received")
        break
    
header = ser.readline().decode().strip().split(",")
print("[INFO] Header:", header)

with open(CSV_FILENAME, mode="w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(header)

    print("[INFO] Recording data... (Ctrl+C to stop)")
    try:
        while True:
            line = ser.readline().decode(errors="ignore").strip()
            if not line:
                continue

            values = line.split(",")

            if len(values) != len(header):
                continue

            writer.writerow(values)

            print(values)

    except KeyboardInterrupt:
        print("\n[INFO] Stopped by user")

ser.close()
print("[INFO] Serial closed")