import numpy as np

class HandEyeCalibrator:
    def __init__(self, intr):
        self.fx = intr.fx
        self.fy = intr.fy
        self.cx = intr.ppx
        self.cy = intr.ppy
        print(f"fx={self.fx:.3f}, fy={self.fy:.3f}")
        print(f"cx={self.cx:.3f}, cy={self.cy:.3f}")
        
        self.T = None
    
    def pixel_to_3d(self, u, v, depth):
        Xc = (u - self.cx) * depth / self.fx
        Yc = (v - self.cy) * depth / self.fy
        Zc = depth
        return np.array([Xc, Yc, Zc])
    
    def calibrate(self, d435i_points, dobot_points):
        '''
        대응점 샘플값 list(tuple) 형식
        d435i_points : [(u, v, depth), ...]
        dobot_points : [(x, y, z), ...]
        '''

        # Kabsch Algorithm
        Pc = np.array([self.pixel_to_3d(u, v, d) for (u, v, d) in d435i_points])
        Pr = np.array(dobot_points)
        
        Pc_cent = Pc.mean(axis=0)
        Pr_cent = Pr.mean(axis=0)

        Pc_c = Pc - Pc_cent
        Pr_c = Pr - Pr_cent

        H = Pc_c.T @ Pr_c
        U, S, Vt = np.linalg.svd(H)
        R = Vt.T @ U.T

        if np.linalg.det(R) < 0:
            Vt[2, :] *= -1
            R = Vt.T @ U.T

        t = Pr_cent - R @ Pc_cent

        T = np.eye(4)
        T[:3, :3] = R
        T[:3, 3] = t

        self.T = T
        print(self.T)
        
        return T
    
    def d435i_to_dobot(self, u, v, depth):
        '''
        변환 행렬 T를 이용한 좌표변환
        '''
        if self.T is None:
            raise ValueError("Calibration이 먼저 필요합니다.")
        
        Pc = self.pixel_to_3d(u, v, depth)
        Pc_h = np.array([Pc[0], Pc[1], Pc[2], 1.0])
        
        Pr = self.T @ Pc_h
        return Pr[:3]