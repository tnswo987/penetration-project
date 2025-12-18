# -*- coding: utf-8 -*-
import gpiod
import time
import threading

from pymodbus.client import ModbusTcpClient

# GPIO & 모터 설정
DIR_PIN = 17
STEP_PIN = 27
ENABLE_PIN = 22

chip = gpiod.Chip('gpiochip0')

dir_line = chip.get_line(DIR_PIN)
step_line = chip.get_line(STEP_PIN)
enable_line = chip.get_line(ENABLE_PIN)

dir_line.request(consumer="dir", type=gpiod.LINE_REQ_DIR_OUT)
step_line.request(consumer="step", type=gpiod.LINE_REQ_DIR_OUT)
enable_line.request(consumer="enable", type=gpiod.LINE_REQ_DIR_OUT)

# 컨베이어는 한 방향으로만 돈다고 가정 (DIR=0 이 CW)
dir_line.set_value(1)

# 변수
state = 0              # Modbus에서 받은 원본 값 (0 또는 1)
target_running = False # "돌아야 한다/멈춰야 한다" 목표 상태
motor_running = False  # 실제로 현재 도는 중인지

TargetSpeed = 0.0005 * 2   # 최종 빠른 속도
InitialSpeed = 0.0005 * 2  # 시작/정지 속도
Speed = InitialSpeed
RATIO = 0.0000001 * 2      # 가속/감속 시 한 스텝마다 조절할 양

lock = threading.Lock()  # state/target_running 보호용

# 1. 모터 스텝 쓰레드
def step_motor_thread():
    global target_running, motor_running, Speed

    # 시작 시 모터 비활성
    enable_line.set_value(1)  # 드라이버 비활성

    while True:
        with lock:
            should_run = target_running

        if should_run:
            # 컨베이어를 돌려야 하는 상태
            enable_line.set_value(0)  # 드라이버 활성

            # 가속: Speed 값을 TargetSpeed까지 줄이기
            if Speed > TargetSpeed:
                Speed -= RATIO
                if Speed < TargetSpeed:
                    Speed = TargetSpeed

            motor_running = True

        else:
            # 컨베이어를 멈춰야 하는 상태
            if motor_running:
                # 감속: Speed를 InitialSpeed까지 키우기
                if Speed < InitialSpeed:
                    Speed += RATIO
                else:
                    # 충분히 느려졌으면 완전히 정지
                    Speed = InitialSpeed
                    motor_running = False
                    enable_line.set_value(1)  # 모터 Disable
            else:
                # 이미 정지 상태면 잠깐 쉬고 다음 루프로
                time.sleep(0.02)
                continue

        # 실제 스텝 펄스
        if motor_running:
            step_line.set_value(1)
            time.sleep(Speed)
            step_line.set_value(0)
            time.sleep(Speed)
        else:
            # 감속 완료 후 완전 정지 상태
            time.sleep(0.02)

# 2. Modbus 읽기 쓰레드
def modbus_read_thread():
    global state, target_running

    client = ModbusTcpClient('192.168.110.101', port=20000)
    UNIT_ID = 1   # slave id
    COIL_ADDR = 0 # 0번 coil 사용

    while True:
        if not client.connected:
            print("Trying to connect Modbus server...")
            if not client.connect():
                print("Modbus connect failed. Retry in 2 seconds.")
                time.sleep(2)
                continue
            else:
                print("Modbus connected.")

        try:
            # coil 0번을 1개 읽기
            rr = client.read_coils(COIL_ADDR, 1, slave=UNIT_ID)

            if rr.isError():
                print(f"Modbus error: {rr}")
            else:
                value = rr.bits[0]  # True/False
                with lock:
                    state = 1 if value else 0
                    target_running = (state == 1)

        except Exception as e:
            print(f"Modbus exception: {e}")
            client.close()

        time.sleep(0.03)

# 메인
if __name__ == "__main__":
    motor_thread = threading.Thread(target=step_motor_thread, daemon=True)
    modbus_thread = threading.Thread(target=modbus_read_thread, daemon=True)

    motor_thread.start()
    modbus_thread.start()

    try:
        while True:
            # 상태 한 번씩 찍어보고 싶으면:
            # with lock:
            #     print(f"[DEBUG] state={state}, target_running={target_running}, motor_running={motor_running}, Speed={Speed:.7f}")
            time.sleep(1)
    except KeyboardInterrupt:
        print("Program terminated by user")
    finally:
        with lock:
            target_running = False
            motor_running = False
        time.sleep(0.2)

        enable_line.set_value(1)
        dir_line.release()
        step_line.release()
        enable_line.release()
        chip.close()
