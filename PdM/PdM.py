import numpy as np
import torch
# PyTorch에서 신경망을 만들기 위한 모든 레이어, 활성화 함수, 구조를 제공하는 모듈
import torch.nn as nn
import matplotlib.pyplot as plt

# 정상 IMU 데이터 생성
def generate_normal_data(n_samples=5000):
    # 0 ~ 20PI n_samples 등분
    t = np.linspace(0, 20*np.pi, n_samples)
    data = []
    
    # AX, AY, AZ, GX, GY, GZ
    for _ in range(6):
        # 노이즈 추가
        signal = np.sin(t) + 0.05*np.random.randn(n_samples)
        # 6축에 대해서 노이즈가 섞인 sin 함수 6개 생성
        data.append(signal)
    
    # 전치
    return np.array(data).T # shape: (5000, 6)

# 비정상 IMU 데이터 생성
def generate_abnormal_data(n_samples=3000):
    t = np.linspace(0, 20*np.pi, n_samples)
    data = []
    
    for _ in range(6):
        signal = 1.5*np.sin(1.2*t) + 0.3*np.random.randn(n_samples)

        for _ in range(20):
            # 랜덤 idx값 계산
            idx = np.random.randint(0, n_samples)
            # 이상치 추가
            signal[idx] += np.random.uniform(5, 10)
            
        data.append(signal)
    
    return np.array(data).T

# 슬라이딩 윈도우
def create_windows(data, window_size=50):
    windows = []
    
    for i in range(len(data) - window_size):
        windows.append(data[i:i+window_size])
    
    return np.array(windows)

class IMUAutoEncoder(nn.Module):
    def __init__(self):
        super().__init__()
        
        self.encoder = nn.Sequential(
            nn.Linear(50*6, 128),
            nn.ReLU(),
            nn.Linear(128, 32),
            nn.ReLU(),
            nn.Linear(32, 8),
        )
        
        self.decoder = nn.Sequential(
            nn.Linear(8, 32),
            nn.ReLU(),
            nn.Linear(32, 128),
            nn.ReLU(),
            nn.Linear(128, 50*6),
        )
    
    def forward(self, x):
        # x.size(0) = batch size
        
        x = x.view(x.size(0), -1)
        z = self.encoder(x)
        out = self.decoder(z)
        
        return out.view(x.size(0), 50, 6)

normal_data = generate_normal_data()
abnormal_data = generate_abnormal_data()

normal_windows = create_windows(normal_data)
abnormal_windows = create_windows(abnormal_data)

normal_tensor = torch.tensor(normal_windows, dtype=torch.float32)
abnormal_tensor = torch.tensor(abnormal_windows, dtype=torch.float32)

model = IMUAutoEncoder()
criterion = nn.MSELoss()
optimizer = torch.optim.Adam(model.parameters(), lr=0.001)

epochs = 20
for epoch in range(epochs):
    optimizer.zero_grad()
    output = model(normal_tensor)
    loss = criterion(output, normal_tensor)
    loss.backward()
    optimizer.step()
    print(f"Epoch {epoch+1}/{epochs}  Loss: {loss.item():.6f}")

with torch.no_grad():
    recon = model(normal_tensor)
    loss_per_window = ((recon - normal_tensor)**2).mean(dim=(1,2))

threshold = loss_per_window.mean() + 3*loss_per_window.std()
print("Anomaly threshold =", threshold.item())

with torch.no_grad():
    abnormal_recon = model(abnormal_tensor)
    abnormal_loss = ((abnormal_recon - abnormal_tensor)**2).mean(dim=(1,2))

detections = abnormal_loss > threshold
print("Detected abnormal windows:", detections.sum().item(), "/", len(detections))
