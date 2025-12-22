import numpy as np
import pandas as pd
from keras.models import load_model
from sklearn.preprocessing import StandardScaler
from matplotlib import pyplot as plt
import joblib

# ===============================
# 설정
# ===============================
CSV_PATH = "mpu6050_train.csv"
MODEL_PATH = "LSTM_AutoEncoder_MPU6050.h5"
SCALER_PATH = "mpu6050_scaler.pkl"

TIME_COL = "t"
FEATURE_COLS = ['AcX', 'AcY', 'AcZ', 'GyX', 'GyY', 'GyZ']
SEQ_SIZE = 30

# ===============================
# 데이터 로드
# ===============================
df = pd.read_csv(CSV_PATH)
df = df[[TIME_COL] + FEATURE_COLS].copy()
df = df.sort_values(TIME_COL).reset_index(drop=True)

# train/test 분리 (학습 때와 동일해야 함)
split_idx = int(len(df) * 0.8)
test = df.iloc[split_idx:].copy()

# ===============================
# 스케일러 로드 & 변환
# ===============================
scaler = joblib.load(SCALER_PATH)
test[FEATURE_COLS] = scaler.transform(test[FEATURE_COLS])

# ===============================
# 시퀀스 생성
# ===============================
def to_sequences(data, seq_size):
    seqs = []
    for i in range(len(data) - seq_size):
        seqs.append(data.iloc[i:i+seq_size].values)
    return np.array(seqs)

testX = to_sequences(test[FEATURE_COLS], SEQ_SIZE)

print("testX shape:", testX.shape)

# ===============================
# 모델 로드
# ===============================
model = load_model(MODEL_PATH)

# ===============================
# Reconstruction Error 계산
# ===============================
test_recon = model.predict(testX, verbose=1)
test_error = np.mean(np.abs(test_recon - testX), axis=(1, 2))

# ===============================
# 그래프 출력
# ===============================
plt.figure(figsize=(12,4))
plt.plot(test_error)
plt.title("Reconstruction Error Over Time (Hold-out Normal)")
plt.xlabel("Sequence Index")
plt.ylabel("MAE")
plt.grid()
plt.show()
