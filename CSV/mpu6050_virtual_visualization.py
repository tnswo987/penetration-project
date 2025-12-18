
import pandas as pd
import matplotlib.pyplot as plt

# CSV 로드
df = pd.read_csv("mpu6050_virtual.csv")

# 시간축
t = df['timestamp']

# ---------------------------
# 가속도 시각화
# ---------------------------
plt.figure(figsize=(12, 6))
plt.plot(t, df['ax'], label='ax')
plt.plot(t, df['ay'], label='ay')
plt.plot(t, df['az'], label='az')
plt.title("MPU6050 Accelerometer (RAW)")
plt.xlabel("Time")
plt.ylabel("Value")
plt.legend()
plt.grid(True)
plt.show()

# ---------------------------
# 자이로 시각화
# ---------------------------
plt.figure(figsize=(12, 6))
plt.plot(t, df['gx'], label='gx')
plt.plot(t, df['gy'], label='gy')
plt.plot(t, df['gz'], label='gz')
plt.title("MPU6050 Gyroscope (RAW)")
plt.xlabel("Time")
plt.ylabel("Value")
plt.legend()
plt.grid(True)
plt.show()