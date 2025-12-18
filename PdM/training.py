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

history = model.fit(trainX, trainX, epochs=10, batch_size=32, validation_split=0.1, verbose=1)
model.save("LSTM_AE.h5")
print("모델 저장 완료!")

plt.figure(figsize=(10, 5))
plt.plot(history.history['loss'], label='Training loss')
plt.plot(history.history['val_loss'], label='Validation loss')
plt.title("Training vs Validation Loss")
plt.xlabel("Epoch")
plt.ylabel("Loss")
plt.legend()
plt.grid()
plt.show()


