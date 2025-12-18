from robot.robot import dobot
from uart.uart import uart
from vision.vision import RealSenseColorDetector
from modbus.client import ModbusTCPClient
from transform.transform import HandEyeCalibrator
from debug.logger import Logger
import cv2
import threading
import time
logger = Logger("debug.txt")
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
    logger.log("[initialize_modbus()] 모드버스 서버 접속 완료")
    return client

def initialize_robot():
    robot = dobot('COM6')
    robot.connect()
    robot.w_home()
    logger.log("[initialize_robot()] Dobot 연결 및 Homing 완료")
    return robot

def initialize_uart():
    comm = uart('COM4', 9600)
    logger.log("[initialize_uart()] UART 연결 완료")
    return comm

def initialize_vision():
    vision = RealSenseColorDetector(roi_area=(75, 240, 115, 170))
    logger.log("[initialize_vision()] D435i 연결 완료")
    return vision

def initialize_transformer(vision):
    transformer = HandEyeCalibrator(vision.intr)
    transformer.calibrate(CALIB_CAM_POINTS, CALIB_ROBOT_POINTS)
    logger.log("[initialize_transformer()] 변환 행렬 준비 완료")
    return transformer

# ---------- STATE FUNCTIONS ----------
def wait_start_func():
    global START_PROCESS_FLAG
    logger.log("[wait_start_func()] wait_start_func()에 들어왔습니다.")
    logger.log("[wait_start_func()] START_PROCESS_FLAG를 기다립니다.")
    while True:
        # 공정 시작 신호가 들어왔다면
        if START_PROCESS_FLAG:
            logger.log("[wait_start_func()] START_PROCESS_FLAG를 받아서 if문 안으로 들어왔습니다.")
            START_PROCESS_FLAG = False
            logger.log(f"[wait_start_func()] START_PROCESS_FLAG를 False로 원복했습니다. START_PROCESS_FLAG : {START_PROCESS_FLAG}")
            logger.log("[wait_start_func()] WAIT_START → START_PROCESS")
            return "START_PROCESS"

        yield

def start_process_func():
    logger.log("[start_process_func()] start_process_func()에 들어왔습니다.")
    global CONVEYOR_FLAG
    client.conveyor_on()
    CONVEYOR_FLAG = True
    logger.log(f"[start_process_func()] 컨베이어 ON / CONVEYOR_FLAG : {CONVEYOR_FLAG}")
    yield
    logger.log("[start_process_func()] START_PROCESS → DETECT_OBJECT")
    return "DETECT_OBJECT"

