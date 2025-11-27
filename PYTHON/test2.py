from transform.transform import HandEyeCalibrator

cam_points = [
    (220, 134, 339.00),
    (289, 117, 339.00),
    (450, 120, 338.00),
    (141,  62, 341.00),
    (235,  61, 340.00),
    (324, 181, 336.00),
    (463, 182, 335.00),
    (512, 120, 337.00)
]
robot_points = [
    (195.84, -240.59, 19.89),
    (188.46, -199.43, 22.12),
    (192.61, -108.00, 16.92),
    (154.44, -285.33, 20.71),
    (155.51, -229.09, 22.12),
    (224.84, -180.33, 23.46),
    (229.48, -100.59, 22.97),
    (192.05,  -70.36, 22.96)
]

transformer = HandEyeCalibrator()
T = transformer.calibrate(cam_points, robot_points)
pick_pos = transformer.d435i_to_dobot(220, 134, 339.00)
print(pick_pos)