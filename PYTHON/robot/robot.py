import DobotEDU
import time

class dobot:
    def __init__(self, port):
        self.port = port
        self.device = DobotEDU.dobot_magician
    
    def connect(self):
        self.device.connect_dobot(self.port)
        time.sleep(1)
    
    def disconnect(self):
        self.device.disconnect_dobot(self.port)

    def home(self):
        self.device.set_homecmd(self.port)
        time.sleep(1)

    def move(self, pos_x, pos_y, pos_z, pos_r):
        self.device.set_ptpcmd(self.port, ptp_mode=4, x=pos_x, y=pos_y, z=pos_z, r=pos_r)
        time.sleep(1)
    
    def suction(self, state):
        if state == 1:
            self.device.set_endeffector_suctioncup(self.port, enable=True, on=True)
        else:
            self.device.set_endeffector_suctioncup(self.port, enable=False, on=False)
        
        time.sleep(1)