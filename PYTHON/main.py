from robot.robot import dobot
from uart.uart import uart
from vision.vision import RealSenseColorDetector
from modbus.client import ModbusTCPClient
import cv2
import threading
import time

#################### MEMO ######################
'''
0. 컨베이어 벨트, Turtlebot3 ROS2 추가
1. 모드버스 IP, PORT 바꿔야함
2. 스레드 부분, receive_data 상태 갱신하고 None으로 바뀌는지 확인
3. 모드버스 구조 생각해서, 모드버스 write도 구현하자
4. PICK_POSITION 실제로 측정해서 고치자
5. SORT_POSITION 실제로 측정해서 고치자
6. 현재 COMPLETE_TASK → DETECT_OBJECT로 돌아오고 있는 상황인데 STM32가 컨베이어 벨트를 반드시 ON했다는 보장이 없다.
'''
################################################

#################### DEFINE ####################
NOW_STATE = "WAIT_SIGNAL"
COLOR_CODE = {
    "RED": "001",
    "GREEN": "010",
    "BLUE": "011",
    "YELLOW": "100",
}
PICK_POSITION = (200, 100, -40, 0)
SORT_POSITION = {
    "RED":     (300, 50, -30, 0),
    "GREEN":   (300, 150, -30, 0),
    "BLUE":    (300, 250, -30, 0),
    "YELLOW":  (300, 350, -30, 0),
}
last_detected_color = None
'''''''''''''''''''''''''''''''''''''''''''''''''''
대기 상태 : WAIT_SIGNAL
공정 시작 : START_PROCESS
공정 종료 : FINISH_PROCESS
물체 탐지 : DETECT_OBJECT
물체 분류 : CLASSIFY_OBJECT
작업 완료 : COMPLETE_TASK
비상 시작 : EMERGENCY_ON
비상 종료 : EMERGENCY_OFF
'''''''''''''''''''''''''''''''''''''''''''''''''''
###################################################

#################### SETUP ####################
# Modbus 연결
client = ModbusTCPClient('255.255.255.0', 'PORT_NUMBER')
client.connect()
print("[MODBUS] Client connected successfully.")

# Dobot 초기화
robot = dobot('COM6')
robot.connect()
robot.home()
print("[DOBOT] Device connected successfully.")

# UART 연결
comm = uart('COM4', 9600)
print("[UART] Device connected successfully.")

# D435i 연결
vision = RealSenseColorDetector(roi_area=(230, 280, 425, 475))
print("[D435i] Device connected successfully.")
###################################################

################## THREAD ##################
def stm32_listener():
    print("[UART] stm32_listener thread started!")
    global NOW_STATE
    
    while True:
        receive_data = comm.receive()
        
        if receive_data:
            if receive_data == "110":
                    print("[UART] Received: START_PROCESS(110) from STM32.")
                    NOW_STATE = "START_PROCESS"
            
            elif receive_data == "101":
                    print("[UART] Received: CLASSIFY_OBJECT(101) from STM32.")
                    NOW_STATE = "CLASSIFY_OBJECT"
            
            elif receive_data == "111":
                    print("[UART] Received: EMERGENCY_ON(111) from STM32.")
                    NOW_STATE = "EMERGENCY_ON"
            
            elif receive_data == "000":
                    print("[UART] Received: EMERGENCY_OFF(000) from STM32.")
                    NOW_STATE = "EMERGENCY_OFF"
                    
        time.sleep(0.01)
####################################################

################## MAIN ##################
t = threading.Thread(target=stm32_listener)
t.start()

while True:
    if NOW_STATE == "WAIT_SIGNAL":
        pass
    
    elif NOW_STATE == "START_PROCESS":
        NOW_STATE = "DETECT_OBJECT"
        
    elif NOW_STATE == "DETECT_OBJECT":
        view, detected_color = vision.detect_one_frame()
        
        if view is not None:
            cv2.imshow("D435i", view)
            cv2.waitKey(1)
        
        if detected_color:
            print(f"[D435i] Detected: {detected_color}")
            last_detected_color = detected_color        
            comm.send(COLOR_CODE[detected_color])
            cv2.destroyWindow("D435i")
            
            NOW_STATE = "WAIT_SIGNAL"

    elif NOW_STATE == "CLASSIFY_OBJECT":
        print(f"[DOBOT] Start PICK & SORT")
        
        robot.move(*PICK_POSITION)
        robot.suction(1)
        
        sort_pos = SORT_POSITION[last_detected_color]
        robot.move(*sort_pos)
        robot.suction(0)
        
        NOW_STATE = "COMPLETE_TASK"
        
    elif NOW_STATE == "COMPLETE_TASK":
        print(f"[DOBOT] Task Completed")
        comm.send("000")
        
        NOW_STATE = "DETECT_OBJECT"
        
    elif NOW_STATE == "EMERGENCY_ON":
        pass
    elif NOW_STATE == "EMERGENCY_OFF":
        pass
    elif NOW_STATE == "FINISH_PROCESS":
        pass
    
    time.sleep(0.01)
##########################################




