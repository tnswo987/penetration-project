from modbus.server import ModbusTCPServer

serv = ModbusTCPServer("192.168.137.1", 20000)
serv.start()