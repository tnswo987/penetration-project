import numpy as np
import pandas as pd
from keras.models import Sequential
from keras.layers import LSTM, RepeatVector, TimeDistributed, Dense
from keras.callbacks import EarlyStopping
from sklearn.preprocessing import StandardScaler
from matplotlib import pyplot as plt
import joblib

dataframe = pd.read_csv("mpu6050_train.csv")

TIME_COL = 't'
FEATURE_COLS = ['AcX', 'AcY', 'AcZ', 'GyX', 'GyY', 'GyZ']

df = dataframe[[TIME_COL] + FEATURE_COLS].copy()
df = df.sort_values(TIME_COL).reset_index(drop=True)

split_idx = int(len(df) * 0.8)

train = df.iloc[:split_idx].copy()
test  = df.iloc[split_idx:].copy()

scaler = StandardScaler()
scaler.fit(train[FEATURE_COLS])

train[FEATURE_COLS] = scaler.transform(train[FEATURE_COLS])
test[FEATURE_COLS]  = scaler.transform(test[FEATURE_COLS])

SEQ_SIZE = 30

def to_sequences(data, seq_size):
    sequences = []
    for i in range(len(data) - seq_size):
        sequences.append(data.iloc[i:i+seq_size].values)
    return np.array(sequences)

trainX = to_sequences(train[FEATURE_COLS], SEQ_SIZE)
testX  = to_sequences(test[FEATURE_COLS], SEQ_SIZE)

print("trainX shape:", trainX.shape)
print("testX shape :", testX.shape)

model = Sequential()

model.add(LSTM(
    128,
    activation='relu',
    input_shape=(SEQ_SIZE, len(FEATURE_COLS)),
    return_sequences=True
))

model.add(LSTM(
    64,
    activation='relu',
    return_sequences=False
))

model.add(RepeatVector(SEQ_SIZE))

model.add(LSTM(
    64,
    activation='relu',
    return_sequences=True
))

model.add(LSTM(
    128,
    activation='relu',
    return_sequences=True
))

model.add(TimeDistributed(Dense(len(FEATURE_COLS))))

model.compile(optimizer='adam', loss='mae')
model.summary()
early_stop = EarlyStopping(
    monitor='val_loss',
    patience=8,
    restore_best_weights=True,
)

history = model.fit(
    trainX,
    trainX,
    epochs=100,
    batch_size=32,
    validation_split=0.1,
    shuffle=False,
    callbacks=[early_stop],
    verbose=1
)

model.save("LSTM_AutoEncoder_MPU6050.h5")
print("모델 저장 완료")

joblib.dump(scaler, "mpu6050_scaler.pkl")
print("스케일러 저장 완료")

# loss, val_loss 그래프 시각화
plt.figure(figsize=(10, 4))
plt.plot(history.history['loss'], label='Train Loss')
plt.plot(history.history['val_loss'], label='Val Loss')
plt.legend()
plt.grid()
plt.show()

# 학습/검증셋 reconstruction error 비교
train_recon = model.predict(trainX)
train_error = np.mean(np.abs(train_recon - trainX), axis=(1, 2))

test_recon = model.predict(testX)
test_error = np.mean(np.abs(test_recon - testX), axis=(1,2))

threshold = np.percentile(train_error, 95)
np.save("mpu6050_threshold.npy", threshold)
print("Threshold 저장 완료:", threshold)

plt.figure(figsize=(7,4))
plt.hist(train_error, bins=50, alpha=0.6, label='Train')
plt.hist(test_error, bins=50, alpha=0.6, label='Hold-out Normal')
plt.legend()
plt.title("Reconstruction Error Distribution (Normal Data)")
plt.xlabel("MAE")
plt.ylabel("Count")
plt.grid()
plt.show()

plt.figure(figsize=(12,4))
plt.plot(test_error)
plt.title("Reconstruction Error Over Time (Hold-out Normal)")
plt.xlabel("Sequence Index")
plt.ylabel("MAE")
plt.grid()
plt.show()