def detect_object_func():
    logger.log("[detect_object_func()] detect_object_func()에 들어왔습니다.")
    logger.log("[detect_object_func()] 물체의 색상 탐지를 시작합니다.")
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
            logger.log(f"[detect_object_func()] 색상을 탐지하였습니다 detected_color : {detected_color}")
            client.conveyor_off()
            CONVEYOR_FLAG = False
            logger.log(f"[detect_object_func()] 컨베이어 OFF / CONVEYOR_FLAG : {CONVEYOR_FLAG}")
            last_detected_color = detected_color
            logger.log(f"[detect_object_func()] last_detected_color에 검출된 색을 저장합니다. last_detected_color : {last_detected_color}")
            if u is not None and v is not None and depth is not None and depth > 0:
                # PICK_POS 계산
                PICK_POS = transformer.d435i_to_dobot(u, v, depth)
                logger.log(f"[detect_object_func()] 계산된 PICK_POS: {PICK_POS}")
            
            else:
                continue
            
            logger.log(f"[detect_object_func()] STM32에게 COLOR_CODE를 보냅니다. COLOR_CODE : {COLOR_CODE[detected_color]}")
            comm.send(COLOR_CODE[detected_color])
            logger.log("[detect_object_func()] DETECT_OBJECT → WAIT_CLASSIFY")
            return "WAIT_CLASSIFY"
        
        # 검출된 색이 노란색이라면
        elif detected_color == "YELLOW":
            if not DETECT_YELLOW_FLAG:
                logger.log("[detect_object_func()] 노란색 물체를 탐지하였습니다.")
                yellow_cnt += 1
                logger.log(f"[detect_object_func()] yellow_cnt : {yellow_cnt}")
                DETECT_YELLOW_FLAG = True
                logger.log(f"[detect_object_func()] 중복 방지를 위해 DETECT_YELLOW_FLAG를 True로 변경합니다. DETECT_YELLOW_FLAG : {DETECT_YELLOW_FLAG}")
            
            if yellow_cnt >= 3:
                logger.log(f"[detect_object_func()] 노란색 물체를 3개 탐지하였습니다. yellow_cnt : {yellow_cnt}")
                if not TURTLEBOT_BUSY_FLAG:
                    logger.log(f"[detect_object_func()] 터틀봇은 Home 위치에 있으므로 작업 명령을 내릴 준비를 합니다. TURTLEBOT_BUSY_FLAG : {TURTLEBOT_BUSY_FLAG}")
                    yellow_cnt = 0
                    logger.log(f"[detect_object_func()] yellow_cnt를 초기화합니다. yellow_cnt : {yellow_cnt}")
                    # 출발 예약 (방어코드)
                    TURTLEBOT_BUSY_FLAG = True
                    logger.log(f"[detect_object_func()] 방어적으로 TURTLEBOT_BUSY_FLAG를 True로 변경합니다. TURTLEBOT_BUSY_FLAG : {TURTLEBOT_BUSY_FLAG}")
                    logger.log(f"[detect_object_func()] 터틀봇에게 명령을 내리기 위한 스레드를 시작합니다.")
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
    logger.log("[wait_classify_func()] wait_classify_func()에 들어왔습니다.")
    logger.log("[wait_classify_func()] CLASSIFY_OBJECT_FLAG를 기다립니다.")
    global CLASSIFY_OBJECT_FLAG
    
    while True:
        if CLASSIFY_OBJECT_FLAG:
            logger.log("[wait_classify_func()] CLASSIFY_OBJECT_FLAG를 받아서 if문 안으로 들어왔습니다.")
            CLASSIFY_OBJECT_FLAG = False
            logger.log(f"[wait_classify_func()] CLASSIFY_OBJECT_FLAG를 False로 원복했습니다. CLASSIFY_OBJECT_FLAG : {CLASSIFY_OBJECT_FLAG}")
            logger.log("[wait_classify_func()] WAIT_CLASSIFY → CLASSIFY_OBJECT")
            return "CLASSIFY_OBJECT"
        
        yield
      
