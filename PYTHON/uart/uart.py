import serial

class uart:
    def __init__(self, port, baudrate):
        self.port = port
        self.baudrate = baudrate
        self.ser = serial.Serial(self.port, baudrate, timeout=1)
    
    def receive(self):
        raw_datas = None
        
        if self.ser.in_waiting > 0: 
            raw_datas = self.ser.readline().decode('utf-8').strip()
            
        if raw_datas:
            try:
                datas = list(enumerate(raw_datas))
                return datas
            
            except Exception as e:
                print("[Failed to receive data from STM32]")

            
    def send(self, data):
        if isinstance(data, (list, tuple)):
            data = "".join(str(x) for x in data)
        
        if not isinstance(data, str) or len(data) != 3:
            print("[Data must be a 3-character string]")
            return False
        
        try:
            self.ser.write((data + "\r\n").encode('utf-8'))
            return True
        
        except Exception as e:
            print("Failed to send data to STM32")
            return False