from robot.robot import dobot
from uart.uart import uart
from vision.vision import RealSenseColorDetector
from modbus.client import ModbusTCPClient
import cv2
import threading
import time
##########MEMO#################
'''
1. FINISH_PROCESS 부분에서 HOMING EMERGENCY 가능한지 CHECK
2. 
'''
###############################
'''
시작 대기 : WAIT_START
공정 시작 : START_PROCESS
공정 종료 : FINISH_PROCESS
물체 탐지 : DETECT_OBJECT
분류 대기 : WAIT_CLASSIFY
물체 분류 : CLASSIFY_OBJECT
작업 완료 : COMPLETE_TASK
비상 시작 : EMERGENCY_ON
비상 종료 : EMERGENCY_OFF
'''

# ---------- SYSTEM COMPONENTS ----------
client = None
vision = None
robot = None
comm = None

# ------------- NOW_STATE --------------
NOW_STATE = "WAIT_START"

# ------------ STATE FLAGS -------------
START_PROCESS_FLAG = False
FINISH_PROCESS_FLAG = False
CLASSIFY_OBJECT_FLAG = False
EMERGENCY_FLAG = False

# -------------- DOBOT VAR --------------
HOME_POSITION = [209.75, 0, 99.96, 0]
PICK_POSITION_1 = [141.87, -233.48, 87.7, -53.06]
PICK_POSITION_2 = [121.78, -257.6, 20.84, -64.7]
SORT_POSITION = {
    "RED":     [251.84, 66.75, -18.93, 14.84],
    "GREEN":   [256.83, -7.62, -17.89, -1.7],
    "BLUE":    [241.76, -86.3, -18.49, -19.65],
}
step = 0
move_sent = False

# -------------- D435i VAR --------------
COLOR_CODE = {
    "RED": "001",
    "BLUE": "011",
    "GREEN": "010",
}
last_detected_color = None

# -------------- TURTLE VAR --------------
yellow_cnt = 0
turtlebot_busy = False

# ------------- EMERGENCY VAR -------------
temp = None
cnt = 0

# ---------- SETUP FUNCTIONS ----------
def initialize_modbus():
    client = ModbusTCPClient('192.168.110.101', 20000)
    client.connect()
    client.write_log("[MODBUS] 서버와의 연결이 완료되었습니다.")
    print("[MODBUS] 서버와의 연결이 완료되었습니다.")
    return client

def initialize_robot(client):
    robot = dobot('COM6')
    robot.connect()
    robot.home()
    client.write_log("[DOBOT] 장치 연결이 완료되었습니다.")
    print("[DOBOT] 장치 연결이 완료되었습니다.")
    return robot

def initialize_uart(client):
    comm = uart('COM4', 9600)
    client.write_log("[UART] 장치 연결이 완료되었습니다.")
    print("[UART] 장치 연결이 완료되었습니다.")
    return comm

def initialize_vision(client):
    vision = RealSenseColorDetector(roi_area=(230, 280, 425, 475))
    client.write_log("[D435i] 장치 연결이 완료되었습니다.")
    print("[D435i] 장치 연결이 완료되었습니다.")
    return vision

# ---------- STATE FUNCTIONS ----------
def wait_start_func():
    global START_PROCESS_FLAG
    
    while True:
        if START_PROCESS_FLAG:
            client.write_log("[SYSTEM] 공정 시작")
            print("[SYSTEM] 공정 시작")
            START_PROCESS_FLAG = False
            return "START_PROCESS"
                
        yield

def start_process_func():
    client.conveyor_on()
    yield
    return "DETECT_OBJECT"

