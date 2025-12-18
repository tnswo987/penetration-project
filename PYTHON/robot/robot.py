import DobotEDU

class dobot:
    def __init__(self, port):
        self.port = port
        self.device = DobotEDU.dobot_magician
    
    def connect(self):
        self.device.connect_dobot(self.port)
    
    def disconnect(self):
        self.device.disconnect_dobot(self.port)

    def home(self):
        self.device.set_homecmd(self.port, is_queued=True, is_wait=False)
    
    def w_home(self):
        self.device.set_homecmd(self.port, is_queued=True, is_wait=True)
        
    def moveL(self, pos_x, pos_y, pos_z, pos_r):
        self.device.set_ptpcmd(self.port, ptp_mode=2, x=pos_x, y=pos_y, z=pos_z, r=pos_r, is_queued=True, is_wait=False)
    
    def moveJ(self, pos_x, pos_y, pos_z, pos_r):
        self.device.set_ptpcmd(self.port, ptp_mode=1, x=pos_x, y=pos_y, z=pos_z, r=pos_r, is_queued=True, is_wait=False)
        
    def suction(self, state):
        if state == 1:
            self.device.set_endeffector_suctioncup(self.port, enable=True, on=True)
        else:
            self.device.set_endeffector_suctioncup(self.port, enable=False, on=False)
    
    def get_pose(self):
        return self.device.get_pose(self.port)
    
    def is_reached(self, target_pose: list, tol=2.0):
        current_pose = self.get_pose()
        dx = abs(current_pose['x'] - target_pose[0])
        dy = abs(current_pose['y'] - target_pose[1])
        dz = abs(current_pose['z'] - target_pose[2])
        return dx < tol and dy < tol and dz < tol
        
    def stop(self):
        self.device.queuedcmd_stop(self.port, force_stop=True)
    
    def start(self):
        self.device.queuedcmd_start(self.port)

    def clear(self):
        self.device.queuedcmd_clear(self.port)