def classify_object_func():
    global step
    global move_sent
    step = 0
    move_sent = False
    
    logger.log("[classify_object_func()] classify_object_func()에 들어왔습니다.")
    logger.log(f"[classify_object_func()] step : {step} / move_sent : {move_sent}")
    PICK_WAY_POS = [PICK_POS[0], PICK_POS[1], PICK_POS[2] + 50, 0]
    logger.log(f"[classify_object_func()] PICK_WAY_POS : {PICK_WAY_POS}")
    sort_pos = SORT_POS[last_detected_color]
    logger.log(f"[classify_object_func()] sort_pos : {sort_pos}")
    sort_way_pos = [sort_pos[0], sort_pos[1], sort_pos[2] + 50, 0]
    logger.log(f"[classify_object_func()] sort_way_pos : {sort_way_pos}")
    
    suction_on_time = None
    logger.log(f"[classify_object_func()] suction_on_time : {suction_on_time}")
    
    # Home → PICK_WAY_POS → PICK_POS → SUCTION → PICK_WAY_POS → Home → SORT_WAY_POS → SORT_POS → DROP → SORT_WAY_POS → NEXT_STATE 
    while True:
        # Home
        if step == 0:
            if not move_sent:
                logger.log(f"[classify_object_func()] moveJ(HOME_POS) step : {step}")
                robot.moveJ(*HOME_POS)
                move_sent = True
                logger.log(f"[classify_object_func()] move_sent를 True로 변경합니다. move_sent : {move_sent}")
            
            if robot.is_reached(HOME_POS):
                logger.log(f"[classify_object_func()] HOME_POS에 도착했습니다.")
                step = 1
                move_sent = False
                logger.log(f"[classify_object_func()] step, move_sent를 변경합니다. step : {step} / move_sent : {move_sent}")
            yield
            
        # PICK_WAY_POS
        if step == 1:
            if not move_sent:
                logger.log(f"[classify_object_func()] moveJ(PICK_WAY_POS) step : {step}")
                robot.moveJ(*PICK_WAY_POS)
                move_sent = True
                logger.log(f"[classify_object_func()] move_sent를 True로 변경합니다. move_sent : {move_sent}")
            
            if robot.is_reached(PICK_WAY_POS):
                logger.log(f"[classify_object_func()] PICK_WAY_POS에 도착했습니다.")
                step = 2
                move_sent = False
                logger.log(f"[classify_object_func()] step, move_sent를 변경합니다. step : {step} / move_sent : {move_sent}")
            yield
            
        # PICK_POS    
        if step == 2:
            if not move_sent:
                logger.log(f"[classify_object_func()] moveL(PICK_POS) step : {step}")
                robot.moveL(*PICK_POS)
                move_sent = True
                logger.log(f"[classify_object_func()] move_sent를 True로 변경합니다. move_sent : {move_sent}")
                
            if robot.is_reached(PICK_POS):
                logger.log(f"[classify_object_func()] PICK_POS에 도착했습니다.")
                step = 3
                move_sent = False
                logger.log(f"[classify_object_func()] step, move_sent를 변경합니다. step : {step} / move_sent : {move_sent}")
            yield
        
        # SUCTION
        if step == 3:
            if suction_on_time is None:
                logger.log(f"[classify_object_func()] 흡입 step : {step}")
                robot.suction(1)
                suction_on_time = time.time()
                logger.log(f"[classify_object_func()] 흡입 시작 시간을 기록합니다. suction_on_time : {suction_on_time}")
            
            if (time.time() - suction_on_time) >= 1.0:
                logger.log(f"[classify_object_func()] 흡입 지속 시간이 1초를 경과하였습니다.")
                suction_on_time = None
                step = 4
                logger.log(f"[classify_object_func()] suction_on_time, step를 변경합니다. suction_on_time : {suction_on_time} / step : {step}")
            yield

        # PICK_WAY_POS
        if step == 4:
            if not move_sent:
                logger.log(f"[classify_object_func()] moveL(PICK_WAY_POS) step : {step}")
                robot.moveL(*PICK_WAY_POS)
                move_sent = True
                logger.log(f"[classify_object_func()] move_sent를 True로 변경합니다. move_sent : {move_sent}")
            
            if robot.is_reached(PICK_WAY_POS):
                logger.log(f"[classify_object_func()] PICK_WAY_POS에 도착했습니다.")
                step = 5
                move_sent = False
                logger.log(f"[classify_object_func()] step, move_sent를 변경합니다. step : {step} / move_sent : {move_sent}")
            yield
        
        # Home
        if step == 5:
            if not move_sent:
                logger.log(f"[classify_object_func()] moveJ(HOME_POS) step : {step}")
                robot.moveJ(*HOME_POS)
                move_sent = True
                logger.log(f"[classify_object_func()] move_sent를 True로 변경합니다. move_sent : {move_sent}")
            
            if robot.is_reached(HOME_POS):
                logger.log(f"[classify_object_func()] HOME_POS에 도착했습니다.")
                step = 6
                move_sent = False
                logger.log(f"[classify_object_func()] step, move_sent를 변경합니다. step : {step} / move_sent : {move_sent}")
            yield
        
        # SORT_WAY_POS
        if step == 6:
            if not move_sent:
                logger.log(f"[classify_object_func()] moveJ(sort_way_pos) step : {step}")
                robot.moveJ(*sort_way_pos)
                move_sent = True
                logger.log(f"[classify_object_func()] move_sent를 True로 변경합니다. move_sent : {move_sent}")
            
            if robot.is_reached(sort_way_pos):
                logger.log(f"[classify_object_func()] sort_way_pos에 도착했습니다.")
                step = 7
                move_sent = False
                logger.log(f"[classify_object_func()] step, move_sent를 변경합니다. step : {step} / move_sent : {move_sent}")
            yield
        
        # SORT_POS
        if step == 7:
            if not move_sent:
                logger.log(f"[classify_object_func()] moveL(sort_pos) step : {step}")
                robot.moveL(*sort_pos)
                move_sent = True
                logger.log(f"[classify_object_func()] move_sent를 True로 변경합니다. move_sent : {move_sent}")
            
            if robot.is_reached(sort_pos):
                logger.log(f"[classify_object_func()] sort_pos에 도착했습니다.")
                step = 8
                move_sent = False
                logger.log(f"[classify_object_func()] step, move_sent를 변경합니다. step : {step} / move_sent : {move_sent}")
            yield
        
        # DROP
        if step == 8:
            logger.log(f"[classify_object_func()] DROP step : {step}")
            robot.suction(0)
            step = 9
            logger.log(f"[classify_object_func()] step를 변경합니다. step : {step}")
            yield
        
        # SORT_WAY_POS
        if step == 9:
            if not move_sent:
                logger.log(f"[classify_object_func()] moveL(sort_way_pos) step : {step}")
                robot.moveL(*sort_way_pos)
                move_sent = True
                logger.log(f"[classify_object_func()] move_sent를 True로 변경합니다. move_sent : {move_sent}")
            
            if robot.is_reached(sort_way_pos):
                logger.log(f"[classify_object_func()] sort_way_pos에 도착했습니다.")
                step = 10
                move_sent = False
                logger.log(f"[classify_object_func()] step, move_sent를 변경합니다. step : {step} / move_sent : {move_sent}")
            yield
            
        # NEXT_STATE
        if step == 10:
            logger.log(f"[classify_object_func()] Dobot은 모든 분류작업을 끝냈습니다. step : {step}")
            logger.log(f"[classify_object_func()] CLASSIFY_OBJECT → COMPLETE_TASK")
            return "COMPLETE_TASK"
            