def detect_object_func():
    global last_detected_color
    global yellow_cnt
    global turtlebot_busy
    
    while True:
        view, detected_color = vision.detect_one_frame()
        yield
        
        if view is not None:
            cv2.imshow("D435i", view)
            cv2.waitKey(1)
        yield

        if detected_color and detected_color != "YELLOW":
            client.conveyor_off()
            client.write_log(f"[D435i] {detected_color} 탐지")
            print(f"[D435i] {detected_color} 탐지")
            last_detected_color = detected_color
            comm.send(COLOR_CODE[detected_color])
            return "WAIT_CLASSIFY"
        
        elif detected_color == "YELLOW":
            if turtlebot_busy:
                yield
                continue
            
            yellow_cnt += 1
            client.write_log(f"[D435i] YELLOW : {yellow_cnt}")
            print(f"[D435i] YELLOW : {yellow_cnt}")
            
            if yellow_cnt >= 3:
                yellow_cnt = 0
                threading.Thread(target=delayed_turtlebot_start).start()
            
            yield
            continue
        
        else:
            yield
            continue

def wait_classify_func():
    global CLASSIFY_OBJECT_FLAG
    
    while True:
        if CLASSIFY_OBJECT_FLAG:
            CLASSIFY_OBJECT_FLAG = False
            return "CLASSIFY_OBJECT"
        
        yield
      
def classify_object_func():
    global step
    global move_sent
    step = 0
    move_sent = False
    client.write_log("[DOBOT] 분류 작업을 시작합니다.")
    print("[DOBOT] 분류 작업을 시작합니다.")
    
    while True:
        if step == 0:
            if not move_sent:
                robot.move(*PICK_POSITION_1)
                move_sent = True
            
            if robot.is_reached(PICK_POSITION_1):
                step = 1
                move_sent = False
            yield
            
        if step == 1:
            if not move_sent:
                robot.move(*PICK_POSITION_2)
                move_sent = True
                
            pose = robot.get_pose()
            if robot.is_reached(PICK_POSITION_2):
                step = 2
                move_sent = False 
            yield
        
        if step == 2:
            robot.suction(1)
            time.sleep(0.5)
            step = 3
            yield
            
        if step == 3:
            if not move_sent:
                robot.move(*PICK_POSITION_1)
                move_sent = True
            
            pose = robot.get_pose()
            if robot.is_reached(PICK_POSITION_1):
                step = 4
                move_sent = False
            yield
            
        if step == 4:
            if not move_sent:
                sort_pos = SORT_POSITION[last_detected_color]
                robot.move(*sort_pos)
                move_sent = True
            
            if robot.is_reached(sort_pos):
                step = 5
                move_sent = False
            yield
            
        if step == 5:
            robot.suction(0)
            step = 6
            yield
        
        if step == 6:
            return "COMPLETE_TASK"
            
def complete_task_func():
    global FINISH_PROCESS_FLAG
    comm.send("000")
    client.write_log("[DOBOT] 분류 작업을 완료하였습니다.")
    print(f"[DOBOT] 분류 작업을 완료하였습니다.")
        
    yield
    
    if FINISH_PROCESS_FLAG:
        FINISH_PROCESS_FLAG = False
        return "FINISH_PROCESS"
    
    else:
        client.conveyor_on()
        return "DETECT_OBJECT"

def finish_process_func():
    global step
    global move_sent
    step = 0
    move_sent = False
    
    client.write_log("[SYSTEM] 공정 종료")
    print("[SYSTEM] 공정 종료")
    
    while True:
        if step == 0:
            if not move_sent:
                robot.home()
                move_sent = True
                
            if robot.is_reached(HOME_POSITION):
                step = 1
                move_sent = False 
            yield
            
        if step == 1:
            cv2.destroyWindow("D435i")
            client.export_logs()
            return "WAIT_START"

