import numpy as np
import pandas as pd
from keras.models import load_model
from sklearn.preprocessing import StandardScaler
import matplotlib.pyplot as plt
import seaborn as sns

model = load_model("LSTM_AE.h5")
print("모델 불러오기 완료!")

dataframe = pd.read_csv('data.csv') # (7186, 6)
df = dataframe[['Date', 'Close']].copy() # (7186, 2)

df['Date'] = pd.to_datetime(df['Date'])

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

trainX, trainY = to_sequences(train[['Close']], train['Close'], seq_size)
testX, testY = to_sequences(test[['Close']], test['Close'], seq_size)

trainPredict = model.predict(trainX)
trainMAE = np.mean(np.abs(trainPredict - trainX), axis=1)
max_trainMAE = np.mean(trainMAE) + 3 * np.std(trainMAE)

testPredict = model.predict(testX)
testMAE = np.mean(np.abs(testPredict - testX), axis=1)

#testX 데이터에 의해, 앞의 0~29 데이터는 예측으로 사용되기 때문에 슬라이싱
anomaly_df = pd.DataFrame(test[seq_size:])
anomaly_df['testMAE'] = testMAE
anomaly_df['max_trainMAE'] = max_trainMAE
anomaly_df['anomaly'] = anomaly_df['testMAE'] > anomaly_df['max_trainMAE']

# sns.lineplot(x=anomaly_df['Date'], y=anomaly_df['testMAE'])
# sns.lineplot(x=anomaly_df['Date'], y=anomaly_df['max_trainMAE'])
# plt.show()

anomalies = anomaly_df.loc[anomaly_df['anomaly'] == True]

sns.lineplot(
    x=anomaly_df['Date'], 
    y=scaler.inverse_transform(anomaly_df[['Close']]).flatten()
)
sns.scatterplot(
    x=anomalies['Date'],
    y=scaler.inverse_transform(anomalies[['Close']]).flatten(),
    color='r'
)
plt.show()