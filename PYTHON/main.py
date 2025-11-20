from robot.robot import dobot
from uart.uart import uart
from vision.vision import RealSenseColorDetector
from modbus.client import ModbusTCPClient
import threading
import time

#################### STATE 정의 ####################
STATE_MAP = {
    0: "WAIT_START",
    1: "DETECT_OBJECT",
    2: "PROCESS_OBJECT",
    3: "DOBOT_WORK",
    4: "FINISH_WORK",
    5: "EMERGENCY_ON",
    6: "EMERGENCY_OFF",
}
NOW_STATE = 0
###################################################

#################### 기본 세팅부 ####################
# Modbus 연결
# client = ModbusTCPClient('IP', 'PORT_NUMBER')
# client.connect()

# Dobot 초기화
robot = dobot('COM6')
robot.connect()
robot.home()

# UART 연결
comm = uart('COM4', 9600)

# D435i 연결
vision = RealSenseColorDetector(roi_area=(230, 280, 425, 475))
###################################################

################## RECEIVE THREAD ##################
SIGNAL_MAP = {
    "110": "PROCESS_START",
    "101": "WORK_START",
    "111": "EMERGENCY_ON",
    "000": "EMERGENCY_OFF",
}

def stm32_listener():
    print("[UART] STM32_LISTENER THREAD STARTED!")
    global NOW_STATE
    
    # 무한 반복
    while True:
        receive_data = comm.receive()
        
        # STM32로부터 데이터를 받았다면
        if receive_data:
            if receive_data in SIGNAL_MAP:
                signal = SIGNAL_MAP[receive_data]
                
                # 공정 시작 신호
                if signal == "PROCESS_START":
                    print("[UART] PROCESS_START(110) Received from STM32")
                    NOW_STATE = STATE_MAP[1]
                
                # 작업 시작 신호
                elif signal == "WORK_START":
                    print("[UART] WORK_START(101) Received from STM32")
                    NOW_STATE = STATE_MAP[3]
                
                # 비상 상황 발생 신호
                elif signal == "EMERGENCY_ON":
                    print("[UART] EMERGENCY_ON(111) Received from STM32")
                    NOW_STATE = STATE_MAP[5]
                
                # 비상 상황 종료 신호
                elif signal == "EMERGENCY_OFF":
                    print("[UART] EMERGENCY_OFF(000) Received from STM32")
                    NOW_STATE = STATE_MAP[6]
####################################################