# ---------- THREAD FUNCTIONS ----------
def stm32_listener():
    print("[UART] STM32 수신 스레드를 시작합니다.")
    
    global START_PROCESS_FLAG
    global FINISH_PROCESS_FLAG
    global CLASSIFY_OBJECT_FLAG
    global EMERGENCY_FLAG
    global step
    global temp
    global cnt
    
    while True:
        receive_data = comm.receive()
        
        if receive_data:
            if receive_data == "110":
                if NOW_STATE == "WAIT_START":
                    client.write_log("[UART] STM32로부터 START_PROCESS(110) 신호를 수신했습니다.")
                    print("[UART] STM32로부터 START_PROCESS(110) 신호를 수신했습니다.")
                    START_PROCESS_FLAG = True
            
            elif receive_data == "100":
                if NOW_STATE != "WAIT_START":
                    client.write_log("[UART] STM32로부터 FINISH_PROCESS(100) 신호를 수신했습니다.")
                    print("[UART] STM32로부터 FINISH_PROCESS(100) 신호를 수신했습니다.")
                    FINISH_PROCESS_FLAG = True
                    
            elif receive_data == "101":
                client.write_log("[UART] STM32로부터 CLASSIFY_OBJECT(101) 신호를 수신했습니다.")
                print("[UART] STM32로부터 CLASSIFY_OBJECT(101) 신호를 수신했습니다.")
                CLASSIFY_OBJECT_FLAG = True
            
            elif receive_data == "111":
                client.write_log("[UART] STM32로부터 EMERGENCY_ON(111) 신호를 수신했습니다.")
                print("[UART] STM32로부터 EMERGENCY_ON(111) 신호를 수신했습니다.")
                temp = step
                EMERGENCY_FLAG = True
            
            elif receive_data == "000":
                client.write_log("[UART] STM32로부터 EMERGENCY_OFF(000) 신호를 수신했습니다.")
                print("[UART] STM32로부터 EMERGENCY_OFF(000) 신호를 수신했습니다.")
                step = temp
                cnt = 0
                EMERGENCY_FLAG = False
                    
        time.sleep(0.01)

def delayed_turtlebot_start():
    global turtlebot_busy
    
    DELAY_TIME = 1.5
    time.sleep(DELAY_TIME)
    
    client.turtlebot_start()
    print("[TURTLE] TURTLEBOT 출발")
    client.write_log("[TURTLE] TURTLEBOT 출발")
    turtlebot_busy = True

def turtlebot_monitor():
    global turtlebot_busy
    
    while True:
        result = client.read_turtlebot_status()
        
        if result == False and turtlebot_busy == True:
            turtlebot_busy = False
            print("[TURTLE] TURTLEBOT 복귀")
            client.write_log("[TURTLE] TURTLEBOT 복귀")
        
        time.sleep(0.1)
# -------------- MAIN --------------
client = initialize_modbus()
robot = initialize_robot(client)
comm = initialize_uart(client)
vision = initialize_vision(client)
    
t1 = threading.Thread(target=stm32_listener)
t1.start()
t2 = threading.Thread(target=turtlebot_monitor)
t2.start()

STATE_FUNCTIONS = {
    "WAIT_START": wait_start_func,
    "START_PROCESS": start_process_func,
    "FINISH_PROCESS": finish_process_func,
    "DETECT_OBJECT": detect_object_func,
    "WAIT_CLASSIFY": wait_classify_func,
    "CLASSIFY_OBJECT": classify_object_func,
    "COMPLETE_TASK": complete_task_func,
}

current = STATE_FUNCTIONS[NOW_STATE]()

while True:
    if EMERGENCY_FLAG and cnt == 0:
        robot.stop()
        robot.clear()
        cnt += 1
        move_sent = False
        time.sleep(0.01)
        continue
        
    if EMERGENCY_FLAG and cnt == 1:
        robot.start()
        cnt += 1
        time.sleep(0.01)
        continue
    
    if EMERGENCY_FLAG and cnt > 1:
        time.sleep(0.01)
        continue
    
    try:
        next(current)
        
    except StopIteration as e:
        NOW_STATE = e.value
        current = STATE_FUNCTIONS[NOW_STATE]()
            
    time.sleep(0.01)