def complete_task_func():
    logger.log(f"[complete_task_func()] complete_task_func()에 들어왔습니다.")
    global FINISH_PROCESS_FLAG
    global CONVEYOR_FLAG
    logger.log(f"[complete_task_func()] STM32에게 분류 작업을 완료했다는 신호(000)를 보냅니다.")
    comm.send("000")

    yield
    
    if FINISH_PROCESS_FLAG:
        logger.log(f"[complete_task_func()] FINISH_PROCESS_FLAG를 받았습니다.")
        FINISH_PROCESS_FLAG = False
        logger.log(f"[complete_task_func()] FINISH_PROCESS_FLAG를 False로 바꿉니다. FINISH_PROCESS_FLAG : {FINISH_PROCESS_FLAG}")
        logger.log(f"COMPLETE_TASK → FINISH_PROCESS")
        return "FINISH_PROCESS"
    
    else:
        logger.log(f"[complete_task_func()] FINISH_PROCESS_FLAG가 없었으므로, 공정을 계속 진행합니다.")
        client.conveyor_on()
        CONVEYOR_FLAG = True
        logger.log(f"[complete_task_func()] 꺼져있던 CONVEYOR를 다시 가동(ON)합니다. CONVEYOR_FLAG : {CONVEYOR_FLAG}")
        logger.log(f"[complete_task_func()] COMPLETE_TASK → DETECT_OBJECT")
        return "DETECT_OBJECT"

def finish_process_func():
    logger.log("[finish_process_func()] finish_process_func()에 들어왔습니다.")
    global START_PROCESS_FLAG
    global FINISH_PROCESS_FLAG
    global step
    global move_sent
    step = 0
    move_sent = False
    logger.log(f"[finish_process_func()] step, move_sent를 초기화합니다. step : {step} / move_sent : {move_sent}")
    
    while True:
        if step == 0:
            if not move_sent:
                logger.log(f"[finish_process_func()] robot.home() 합니다. step : {step}")
                robot.home()
                move_sent = True
                logger.log(f"[finish_process_func()] move_sent를 True로 변경합니다 move_sent : {move_sent}")
                
            if robot.is_reached(HOME_POS):
                logger.log(f"[finish_process_func()] HOME_POS에 도착하였습니다.")
                step = 1
                move_sent = False
                logger.log(f"[finish_process_func()] step, move_sent를 변경합니다. step : {step} / move_sent : {move_sent}") 
            yield
            
        if step == 1:
            logger.log(f"[finish_process_func()] 공정을 종료합니다. step : {step}")
            cv2.destroyWindow("D435i")
            logger.log(f"[finish_process_func()] cv창을 종료합니다.")
            START_PROCESS_FLAG = False
            logger.log(f"[finish_process_func()] WAIT_START로 돌아가기 전, START_PROCESS_FLAG를 False로 초기화합니다. START_PROCESS_FLAG : {START_PROCESS_FLAG}")
            FINISH_PROCESS_FLAG = False
            logger.log(f"[finish_process_func()] WAIT_START로 돌아가기 전, FINISH_PROCESS_FLAG를 False로 초기화합니다. FINISH_PROCESS_FLAG : {FINISH_PROCESS_FLAG}")
            logger.log(f"[finish_process_func()] FINISH_PROCESS → WAIT_START")
            return "WAIT_START"

