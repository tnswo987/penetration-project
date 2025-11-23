from modbus.client import ModbusTCPClient
from datetime import datetime
import time 
client = ModbusTCPClient("192.168.137.1", 20000)
client.connect()


client.write_log("[DOBOT] Device connected successfully.")
client.write_log("[DOBOT] Start PICK & SORT")
client.export_logs()
time.sleep(10)
client.write_log("[DOBOT] Device connected successfully.")
client.write_log("[DOBOT] Start PICK & SORT")
client.write_log("광철쿤")
client.write_log("해냈슴")
client.export_logs()