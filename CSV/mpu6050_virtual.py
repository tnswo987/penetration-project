import csv
import math
import random
import time

SAMPLE_RATE = 100 # Hz
DURATION_SEC = 20 # 총 20초
TOTAL_SAMPLES = SAMPLE_RATE * DURATION_SEC # 2000

CSV_FILE = "mpu6050_virtual.csv"

with open(CSV_FILE, 'w', newline='') as f:
    writer = csv.writer(f)
    
    writer.writerow(['timestamp', 'ax', 'ay', 'az', 'gx', 'gy', 'gz'])
    
    for t in range(TOTAL_SAMPLES):
        timestamp = t
        
        
        ax = int(500 * math.sin(2 * math.pi * 2 * t / SAMPLE_RATE)
                 + random.gauss(0, 20))

        ay = int(300 * math.sin(2 * math.pi * 3 * t / SAMPLE_RATE)
                 + random.gauss(0, 15))

        az = int(16384 
                 + 200 * math.sin(2 * math.pi * 1 * t / SAMPLE_RATE)
                 + random.gauss(0, 30))

        gx = int(50 * math.sin(2 * math.pi * 4 * t / SAMPLE_RATE)
                 + random.gauss(0, 3))

        gy = int(40 * math.sin(2 * math.pi * 5 * t / SAMPLE_RATE)
                 + random.gauss(0, 3))

        gz = int(30 * math.sin(2 * math.pi * 6 * t / SAMPLE_RATE)
                 + random.gauss(0, 2))
        
        writer.writerow([timestamp, ax, ay, az, gx, gy, gz])
print(f"CSV 생성완료 -> {CSV_FILE}")