# ---------- THREAD FUNCTIONS ----------
def stm32_listener():
    logger.log("[stm32_listener()] stm32_listener를 시작합니다.")
    
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
                    logger.log("[stm32_listener()] STM32로부터 START_PROCESS_FLAG(110) 받았음")
                    START_PROCESS_FLAG = True
                    logger.log(f"[stm32_listener()] START_PROCESS_FLAG를 True로 바꿨습니다. START_PROCESS_FLAG : {START_PROCESS_FLAG}")
            
            elif receive_data == "100":
                if NOW_STATE != "WAIT_START" and NOW_STATE != "FINISH_PROCESS" and not EMERGENCY_FLAG:
                    logger.log("[stm32_listener()] STM32로부터 FINISH_PROCESS_FLAG(100) 받았음")
                    FINISH_PROCESS_FLAG = True
                    logger.log(f"[stm32_listener()] FINISH_PROCESS_FLAG를 True로 바꿨습니다. FINISH_PROCESS_FLAG : {FINISH_PROCESS_FLAG}")
                    
            elif receive_data == "101":
                logger.log("[stm32_listener()] STM32로부터 CLASSIFY_OBJECT_FLAG(101) 받았음")
                CLASSIFY_OBJECT_FLAG = True
                logger.log(f"[stm32_listener()] CLASSIFY_OBJECT_FLAG를 True로 바꿨습니다. CLASSIFY_OBJECT_FLAG : {CLASSIFY_OBJECT_FLAG}")
            
            elif receive_data == "111":
                logger.log("[stm32_listener()] STM32로부터 EMERGENCY_FLAG(111) 받았음")
                client.emergency_on()
                logger.log(f"[stm32_listener()] modbus coil 2번을 True로 변경합니다. (터틀봇 비상 시작)")
                EMERGENCY_FLAG = True
                logger.log(f"[stm32_listener()] 비상 상황을 시작합니다. EMERGENCY_FLAG : {EMERGENCY_FLAG}")
            
            elif receive_data == "000":
                logger.log("[stm32_listener()] STM32로부터 EMERGENCY_FLAG(000) 받았음")
                client.emergency_off()
                logger.log(f"[stm32_listener()] modbus coil 2번을 False로 변경합니다. (터틀봇 비상 해제)")
                EMERGENCY_FLAG = False
                logger.log(f"[stm32_listener()] 비상 상황을 해제합니다. EMERGENCY_FLAG : {EMERGENCY_FLAG}")
                    
        time.sleep(0.01)

def monitor_turtlebot():
    logger.log("[monitor_turtlebot()] 터틀봇이 Home으로 복귀했는지 확인하기 위한 스레드를 시작합니다.")
    global TURTLEBOT_BUSY_FLAG
    while True:
        TURTLEBOT_BUSY_FLAG = client.is_turtlebot_busy()
        time.sleep(0.01)
        
def start_turtlebot():
    logger.log("[start_turtlebot] 터틀봇에게 출발 명령을 내리기 위한 스레드에 들어왔습니다.")
    logger.log("[start_turtlebot] 컨베이어 → 터틀봇의 낙하시간을 고려해 2초를 대기합니다.")
    time.sleep(2)
    logger.log("[start_turtlebot] 터틀봇에게 출발 명령을 전송합니다.")
    client.send_start_mission()
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
                logger.log("[main()] Dobot queue 정지/초기화/시작 완료")
                cnt += 1
                logger.log(f"[main()] cnt +1 합니다. cnt : {cnt}")
                move_sent = False
                logger.log(f"[main()] move_sent를 False로 변경합니다. move_sent : {move_sent}")
                time.sleep(0.01)
                continue
            else:
                time.sleep(0.01)
                continue
        else:
            # 컨베이어가 켜져 있었다면
            if CONVEYOR_FLAG:
                logger.log("[main()] 컨베이어는 켜져있었고, 비상상황이므로 컨베이어를 종료합니다.")
                client.conveyor_off()
                CONVEYOR_FLAG = False
                logger.log(f"[main()] CONVEYOR_FLAG를 False로 변경합니다. CONVEYOR_FLAG : {CONVEYOR_FLAG}")
            time.sleep(0.01)
            continue
            
    try:
        # EMERGENCY CNT 원복
        cnt = 0
        # 컨베이어 상태 원복
        if conveyor_temp == True and CONVEYOR_FLAG == False:
            logger.log("[main()] 컨베이어가 비상 상황 전에 켜져있었으므로 다시 키겠습니다.")
            client.conveyor_on()
            CONVEYOR_FLAG = True
            logger.log(f"[main()] CONVEYOR_FLAG를 True로 변경합니다. CONVEYOR_FLAG : {CONVEYOR_FLAG}")
        next(current)
        
    except StopIteration as e:
        NOW_STATE = e.value
        current = STATE_FUNCTIONS[NOW_STATE]()
    
    # 컨베이어 상태 저장
    conveyor_temp = CONVEYOR_FLAG
    time.sleep(0.01)




