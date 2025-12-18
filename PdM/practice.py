import numpy as np
from keras.models import Sequential
from keras.layers import LSTM, RepeatVector, TimeDistributed, Dense, Dropout
import pandas as pd
from matplotlib import pyplot as plt
from sklearn.preprocessing import MinMaxScaler, StandardScaler
from keras.models import Model
import seaborn as sns

dataframe = pd.read_csv('data.csv') # (7186, 6)
df = dataframe[['Date', 'Close']].copy() # (7186, 2)

df['Date'] = pd.to_datetime(df['Date'])

# sns.lineplot(x=df['Date'], y=df['Close'])
# plt.show()

# # print("Start date is: ", df['Date'].min())
# # print("End date is: ", df['Date'].max())

train = df.loc[df['Date'] <= '2020-12-31'].copy() # (5948, 2)
test = df.loc[df['Date'] > '2020-12-31'].copy() # (1238, 2)

scaler = StandardScaler()
scaler = scaler.fit(train[['Close']])

train['Close'] = scaler.transform(train[['Close']])
test['Close'] = scaler.transform(test[['Close']])

seq_size = 30

def to_sequences(x, y, seq_size=1):
    x_values = []
    y_values = []
    
    for i in range(len(x)-seq_size):
        x_values.append(x.iloc[i:(i+seq_size)].values)
        y_values.append(y.iloc[i+seq_size])
    
    return np.array(x_values), np.array(y_values)

# #trainX shape : (batch_size, seq_size, feature_size) 3D
# #trainY shape : (batch_size,) 1D
trainX, trainY = to_sequences(train[['Close']], train['Close'], seq_size)
testX, testY = to_sequences(test[['Close']], test['Close'], seq_size)

model = Sequential()
model.add(
    LSTM(
        128,
        activation='relu',
        input_shape=(trainX.shape[1], trainX.shape[2]),
        return_sequences=True
    )
)
model.add(
    LSTM(
        64,
        activation='relu',
        return_sequences=False
    )
) 
model.add(RepeatVector(trainX.shape[1]))
model.add(
    LSTM(
        64,
        activation='relu',
        return_sequences=True
    )
)
model.add(
    LSTM(
        128,
        activation='relu',
        return_sequences=True
    )
)
model.add(TimeDistributed(Dense(trainX.shape[2])))

model.compile(optimizer='adam', loss='mae')
model.summary()

# model = Sequential()

# model.add(LSTM(128, input_shape=(trainX.shape[1], trainX.shape[2])))
# model.add(Dropout(rate=0.2))

# model.add(RepeatVector(trainX.shape[1]))

# model.add(LSTM(128, return_sequences=True))
# model.add(Dropout(rate=0.2))

# model.add(TimeDistributed(Dense(trainX.shape[2])))

# model.compile(optimizer='adam', loss='mae')
# model.summary()

history = model.fit(trainX, trainX, epochs=10, batch_size=32, validation_split=0.1, verbose=1)

# overfitting 과적합 발생! 잡아야 한다.
plt.figure(figsize=(10, 5))
plt.plot(history.history['loss'], label='Training loss')
plt.plot(history.history['val_loss'], label='Validation loss')
plt.title("Training vs Validation Loss")
plt.xlabel("Epoch")
plt.ylabel("Loss")
plt.legend()
plt.grid()
plt.show()

# 이상치 판단 기준(threshold)을 설정하는 단계
# trainPredict Shape : (batch, 30, 1)
trainPredict = model.predict(trainX)
# axis=1 : 30개의 timestep에 대해 평균을 내겠다.
# 즉, batch마다 1개의 재구성 오차가 생긴다.
# trainMAE Shape : (batch, )
trainMAE = np.mean(np.abs(trainPredict - trainX), axis=1)
# trainMAE에 대해서 히스토그램을 그린다.
# 히스토그램 : 값을 구간별로 나눠서 몇 개가 있는지 세는 그래프
# bins=30 : 즉, 30구간으로 나누겠다.
plt.hist(trainMAE, bins=30)
plt.show()
# Z-score 방식
max_trainMAE = np.mean(trainMAE) + 3 * np.std(trainMAE)
print(max_trainMAE)


# testPredict = model.predict(testX)
# testMAE = np.mean(np.abs(testPredict - testX), axis=1)
# plt.hist(testMAE, bins=30)

# #testX 데이터에 의해, 앞의 0~29 데이터는 예측으로 사용되기 때문에 슬라이싱
# anomaly_df = pd.DataFrame(test[seq_size:])
# anomaly_df['testMAE'] = testMAE
# anomaly_df['max_trainMAE'] = max_trainMAE
# anomaly_df['anomaly'] = anomaly_df['testMAE'] > anomaly_df['max_trainMAE']
# anomaly_df['Close'] = test[seq_size:]['Close']

# sns.lineplot(x=anomaly_df['Date'], y=anomaly_df['testMAE'])
# sns.lineplot(x=anomaly_df['Date'], y=anomaly_df['max_trainMAE'])
# plt.show()

# anomalies = anomaly_df.loc[anomaly_df['anomaly'] == True]

# sns.lineplot(
#     x=anomaly_df['Date'], 
#     y=scaler.inverse_transform(anomaly_df[['Close']]).flatten()
# )
# sns.scatterplot(
#     x=anomalies['Date'],
#     y=scaler.inverse_transform(anomalies[['Close']]).flatten(),
#     color='r'
# )
# plt.show()