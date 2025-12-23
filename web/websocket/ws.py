import json
import time
import threading
import serial
from collections import deque

import numpy as np
import joblib
from keras.models import load_model
from websocket_server import WebsocketServer

SERIAL_PORT = "COM12"
BAUDRATE = 115200
WS_PORT = 3001

SENSOR_INTERVAL = 0.03
SEQ_SIZE = 30
seq = 0
last_ai_result = None
AI_HZ = 10
AI_PERIOD = 1.0 / AI_HZ

ANOMALY_TIME_SEC = 1.0

FEATURE_NAMES = ["AcX", "AcY", "AcZ", "GyX", "GyY", "GyZ"]

MODEL_PATH = "LSTM_AutoEncoder_MPU6050.h5"
SCALER_PATH = "mpu6050_scaler.pkl"
THRESHOLD_PATH = "mpu6050_threshold.npy"

mpu_buffer = deque(maxlen=SEQ_SIZE)
latest_sensor = None
connected = False

anomaly_duration = 0.0
last_ai_time = 0.0

lock = threading.Lock()

model = load_model(MODEL_PATH)
scaler = joblib.load(SCALER_PATH)
threshold = float(np.load(THRESHOLD_PATH))

# SERIAL PARSER
def parse_mpu_line(line: str):
    parts = line.split(",")
    if len(parts) != 7:
        return None
    try:
        return {
            "t_ms": int(parts[0]),
            "pc_ts": time.time(),
            "AcX": int(parts[1]),
            "AcY": int(parts[2]),
            "AcZ": int(parts[3]),
            "GyX": int(parts[4]),
            "GyY": int(parts[5]),
            "GyZ": int(parts[6]),
        }
    except ValueError:
        return None

# THREAD 1: SERIAL COLLECTOR
def serial_thread():
    global connected, latest_sensor

    ser = serial.Serial(SERIAL_PORT, BAUDRATE, timeout=1)
    time.sleep(2)
    connected = True
    print("[SERIAL] Connected")

    while True:
        try:
            line = ser.readline().decode(errors="ignore").strip()
            if not line or line.startswith("t,AcX"):
                continue

            data = parse_mpu_line(line)
            if data is None:
                continue

            with lock:
                latest_sensor = data
                mpu_buffer.append([data[k] for k in FEATURE_NAMES])

        except Exception as e:
            print("[SERIAL ERROR]", e)
            connected = False
            time.sleep(1)

# THREAD 2 : AI INFERENCE
def ai_thread():
    global anomaly_duration, last_ai_time, last_ai_result

    while True:
        now = time.time()

        # AI 추론 주기를 기다린다.
        if now - last_ai_time < AI_PERIOD:
            time.sleep(0.001) # 1ms 지연
            continue
        
        # 최신 추론 시간 갱신
        last_ai_time = now

        # Window 길이 조건
        if len(mpu_buffer) < SEQ_SIZE:
            continue

        # 가장 최신 0.9초 (= 1 Window(=30 STEP)) 데이터 Numpy로 가공
        with lock:
            seq_np = np.array(mpu_buffer, dtype=np.float32)
            latest_ts = latest_sensor["pc_ts"] if latest_sensor else now
            
        seq_scaled = scaler.transform(
            seq_np.reshape(-1, 6)
        ).reshape(1, SEQ_SIZE, 6)

        # 재현
        recon = model.predict(seq_scaled, verbose=0)
        # mae 계산
        mae = float(np.mean(np.abs(recon - seq_scaled)))

        # threshold를 넘는 MAE (이상 데이터)
        over = mae > threshold

        # 이상 데이터가 감지되었다면
        if over:
            # +0.1s
            anomaly_duration += AI_PERIOD
        # 이상 데이터가 복구되었다면    
        else:
            # 초기화
            anomaly_duration = 0.0

        last_ai_result = {
            "ts": now,
            "mae": mae,
            "over_threshold": over,
            "anomaly_duration": round(anomaly_duration, 2),
            "anomaly": anomaly_duration >= ANOMALY_TIME_SEC,
            "lag_ms": int((now - latest_ts) * 1000)
        }
# THREAD 3 : WEBSOCKET SERVER
def ws_thread(server):
    global seq
    
    while True:
        # 30ms (= 센싱 주기)
        time.sleep(0.03)

        payload = {
            "type": "tick",
            "seq": seq,
            "connected": connected,
            "mpu": None,
            "ai": None
        }

        with lock:
            payload["mpu"] = latest_sensor
            payload["ai"] = last_ai_result
        
        seq += 1

        if server.clients:
            server.send_message_to_all(json.dumps(payload))
            
def main():
    server = WebsocketServer(port=WS_PORT)
    print(f"[WS] ws://localhost:{WS_PORT}")

    threading.Thread(target=serial_thread, daemon=True).start()
    threading.Thread(target=ai_thread, daemon=True).start()
    threading.Thread(target=ws_thread, args=(server,), daemon=True).start()

    server.run_forever()

if __name__ == "__main__":
    main()