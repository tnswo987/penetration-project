import time
import threading

import rclpy
from nav2_simple_commander.robot_navigator import BasicNavigator, TaskResult
from geometry_msgs.msg import PoseStamped

from pymodbus.client import ModbusTcpClient

# Modbus 설정
MODBUS_HOST = "192.168.110.101"
MODBUS_PORT = 20000
MODBUS_UNIT_ID = 1    

# Coil / Register 매핑
COIL_START_MISSION = 1   # 목적지 출발 명령
COIL_EMERGENCY     = 2   # 비상 플래그

# 목적지로 출발 명령
start_mission_flag = False
# 비상 상태
emergency_flag = False
modbus_running = True

modbus_lock = threading.Lock()
modbus_client = None


WORK_ROUTE = {
    "work_target": [3.67, 2.22, 0.00247, 1.0],
    "work_init": [-0.17, 0.00495, 0.14, 1.0],
}

def make_pose(x, y, w, navigator):
    goal = PoseStamped()
    goal.header.frame_id = 'map'
    goal.header.stamp = navigator.get_clock().now().to_msg()
    goal.pose.position.x = x
    goal.pose.position.y = y
    goal.pose.orientation.w = w
    return goal

def go_to_with_emergency(navigator, goal_pose, init_pose):
    global emergency_flag

    navigator.goToPose(goal_pose)

    while not navigator.isTaskComplete():
        # 비상 감지
        if emergency_flag:
            print("[NAV] Emergency detected! Cancel current goal and go home.")
            navigator.cancelTask()
            time.sleep(0.1)

            # 초기 위치로 복귀
            navigator.goToPose(init_pose)
            while not navigator.isTaskComplete():
                time.sleep(0.1)

            print("[NAV] Returned to init pose due to emergency.")
            return "ABORTED_EMERGENCY"
        time.sleep(0.1)

    result = navigator.getResult()
    print(f"[NAV] Goal finished with result: {result}")
    return "COMPLETED"

def ensure_modbus_connected():
    # 클라이언트 연결 보장
    global modbus_client
    if modbus_client is None:
        modbus_client = ModbusTcpClient(MODBUS_HOST, port=MODBUS_PORT)
    if not modbus_client.connected:
        modbus_client.connect()

def read_coils_safe(address, count = 1):
    with modbus_lock:
        ensure_modbus_connected()
        rr = modbus_client.read_coils(address, count, slave = MODBUS_UNIT_ID)
    return rr

def write_coil_safe(address, value):
    with modbus_lock:
        ensure_modbus_connected()
        modbus_client.write_coil(address, value, slave = MODBUS_UNIT_ID)

def modbus_polling_thread():
    global start_mission_flag, emergency_flag, modbus_running

    print("[MODBUS] Polling thread started.")

    while modbus_running:
        try:
            rr = read_coils_safe(COIL_START_MISSION, 2)
            if rr.isError():
                print("[MODBUS] Read error:", rr)
            else:
                bits = rr.bits
                start_mission_flag = bool(bits[0])
                emergency_flag = bool(bits[1])

        except Exception as e:
            print("[MODBUS] Exception while reading:", e)
            # 에러 시 잠깐 쉬고 재시도
            time.sleep(1.0)

        time.sleep(0.1)

    print("[MODBUS] Polling thread stopped.")

def main():

    global modbus_running

    # Modbus 쓰레드 시작
    polling_thread = threading.Thread(target=modbus_polling_thread, daemon=True)
    polling_thread.start()

    # ROS2 Nav2 초기화
    rclpy.init()
    navigator = BasicNavigator()
    navigator.waitUntilNav2Active()
    print("[NAV] Nav2 is Ready!")

    # 초기 위치 pose
    x_i, y_i, _, w_i = WORK_ROUTE["work_init"]
    init_pose = make_pose(x_i, y_i, w_i, navigator)

    mission_active = False

    try:
        while rclpy.ok():
            if not mission_active:
                if start_mission_flag and not emergency_flag:
                    mission_active = True
                    print("[MAIN] Start mission from Modbus (coil 1).")
                
                # 1) 목적지 이동
                    x_t, y_t, _, w_t = WORK_ROUTE["work_target"]
                    target_pose = make_pose(x_t, y_t, w_t, navigator)

                    print("[MAIN] Going to target pose...")
                    result = go_to_with_emergency(navigator, target_pose, init_pose)

                    if result == "ABORTED_EMERGENCY":
                        mission_active = False
                        continue

                    # 정상 도착
                    print("[MAIN] Arrived at target.")

                # 30초간 언로딩 대기
                    print("[MAIN] Waiting 30 seconds for unloading mini boxes...")
                    for _ in range(30):
                        if emergency_flag:
                            print("[MAIN] Emergency during unloading, returning home.")
                            result2 = go_to_with_emergency(navigator, init_pose, init_pose)
                            print("[MAIN] Writing INIT_REACHED (coil 1).")
                            write_coil_safe(COIL_START_MISSION, False)
                            mission_active = False
                            break
                        time.sleep(1.0)

                    if emergency_flag:
                        continue

                    # 2) 초기 위치로 복귀
                    print("[MAIN] Returning to init pose...")
                    result2 = go_to_with_emergency(navigator, init_pose, init_pose)

                    if result2 == "ABORTED_EMERGENCY":
                        print("[MAIN] Returned home due to emergency during return.")
                    else:
                        print("[MAIN] Init pose reached normally.")

                    print("[MAIN] Writing INIT_REACHED (coil 1).")
                    write_coil_safe(COIL_START_MISSION, False)

                    # 다음 미션 준비
                    mission_active = False

                else:
                    time.sleep(0.1)
            else:
                time.sleep(0.1)
    
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
