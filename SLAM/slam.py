import time
import threading

import rclpy
from nav2_simple_commander.robot_navigator import BasicNavigator, TaskResult
from geometry_msgs.msg import PoseStamped

from pymodbus.client import ModbusTcpClient
from std_msgs.msg import String, Bool, Int32

# ---------------- Modbus 설정 ----------------
MODBUS_HOST = "192.168.110.101"
MODBUS_PORT = 20000
MODBUS_UNIT_ID = 1

# 출발 명령(ON)
COIL_START_MISSION = 1
# 비상(ON), 해제(OFF)
COIL_EMERGENCY     = 2

start_mission_flag = False
emergency_flag = False
prev_start_mission_flag = False
modbus_running = True

modbus_lock = threading.Lock()
modbus_client = None

# WORK_ROUTE = {
#         "work_init": [
#         -1.96, -0.497, 0.076,
#         0.9999676506991817
#     ],
#     "work_target": [
#         1.77, 0.601, -0.00137,
#         0.9999676506991817
#     ],
# }

# 초기 실제 값
WORK_ROUTE = {
    "work_target": [3.67, 2.22, 0.00247, 1.0],
    "work_init": [-0.17, 0.00495, 0.14, 1.0],
}

UNLOADING_SECONDS = 10

# ---------------- Utils ----------------
def make_pose(x, y, z, w, navigator):
    goal = PoseStamped()
    goal.header.frame_id = 'map'
    goal.header.stamp = navigator.get_clock().now().to_msg()
    goal.pose.position.x = x
    goal.pose.position.y = y
    goal.pose.orientation.z = z
    goal.pose.orientation.w = w
    return goal

def ensure_modbus_connected():
    global modbus_client
    if modbus_client is None:
        modbus_client = ModbusTcpClient(MODBUS_HOST, port=MODBUS_PORT)
    if not modbus_client.connected:
        modbus_client.connect()

def read_coils_safe(address, count=1):
    with modbus_lock:
        ensure_modbus_connected()
        rr = modbus_client.read_coils(address, count, slave=MODBUS_UNIT_ID)
    return rr

def write_coil_safe(address, value):
    with modbus_lock:
        ensure_modbus_connected()
        modbus_client.write_coil(address, value, slave=MODBUS_UNIT_ID)

def modbus_polling_thread():
    global start_mission_flag, emergency_flag, modbus_running
    print("[MODBUS] Polling thread started.")

    while modbus_running:
        try:
            # coil1~2 읽기
            rr = read_coils_safe(COIL_START_MISSION, 2)
            if rr.isError():
                print("[MODBUS] Read error:", rr)
            else:
                bits = rr.bits
                # coil1
                start_mission_flag = bool(bits[0])
                # coil2
                emergency_flag = bool(bits[1])

        except Exception as e:
            print("[MODBUS] Exception while reading:", e)
            time.sleep(1.0)

        time.sleep(0.01)

    print("[MODBUS] Polling thread stopped.")

def wait_emergency_clear():
    """비상 ON 동안 그 자리에서 대기, OFF 되는 순간 반환"""
    global emergency_flag
    while emergency_flag:
        time.sleep(0.1)

def pause_and_resume_if_emergency(navigator, current_goal_pose):
    """
    emergency_flag가 True면:
      - 현재 task cancel해서 즉시 정지(그 자리)
      - coil2 OFF 될 때까지 대기
      - 같은 goal을 다시 goToPose로 재개
    """
    global emergency_flag

    if not emergency_flag:
        return

    print("[NAV] Emergency ON -> cancel current navigation and wait in place.")
    navigator.cancelTask()
    time.sleep(0.2)

    print("[NAV] Waiting until Emergency OFF...")
    wait_emergency_clear()
    print("[NAV] Emergency OFF -> resume previous goal.")

    navigator.goToPose(current_goal_pose)

def run_navigation_with_pause(navigator, goal_pose, publish_ui_cb=None, moving_text=""):
    """
    goal_pose로 이동을 진행하되,
    이동 중 emergency ON이면 정지/대기/재개 수행.
    """
    navigator.goToPose(goal_pose)

    while not navigator.isTaskComplete():

        if publish_ui_cb:
            publish_ui_cb(moving_text, emergency_flag, 0)
        
        pause_and_resume_if_emergency(navigator, goal_pose)
        time.sleep(0.1)

    return navigator.getResult()

