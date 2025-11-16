from pymodbus.client import ModbusTcpClient

class ModbusTCPClient:
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
    
    # 3비트만 취급할거임
    # 내부값은 str
    # enumrate된, list 형태만 data값으로 받기
    # 비상입력만 받게된다.
    def write(self, datas):
        for data in datas:
            self.client.write_register(address=int(data[0]), value=int(data[1]), slave=1)
    
    def read(self):
        result = ""
        
        a = self.client.read_holding_registers(address=0, count=3, slave=1)
        values = a.registers
        
        for value in values:
            result += str(value)

        return result