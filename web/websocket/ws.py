import json
import time
import threading
import serial
from collections import deque
from queue import Queue

import numpy as np
import joblib
from keras.models import load_model
from websocket_server import WebsocketServer

SERIAL_PORT = "COM9"
BAUDRATE = 115200

WS_PORT = 3001

SENSOR_INTERVAL = 0.03 # 30ms
SEQ_SIZE = 30

FEATURE_NAMES = ["AcX", "AcY", "AcZ", "GyX", "GyY", "GyZ"]

ANOMALY_SEQ_THRESHOLD = 30

MODEL_PATH = "LSTM_AutoEncoder_MPU6050.h5"
SCALER_PATH = "mpu6050_scaler.pkl"
THRESHOLD_PATH = "mpu6050_threshold.npy"

# 센서 이벤트 기반 트리거
sensor_queue = Queue()
ai_event_queue = Queue()

mpu_buffer = deque(maxlen=SEQ_SIZE)

latest_sensor = None
connected = False
seq = 0

anomaly_count = 0
lock = threading.Lock()

print("[AI] Loading model...")
model = load_model(MODEL_PATH)
scaler = joblib.load(SCALER_PATH)
threshold = float(np.load(THRESHOLD_PATH))
print(f"[AI] Threshold = {threshold:.6f}")

def is_emergency():
    # TODO: Modbus coil 연동해야된다.
    return False

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

# THREAD 1: SERIAL COLLECTOR (30ms)
def serial_thread():
    global connected, latest_sensor
    
    ser = serial.Serial(SERIAL_PORT, BAUDRATE, timeout=1)
    time.sleep(2)
    connected = True
    print("[SERIAL] Connected")
    
    while True:
        try:
            line = ser.readline().decode(errors="ignore").strip()
            if not line or line == "START" or line.startswith("t,AcX"):
                continue
            
            data = parse_mpu_line(line)
            if data is None:
                continue
            
            with lock:
                latest_sensor = data
            
            sensor_queue.put(data)
        
        except Exception as e:
            print("[SERIAL ERROR]", e)
            connected = False
            time.sleep(1)

# THREAD 2: AI INFERENCE (센서 이벤트 기반)
def ai_thread():
    global anomaly_count
    
    while True:
        sensor = sensor_queue.get()
        
        if is_emergency():
            mpu_buffer.clear()
            anomaly_count = 0
            continue
        
        mpu_buffer.append([
            sensor[k] for k in FEATURE_NAMES
        ])
        
        if len(mpu_buffer) < SEQ_SIZE:
            continue
        
        seq_np = np.array(mpu_buffer).reshape(1, SEQ_SIZE, 6)
        seq_scaled = scaler.transform(
            seq_np.reshape(-1, 6)
        ).reshape(1, SEQ_SIZE, 6)

        recon = model.predict(seq_scaled, verbose=0)
        mae = float(np.mean(np.abs(recon - seq_scaled)))
        
        over = mae > threshold
        anomaly_count = anomaly_count + 1 if over else 0
        
        ai_event_queue.put({
            "ts": time.time(),
            "mae": mae,
            "over_threshold": over,
            "anomaly_count": anomaly_count,
            "anomaly": anomaly_count >= ANOMALY_SEQ_THRESHOLD
        })

# THREAD 3: WEBSOCKET SENDER
def ws_thread(server):
    global seq
    
    while True:
        time.sleep(0.01)
        
        payload = {
            "type": "tick",
            "seq": seq,
            "connected": connected,
            "sensor": None,
            "ai": None,
        }
        
        with lock:
            payload["sensor"] = latest_sensor

        if not ai_event_queue.empty():
            payload["ai"] = ai_event_queue.get()

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