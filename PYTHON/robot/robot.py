import DobotEDU
import time

class dobot:
    def __init__(self, port):
        self.port = port
        self.device = DobotEDU.dobot_magician
    
    def connect(self):
        self.device.connect_dobot(self.port)
    
    def disconnect(self):
        self.device.disconnect_dobot(self.port)

    def home(self):
        self.device.set_homecmd(self.port)

    def move(self, pos_x, pos_y, pos_z, pos_r):
        self.device.set_ptpcmd(self.port, ptp_mode=2, x=pos_x, y=pos_y, z=pos_z, r=pos_r)
    
    def suction(self, state):
        if state == 1:
            self.device.set_endeffector_suctioncup(self.port, enable=True, on=True)
        else:
            self.device.set_endeffector_suctioncup(self.port, enable=False, on=False)
    
    def stop(self):
        self.device.queuedcmd_stop(self.port, force_stop=True)
    
    def start(self):
        self.device.queuedcmd_start(self.port)

    def clear(self):
        self.device.queuedcmd_clear(self.port)