# ---------------- Main ----------------
def main():
    global modbus_running, prev_start_mission_flag

    polling_thread = threading.Thread(target=modbus_polling_thread, daemon=True)
    polling_thread.start()

    rclpy.init()
    # Nav2를 조종할 수 있는 컨트롤 노드를 만든다.
    navigator = BasicNavigator()

    # ROS Topic으로 Web에서 topic 값 받기
    # /ui/mission_state : std_msgs/msg/String
    # /ui/emergency : std_msgs/msg/Bool
    # /ui/wait_remaining : std_msgs/msg/Int32

    mission_pub = navigator.create_publisher(String, "/ui/mission_state", 10)
    emerg_pub   = navigator.create_publisher(Bool,   "/ui/emergency", 10)
    wait_pub    = navigator.create_publisher(Int32,  "/ui/wait_remaining", 10)

    def publish_ui(mission_state: str, emergency: bool, wait_remaining: int):
        mission_pub.publish(String(data=mission_state))
        emerg_pub.publish(Bool(data=emergency))
        wait_pub.publish(Int32(data=int(wait_remaining)))

    # Nav2가 실제로 명령을 받을 수 있을 때까지 기다린다.
    navigator.waitUntilNav2Active()
    # Nav2 준비완료
    print("[NAV] Nav2 is Ready!")

    # init/target pose 준비
    x_i, y_i, z_i, w_i = WORK_ROUTE["work_init"]
    init_pose = make_pose(x_i, y_i, z_i, w_i, navigator)

    x_t, y_t, z_t, w_t = WORK_ROUTE["work_target"]
    target_pose = make_pose(x_t, y_t, z_t, w_t, navigator)

    # 상태머신
    STATE_WAIT     = "WAIT_START"
    STATE_GO_TARGET = "GO_TARGET"
    STATE_WAIT_WORK = "WAIT_WORK"
    STATE_GO_HOME  = "GO_HOME"

    state = STATE_WAIT
    wait_remaining = 0
    mission_active = False

    try:
        while rclpy.ok():

            # ------------- WAIT_START -------------
            if state == STATE_WAIT:

                # ROS Topic Publish
                publish_ui("초기 위치에서 대기", emergency_flag, 0)

                mission_active = False

                # 비상 중이면 그냥 대기
                if emergency_flag:
                    time.sleep(0.1)
                    continue

                # START_MISSION 상승 에지 감지
                if start_mission_flag and not prev_start_mission_flag:
                    print("[MAIN] START_MISSION rising edge detected -> start mission!")
                    mission_active = True
                    state = STATE_GO_TARGET

                # 이전 상태 갱신
                prev_start_mission_flag = start_mission_flag
                time.sleep(0.05)

            # ------------- GO_TARGET -------------
            elif state == STATE_GO_TARGET:
                # ROS Topic Publish
                publish_ui("목표 지점으로 이동", emergency_flag, 0)
                
                print("[MAIN] Going to target pose...")
                result = run_navigation_with_pause(navigator, target_pose, publish_ui_cb=publish_ui, moving_text="work target으로 이동중")
                print(f"[MAIN] Target navigation finished: {result}")

                if result == TaskResult.SUCCEEDED:
                    print(f"[MAIN] Arrived at target -> wait {UNLOADING_SECONDS}s.")
                    wait_remaining = UNLOADING_SECONDS
                    state = STATE_WAIT_WORK
                else:
                    # 이동 실패/중단 시: 미션 종료로 보고 coil1 OFF로 리셋(안전)
                    print("[MAIN] Failed to reach target -> write coil1 OFF and back to WAIT.")
                    write_coil_safe(COIL_START_MISSION, False)
                    state = STATE_WAIT

            # ------------- WAIT_WORK (10s wait at target) -------------
            elif state == STATE_WAIT_WORK:
                # 비상 ON이면 타이머 멈추고 그 자리 대기
                if emergency_flag:
                    print("[MAIN] Emergency ON during work-wait -> pause timer and wait.")
                    # ROS Topic Publish
                    publish_ui("목표 지점에서 박스 하차", True, wait_remaining)
                    wait_emergency_clear()
                    print("[MAIN] Emergency OFF -> resume work-wait timer.")

                if wait_remaining > 0:
                    # ROS Topic Publish
                    publish_ui("목표 지점에서 박스 하차", emergency_flag, wait_remaining)
                    print(f"[MAIN] Work-wait... remaining: {wait_remaining}s")
                    time.sleep(1.0)
                    wait_remaining -= 1
                else:
                    state = STATE_GO_HOME

            # ------------- GO_HOME -------------
            elif state == STATE_GO_HOME:
                publish_ui("초기 위치로 복귀", emergency_flag, 0)
                print("[MAIN] Returning to init pose...")
                result = run_navigation_with_pause(navigator, init_pose, publish_ui_cb=publish_ui, moving_text="work init으로 복귀")
                print(f"[MAIN] Home navigation finished: {result}")

                # 요구사항: HOME 복귀 완료 후 coil1 OFF 기록
                if result == TaskResult.SUCCEEDED:
                    print("[MAIN] Home reached -> write coil1 OFF (mission complete).")
                else:
                    print("[MAIN] Home navigation not SUCCEEDED, but reset coil1 OFF for safety.")

                write_coil_safe(COIL_START_MISSION, False)
                state = STATE_WAIT

            else:
                time.sleep(0.1)

            rclpy.spin_once(navigator, timeout_sec=0.0)

    except KeyboardInterrupt:
        print("[MAIN] KeyboardInterrupt, shutting down...")

    finally:
        modbus_running = False
        polling_thread.join(timeout=1.0)

        if modbus_client is not None:
            modbus_client.close()

        rclpy.shutdown()

if __name__ == '__main__':
    main()
