from robot.robot import dobot
from uart.uart import uart
from vision.vision import RealSenseColorDetector
from modbus.client import ModbusTCPClient
from transform.transform import HandEyeCalibrator
from debug.logger import Logger
import cv2
import threading
import time
logger = Logger("log.txt")
##########MEMO#################
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
transformer = None

# ------------- NOW_STATE --------------
NOW_STATE = "WAIT_START"

# ------------ STATE FLAGS -------------
START_PROCESS_FLAG = False
FINISH_PROCESS_FLAG = False
CLASSIFY_OBJECT_FLAG = False
EMERGENCY_FLAG = False
CONVEYOR_FLAG = False
DETECT_YELLOW_FLAG = False
TURTLEBOT_BUSY_FLAG = False

# -------------- DOBOT VAR --------------
HOME_POS = [209.75, 0, 99.96, 0]
PICK_POS = None
SORT_POS = {
    "RED":     [152.29, 222.28, 33.36, 55.53], # 실측해서 넣자.
    "GREEN":   [152.29, 222.28, 33.36, 55.53], # 실측해서 넣자.
    "BLUE":    [152.29, 222.28, 33.36, 55.53], # 실측해서 넣자.
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

# ------------- EMERGENCY VAR -------------
conveyor_temp = False
cnt = 0

# ------------ Transformer VAR ------------
CALIB_CAM_POINTS = [
    (295, 117, 333),
    (216, 189, 335),
    (338, 104, 330),
    (413, 166, 328),
    (222, 125, 336),
    (193, 184, 336),
    (328, 179, 330),
    (440, 182, 326),
]
CALIB_ROBOT_POINTS = [
    (175.61, -76.88, 28.46),
    (214.46, -121.17, 20.34),
    (169.48, -52.67, 31.51),
    (207.84, -12.8, 28.79),
    (180.6, -120.45, 21.58),
    (208.48, -135.32, 20.15),
    (212.02, -59.71, 30.05),
    (213.31, 2.74, 31.24),
]

# ---------- SETUP FUNCTIONS ----------
def initialize_modbus():
    client = ModbusTCPClient('192.168.110.101', 20000)
    client.connect()
    logger.mlog("INFO", "MODBUS", "Connected to Modbus server")
    return client

def initialize_robot():
    robot = dobot('COM6')
    robot.connect()
    logger.mlog("INFO", "DOBOT", "Connected to Dobot")
    robot.w_home()
    logger.mlog("INFO", "DOBOT", "Dobot homing completed")
    return robot

def initialize_uart():
    comm = uart('COM4', 9600)
    logger.mlog("INFO", "UART", "Connected to STM32 via UART")
    return comm

def initialize_vision():
    vision = RealSenseColorDetector(roi_area=(75, 240, 115, 170))
    logger.mlog("INFO", "D435i", "Connected to D435i")
    return vision

def initialize_transformer(vision):
    transformer = HandEyeCalibrator(vision.intr)
    transformer.calibrate(CALIB_CAM_POINTS, CALIB_ROBOT_POINTS)
    logger.mlog("INFO", "SYSTEM", "Coordinate transformation ready")
    return transformer

# ---------- STATE FUNCTIONS ----------
def wait_start_func():
    global START_PROCESS_FLAG
    logger.mlog("INFO", "SYSTEM", "STATE = WAIT_START")
    while True:
        # 공정 시작 신호가 들어왔다면
        if START_PROCESS_FLAG:
            START_PROCESS_FLAG = False
            return "START_PROCESS"

        yield

def start_process_func():
    logger.mlog("INFO", "SYSTEM", "STATE = START_PROCESS")
    global CONVEYOR_FLAG
    client.conveyor_on()
    CONVEYOR_FLAG = True
    logger.mlog("INFO", "CONVEYOR", "ON")
    yield
    return "DETECT_OBJECT"

def detect_object_func():
    logger.mlog("INFO", "SYSTEM", "STATE = DETECT_OBJECT")
    global last_detected_color
    global yellow_cnt
    global DETECT_YELLOW_FLAG
    global TURTLEBOT_BUSY_FLAG
    global CONVEYOR_FLAG
    global PICK_POS
    
    while True:
        view, detected_color, (u, v, depth) = vision.detect_one_frame()
        yield
        
        if view is not None:
            cv2.imshow("D435i", view)
            # 화면 갱신
            cv2.waitKey(1)
        yield

        # 검출된 색이 있으면서, 동시에 검출된 색이 노란색이 아닐 때
        if detected_color and detected_color != "YELLOW":
            logger.mlog("INFO", "D435i", f"Detected color : {detected_color}")
            client.conveyor_off()
            CONVEYOR_FLAG = False
            logger.mlog("INFO", "CONVEYOR", "OFF")
            last_detected_color = detected_color
            if u is not None and v is not None and depth is not None and depth > 0:
                # PICK_POS 계산
                PICK_POS = transformer.d435i_to_dobot(u, v, depth)
            
            else:
                continue
            
            comm.send(COLOR_CODE[detected_color])
            logger.mlog("INFO", "UART", f"Send({COLOR_CODE[detected_color]})")
            return "WAIT_CLASSIFY"
        
        # 검출된 색이 노란색이라면
        elif detected_color == "YELLOW":
            if not DETECT_YELLOW_FLAG:
                logger.mlog("INFO", "D435i", f"Detected color : {detected_color}")
                yellow_cnt += 1
                DETECT_YELLOW_FLAG = True
            
            if yellow_cnt >= 3:
                if not TURTLEBOT_BUSY_FLAG:
                    yellow_cnt = 0
                    # 출발 예약 (방어코드)
                    TURTLEBOT_BUSY_FLAG = True
                    threading.Thread(
                        target=start_turtlebot,
                        daemon=True
                    ).start()
            yield
            continue
        
        # 검출된 색이 없다면
        else:
            DETECT_YELLOW_FLAG = False
            yield
            continue

def wait_classify_func():
    logger.mlog("INFO", "SYSTEM", "STATE = WAIT_CLASSIFY")
    global CLASSIFY_OBJECT_FLAG
    
    while True:
        if CLASSIFY_OBJECT_FLAG:
            CLASSIFY_OBJECT_FLAG = False
            return "CLASSIFY_OBJECT"
        
        yield
      
def classify_object_func():
    logger.mlog("INFO", "SYSTEM", "STATE = CLASSIFY_OBJECT")
    global step
    global move_sent
    step = 0
    move_sent = False
    
    PICK_WAY_POS = [PICK_POS[0], PICK_POS[1], PICK_POS[2] + 50, 0]
    sort_pos = SORT_POS[last_detected_color]
    sort_way_pos = [sort_pos[0], sort_pos[1], sort_pos[2] + 50, 0]
    
    suction_on_time = None
    
    # Home → PICK_WAY_POS → PICK_POS → SUCTION → PICK_WAY_POS → Home → SORT_WAY_POS → SORT_POS → DROP → SORT_WAY_POS → NEXT_STATE 
    while True:
        # Home
        if step == 0:
            if not move_sent:
                robot.moveJ(*HOME_POS)
                logger.mlog("INFO", "DOBOT", "Moving to home")
                move_sent = True
            
            if robot.is_reached(HOME_POS):
                step = 1
                move_sent = False
            yield
            
        # PICK_WAY_POS
        if step == 1:
            if not move_sent:
                robot.moveJ(*PICK_WAY_POS)
                logger.mlog("INFO", "DOBOT", "Moving to pick_way_pos")
                move_sent = True
            
            if robot.is_reached(PICK_WAY_POS):
                step = 2
                move_sent = False
            yield
            
        # PICK_POS    
        if step == 2:
            if not move_sent:
                robot.moveL(*PICK_POS)
                logger.mlog("INFO", "DOBOT", "Moving to pick_pos")
                move_sent = True
                
            if robot.is_reached(PICK_POS):
                step = 3
                move_sent = False
            yield
        
        # SUCTION
        if step == 3:
            if suction_on_time is None:
                robot.suction(1)
                logger.mlog("INFO", "DOBOT", "Suction")
                suction_on_time = time.time()
            
            if (time.time() - suction_on_time) >= 1.0:
                suction_on_time = None
                step = 4
            yield

        # PICK_WAY_POS
        if step == 4:
            if not move_sent:
                robot.moveL(*PICK_WAY_POS)
                logger.mlog("INFO", "DOBOT", "Moving to pick_way_pos")
                move_sent = True
            
            if robot.is_reached(PICK_WAY_POS):
                step = 5
                move_sent = False
            yield
        
        # Home
        if step == 5:
            if not move_sent:
                robot.moveJ(*HOME_POS)
                logger.mlog("INFO", "DOBOT", "Moving to home")
                move_sent = True
            
            if robot.is_reached(HOME_POS):
                step = 6
                move_sent = False
            yield
        
        # SORT_WAY_POS
        if step == 6:
            if not move_sent:
                robot.moveJ(*sort_way_pos)
                logger.mlog("INFO", "DOBOT", "Moving to sort_way_pos")
                move_sent = True
            
            if robot.is_reached(sort_way_pos):
                step = 7
                move_sent = False
            yield
        
        # SORT_POS
        if step == 7:
            if not move_sent:
                robot.moveL(*sort_pos)
                logger.mlog("INFO", "DOBOT", "Moving to sort_pos")
                move_sent = True
            
            if robot.is_reached(sort_pos):
                step = 8
                move_sent = False
            yield
        
        # DROP
        if step == 8:
            robot.suction(0)
            logger.mlog("INFO", "DOBOT", "Drop")
            step = 9
            yield
        
        # SORT_WAY_POS
        if step == 9:
            if not move_sent:
                robot.moveL(*sort_way_pos)
                logger.mlog("INFO", "DOBOT", "Moving to sort_way_pos")
                move_sent = True
            
            if robot.is_reached(sort_way_pos):
                step = 10
                move_sent = False
            yield
            
        # NEXT_STATE
        if step == 10:
            logger.mlog("INFO", "DOBOT", "Classification task completed")
            return "COMPLETE_TASK"
            
def complete_task_func():
    logger.mlog("INFO", "SYSTEM", "STATE = COMPLETE_TASK")
    global FINISH_PROCESS_FLAG
    global CONVEYOR_FLAG
    comm.send("000")
    logger.mlog("INFO", "UART", "Send(000)")

    yield
    
    if FINISH_PROCESS_FLAG:
        FINISH_PROCESS_FLAG = False
        return "FINISH_PROCESS"
    
    else:
        client.conveyor_on()
        CONVEYOR_FLAG = True
        logger.mlog("INFO", "CONVEYOR", "ON")
        return "DETECT_OBJECT"

def finish_process_func():
    logger.mlog("INFO", "SYSTEM", "STATE = FINISH_PROCESS")
    global START_PROCESS_FLAG
    global FINISH_PROCESS_FLAG
    global step
    global move_sent
    step = 0
    move_sent = False
    
    while True:
        if step == 0:
            if not move_sent:
                robot.home()
                logger.mlog("INFO", "DOBOT", "Moving to home")
                move_sent = True
                
            if robot.is_reached(HOME_POS):
                step = 1
                move_sent = False
            yield
            
        if step == 1:
            cv2.destroyWindow("D435i")
            START_PROCESS_FLAG = False
            FINISH_PROCESS_FLAG = False
            return "WAIT_START"

# ---------- THREAD FUNCTIONS ----------
def stm32_listener():
    global START_PROCESS_FLAG
    global FINISH_PROCESS_FLAG
    global CLASSIFY_OBJECT_FLAG
    global EMERGENCY_FLAG
    global CONVEYOR_FLAG
    
    while True:
        receive_data = comm.receive()
        
        if receive_data:
            if receive_data == "110":
                if NOW_STATE == "WAIT_START" and not EMERGENCY_FLAG:
                    logger.mlog("INFO", "UART", "Receive(110)")
                    START_PROCESS_FLAG = True
            
            elif receive_data == "100":
                if NOW_STATE != "WAIT_START" and NOW_STATE != "FINISH_PROCESS" and not EMERGENCY_FLAG:
                    logger.mlog("INFO", "UART", "Receive(110)")
                    FINISH_PROCESS_FLAG = True
    
                    
            elif receive_data == "101":
                logger.mlog("INFO", "UART", "Receive(101)")
                CLASSIFY_OBJECT_FLAG = True
            
            elif receive_data == "111":
                logger.mlog("INFO", "UART", "Receive(111)")
                logger.mlog("WARN", "SYSTEM", "EMERGENCY ON")
                client.emergency_on()
                EMERGENCY_FLAG = True
            
            elif receive_data == "000":
                logger.mlog("INFO", "UART", "Receive(000)")
                logger.mlog("WARN", "SYSTEM", "EMERGENCY OFF")
                client.emergency_off()
                EMERGENCY_FLAG = False
                    
        time.sleep(0.01)

def monitor_turtlebot():
    global TURTLEBOT_BUSY_FLAG
    while True:
        TURTLEBOT_BUSY_FLAG = client.is_turtlebot_busy()
        time.sleep(0.01)
        
def start_turtlebot():
    time.sleep(2)
    client.send_start_mission()
    logger.mlog("INFO", "TURTLEBOT", "Navigation started")
# -------------- MAIN --------------``
client = initialize_modbus()
robot = initialize_robot()
comm = initialize_uart()
vision = initialize_vision()
transformer = initialize_transformer(vision)

t1 = threading.Thread(target=stm32_listener)
t1.start()
t2 = threading.Thread(target=monitor_turtlebot)
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
    if EMERGENCY_FLAG:
        if NOW_STATE == "CLASSIFY_OBJECT" or NOW_STATE == "FINISH_PROCESS":
            if cnt == 0:
                robot.stop()
                robot.clear()
                robot.start()
                logger.mlog("WARN", "DOBOT", "STOP")
                cnt += 1
                move_sent = False
                time.sleep(0.01)
                continue
            else:
                time.sleep(0.01)
                continue
        else:
            # 컨베이어가 켜져 있었다면
            if CONVEYOR_FLAG:
                client.conveyor_off()
                CONVEYOR_FLAG = False
                logger.mlog("INFO", "CONVEYOR", "OFF")
            time.sleep(0.01)
            continue
            
    try:
        # EMERGENCY CNT 원복
        cnt = 0
        # 컨베이어 상태 원복
        if conveyor_temp == True and CONVEYOR_FLAG == False:
            client.conveyor_on()
            CONVEYOR_FLAG = True
            logger.mlog("INFO", "CONVEYOR", "ON")
        next(current)
        
    except StopIteration as e:
        NOW_STATE = e.value
        current = STATE_FUNCTIONS[NOW_STATE]()
    
    # 컨베이어 상태 저장
    conveyor_temp = CONVEYOR_FLAG
    time.sleep(0.01)
