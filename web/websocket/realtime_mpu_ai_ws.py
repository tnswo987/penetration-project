import json
import time
import threading
import serial
from collections import deque
from queue import Queue, Empty

import numpy as np
import joblib
from keras.models import load_model
from websocket_server import WebsocketServer

SERIAL_PORT = "COM9"
BAUDRATE = 115200

WS_PORT = 3001

SEQ_SIZE = 30
FEATURES = ["AcX", "AcY", "AcZ", "GyX", "GyY", "GyZ"]

ANOMALY_COUNT_TH = 30

MODEL_PATH = "LSTM_AutoEncoder_MPU6050.h5"
SCALER_PATH = "mpu6050_scaler.pkl"
THRESHOLD_PATH = "mpu6050_threshold.npy"

latest_lock = threading.Lock()

connected = False
seq = 0

mpu_buffer = deque(maxlen=SEQ_SIZE)

anomaly_count = 0
anomaly_detected = False

ai_event_queue = Queue(maxsize=10000)