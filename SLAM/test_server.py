# -*- coding: utf-8 -*-
import threading
from pymodbus.server import StartTcpServer
from pymodbus.datastore import (
    ModbusSequentialDataBlock,
    ModbusSlaveContext,
    ModbusServerContext,
)

# TurtleBot 쪽에서 사용하는 Coil 매핑
COIL_START_MISSION = 1   # Start_Mission
COIL_EMERGENCY     = 2   # Emergency

# Datastore: coil 0~9 (10개)만 사용
store = ModbusSlaveContext(
    di=None,
    co=ModbusSequentialDataBlock(0, [0] * 10),
    hr=None,
    ir=None,
)
context = ModbusServerContext(slaves=store, single=True)

def set_coil(address, value: bool):
    context[0].setValues(1, address, [1 if value else 0])

def get_coil(address) -> int:
    return context[0].getValues(1, address, count=1)[0]

def toggle_coil(address):
    cur = get_coil(address)
    new = 0 if cur else 1
    set_coil(address, new)
    return new

def user_input_thread():
    print("===== Modbus 서버 테스트 =====")
    print("1 → Start_Mission 토글 (0↔1)")
    print("2 → Emergency 토글 (0↔1)")
    print("Ctrl+C 로 서버 종료")

    while True:
        cmd = input("입력 >> ").strip()

        if cmd == "1":
            new = toggle_coil(COIL_START_MISSION)
            print(f"[SERVER] Start_Mission -> {new}")
        elif cmd == "2":
            new = toggle_coil(COIL_EMERGENCY)
            print(f"[SERVER] Emergency -> {new}")
        else:
            print("1 또는 2만 사용합니다.")

        s = get_coil(COIL_START_MISSION)
        e = get_coil(COIL_EMERGENCY)
        print(f"[STATUS] Start_Mission={s}, Emergency={e}")

if __name__ == "__main__":
    t = threading.Thread(target=user_input_thread, daemon=True)
    t.start()

    print("Modbus TCP Server Start (192.168.110.108:20000)")
    StartTcpServer(context=context, address=("192.168.110.108", 20000))
