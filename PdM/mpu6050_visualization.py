import pandas as pd
import matplotlib.pyplot as plt

csv_path = "mpu6050_train.csv"  # 네 파일명으로 수정
df = pd.read_csv(csv_path)

t = df["t"] / 1000.0   # 초 단위 (선택)

# =========================
# 가속도 (RAW) 시각화
# =========================
plt.figure(figsize=(12, 6))
plt.plot(t, df["AcX"], label="AcX")
plt.plot(t, df["AcY"], label="AcY")
plt.plot(t, df["AcZ"], label="AcZ")

plt.title("MPU6050 Accelerometer (RAW)")
plt.xlabel("Time (s)")
plt.ylabel("Raw Value")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()

# =========================
# 자이로 (RAW) 시각화
# =========================
plt.figure(figsize=(12, 6))
plt.plot(t, df["GyX"], label="GyX")
plt.plot(t, df["GyY"], label="GyY")
plt.plot(t, df["GyZ"], label="GyZ")

plt.title("MPU6050 Gyroscope (RAW)")
plt.xlabel("Time (s)")
plt.ylabel("Raw Value")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()
