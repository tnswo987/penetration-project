import numpy as np
from keras.models import Sequential
from keras.layers import LSTM, RepeatVector, TimeDistributed, Dense
import pandas as pd
from matplotlib import pyplot as plt
from sklearn.preprocessing import MinMaxScaler, StandardScaler
from keras.models import Model
import seaborn as sns

# 데이터 읽기
dataframe = pd.read_csv('data/GE.csv')
# 데이터에서 Data, Close열만 들고오겠다.
df = dataframe[['Date', 'Close']]
# 'Date' 컬럼을 str → datetime 형식으로 변환
df['Date'] = pd.to_datetime(df['Date'])


sns.lineplot(x=df['Date'], y=df['Close'])

print("Start date is: ", df['Date'].min())
print("End date is: ", df['Date'].max())

# Change train data from Mid 2017 to 2019.... seems to be a jump early 2017
train, test = df.loc[df['Date'] <= '2003-12-31'], df.loc[df['Date'] > '2003-12-31']

# # Convert pandas dataframe to numpy array
# dataset = dataframe.values
# # Convert values to float
# dataset = dataset.astype('float32')

# LSTM uses sigmoid and tanh that are sensitive to magnitude so values need to be normalized
# normalize the dataset
# scaler = MinMaxScaler() # Also try QuantileTransformer
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

#trainX shape : (batch_size, seq_size, feature_size) 3D
#trainY shape : (batch_size,) 1D
trainX, trainY = to_sequences(train[['Close']], train['Close'], seq_size)
testX, testY = to_sequences(test[['Close']], test['Close'], seq_size)

trainX = np.random.rand(10, 30, 1)  # batch=10, timesteps=30, features=1
# Input : (N, 30, 1)
model = Sequential()

# (N, 30, 1) → (N, 30, 128) # 정보 1차 압축
model.add(
    LSTM(
        128,
        activation='relu',
        input_shape=(trainX.shape[1], trainX.shape[2]),
        return_sequences=True # 두번째 LSTM에 적합한 형태의 시계열 데이터를 주기 위함
    )
)
# (N, 30, 128) → (N, 64) # 정보 최종 압축
model.add(
    LSTM(
        64,
        activation='relu',
        return_sequences=False
    )
)
# (N, 64) → (N, 30, 64) # Decoder가 사용할 수 있도록 재구성  
model.add(RepeatVector(trainX.shape[1]))
# (N, 30, 64) → (N, 30, 64)
# RepeatVector로 단순히 복붙된 시계열 특징이 없는 데이터를 LSTM을 거쳐 시계열 데이터의 특징을 복원하는 과정
model.add(
    LSTM(
        64,
        activation='relu',
        return_sequences=True
    )
)
# (N, 30, 64) → (N, 30, 128) # 2차 복원
model.add(
    LSTM(
        128,
        activation='relu',
        return_sequences=True
    )
)
# (N, 30, 128) → (N, 30, 1) # 최종 복원
model.add(TimeDistributed(Dense(trainX.shape[2])))

model.compile(optimizer='adam', loss='mse')
model.summary()