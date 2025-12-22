import json
import time
import threading
import serial
from websocket_server import WebsocketServer

# ex)
SERIAL_PORT = "COM9"
BAUDRATE = 115200
WS_PORT = 3001
SEND_HZ = 20

# 자물쇠
latest_lock = threading.Lock()
# 가장 최근 시리얼 센서 값
latest_mpu = None
# 가장 최근 ai 추론 결과 값
latest_ai = None
# 웹으로 보낸 메시지 번호
seq = 0
# 시리얼 연결 상태 표시
connected = False

# mpu 값 parse
def parse_mpu_line(line: str):
    parts = line.strip().split(",")

    if len(parts) != 7:
        return None

    # 숫자 변환
    try:
        t_ms = int(parts[0])
        acx = int(parts[1]); acy = int(parts[2]); acz = int(parts[3])
        gyx = int(parts[4]); gyy = int(parts[5]); gyz = int(parts[6])
    except ValueError:
        return None

    return {
        "t_ms": t_ms,
        "pc_ts_ms": int(time.time() * 1000),
        "AcX": acx, "AcY": acy, "AcZ": acz,
        "GyX": gyx, "GyY": gyy, "GyZ": gyz,
        "raw": line.strip(),
    }

# 시리얼로 값 읽기
def serial_thread():
    global latest_mpu, connected
    ser = serial.Serial(SERIAL_PORT, BAUDRATE, timeout=1)
    time.sleep(2)
    connected = True

    while True:
        try:
            b = ser.readline()
            if not b:
                continue

            line = b.decode("utf-8", errors="ignore").strip()
            if not line:
                continue

            # 헤더/START 라인 스킵
            if line == "START":
                continue
            if line.startswith("t,AcX"):
                continue

            mpu = parse_mpu_line(line)
            if mpu is None:
                continue

            with latest_lock:
                latest_mpu = mpu

        except (serial.SerialException, OSError):
            connected = False
            time.sleep(1)
        except Exception:
            continue

# ai 추론과 ws으로 값 보내기 함수
def ai_ws_thread(server):
    global latest_ai, seq
    # 20Hz 사용 - ai 추론 및 웹으로 보내는 주기
    # 0.005s, 50ms
    interval = 1.0 / SEND_HZ
    while True:
        time.sleep(interval)

        # 안정성 위해 Thread Lock
        with latest_lock:
            if latest_mpu is None:
                continue
            mpu = latest_mpu
            
            # ai 추론 함수 정의 필요
            # ai = infer(mpu)
            # latest_ai = ai
            
            # 웹으로 데이터 보내기 위한 데이터 번호
            seq += 1
            payload = {
                # tick -> 주기적으로 날아오는 메시지라는 뜻
                "type": "tick",
                "seq": seq,
                "connected": connected,
                "mpu": mpu,
                # ai 추론 결과도 같이 보내면 좋겠음
                # "ai": ai
            }

        # 락 밖에서 전송
        if server.clients:
            server.send_message_to_all(json.dumps(payload))


def main():
    server = WebsocketServer(port=WS_PORT)
    threading.Thread(target=serial_thread, daemon=True).start()
    threading.Thread(target=ai_ws_thread, args=(server,), daemon=True).start()
    print(f"WS on ws://localhost:{WS_PORT}")
    server.run_forever()

if __name__ == "__main__":
    main()