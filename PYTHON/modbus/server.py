from pymodbus.server import StartTcpServer
from pymodbus.datastore import ( 
    ModbusSequentialDataBlock,
    ModbusSlaveContext,
    ModbusServerContext,
)
import logging

class ModbusTCPServer:
    def __init__(self, ip, port):
        self.ip = ip
        self.port = port
        
        logging.basicConfig()
        log = logging.getLogger()
        log.setLevel(logging.DEBUG)
        
        self.store = ModbusSlaveContext(
            di = ModbusSequentialDataBlock(0, [0]*1),
            co = ModbusSequentialDataBlock(0, [0]*1),
            ir = ModbusSequentialDataBlock(0, [0]*1),
            hr = ModbusSequentialDataBlock(0, [0]*65530),
        )
        
        self.context = ModbusServerContext(slaves={1: self.store}, single=False)
    
    def start(self):
        print(f"[MDOBUS SERVER ONLINE]")
        print(f"[IP : {self.ip} / PORT : {self.port}]")
        StartTcpServer(context = self.context, address = (self.ip, self.port))