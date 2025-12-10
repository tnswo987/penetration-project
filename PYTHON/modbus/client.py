from pymodbus.client import ModbusTcpClient 
from datetime import datetime

class ModbusTCPClient:
    # 한 줄당 최대 100글자
    LINE_SIZE = 100
    # 최대 500줄 기록 가능
    MAX_LINES = 500
    # 로그 저장 시작 주소
    START_ADDR = 10
    # 로그 초기화 용도
    CHUNK_SIZE = 120
    
    def __init__(self, ip, port):
        self.ip = ip
        self.port = port
        self.client = None
        
    def connect(self):
        self.client = ModbusTcpClient(self.ip, self.port)
        state = self.client.connect()
        
        if state:
            print(f"[CONNECTED]")
        else:
            print(f"[CONNECTION FAILED]")
    
    def conveyor_on(self):
        self.client.write_coil(0, True, slave=1)
    
    def conveyor_off(self):
        self.client.write_coil(0, False, slave=1)
    
    def turtlebot_start(self):
        self.client.write_coil(1, False, slave=1)
    
    def turtlebot_emergency_on(self):
        self.client.write_coil(2, True, slave=1)
        
    def turtlebot_emergency_off(self):
        self.client.write_coil(2, False, slave=1)    
    
    def read_turtlebot_status(self):
        result = self.client.read_coils(1, 1, slave=1)
        return result.bits[0]

    def write_log(self, message: str):
        now = datetime.now().strftime("[%H:%M]")
        log_line = f"{now} {message}"
        
        # 아스키 코드로 변환
        encoded = [ord(c) for c in log_line]
        
        # 글자수를 초과하는 경우 방어 코드
        encoded = encoded[:self.LINE_SIZE]
        
        # 패딩
        while len(encoded) < self.LINE_SIZE:
            encoded.append(0)
            
        # 현재 log_count 읽기
        count_reg = self.client.read_holding_registers(0, 1, slave=1)
        log_count = count_reg.registers[0]
        
        # 기록 가능한 줄의 범위를 초과
        if log_count >= self.MAX_LINES:
            print("[MODBUS] Log memory full! Export required.")
            return
        
        # 시작 주소 계산
        start_addr = self.START_ADDR + (log_count * self.LINE_SIZE)
        
        # 레지스터에 기록
        self.client.write_registers(start_addr, encoded, slave=1)
        
        # log_count++
        self.client.write_registers(0, [log_count + 1], slave=1)
        
        print(f"[LOG SAVED] {log_line}")
    
    def export_logs(self, filename="log.txt"):
        # log_count 읽기
        count_reg = self.client.read_holding_registers(0, 1, slave=1)
        log_count = count_reg.registers[0]
        
        logs = []
        
        for i in range(log_count):
            start_addr = self.START_ADDR + (i * self.LINE_SIZE)
            
            raw = self.client.read_holding_registers(start_addr, self.LINE_SIZE, slave=1).registers
            chars = [chr(v) for v in raw if v != 0]
            log_line = "".join(chars)
            
            logs.append(log_line)
        
        with open(filename, "a", encoding="utf-8") as f:
            exported_time = datetime.now().strftime("%Y-%m-%d")
            
            f.write(f"--------- Exported at {exported_time} ---------\n")
            
            for line in logs:
                f.write(line + "\n")
                
        print(f"[LOG EXPORTED] {filename}")
        
        # log_count 초기화
        self.client.write_registers(0, [0], slave=1)
        
        # log 레지스터 전체 초기화
        total_registers = self.LINE_SIZE * self.MAX_LINES
        self._clear_log_registers_chunked(self.START_ADDR, total_registers)
    
    def _clear_log_registers_chunked(self, start_addr, total_registers):
        addr = start_addr
        remaining = total_registers
        zero_chunk = [0] * self.CHUNK_SIZE
        
        while remaining > 0:
            size = min(self.CHUNK_SIZE, remaining)
            self.client.write_registers(addr, zero_chunk[:size], slave=1)
            addr += size
            remaining -= size