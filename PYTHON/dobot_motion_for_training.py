from robot.robot import dobot
import time

# ===============================
# CONFIG
# ===============================
PORT = "COM6"
RUN_TIME_SEC = 10 * 60  # 20분

HOME_POS = [209.75, 0, 99.96, 0]

PICK_POS = [-94.84517783391416, -241.05790508054199, 20.994688866535284, 0]
PICK_WAY_POS = [-94.84517783391416, -241.05790508054199, 70.99468886653528, 0]   # Z + 50

sort_pos = [263.29, -6.47, 19.36, -1.41]
sort_way_pos = [263.29, -6.47, 69.36, -1.41]  # Z + 50

# ===============================
# INIT
# ===============================
robot = dobot(PORT)
robot.connect()
print("[INFO] Dobot connected")
robot.w_home()
step = 0
move_sent = False
suction_on_time = None
    
# Home → PICK_WAY_POS → PICK_POS → SUCTION → PICK_WAY_POS → Home → SORT_WAY_POS → SORT_POS → DROP → SORT_WAY_POS → NEXT_STATE 
while True:
    # Home
    if step == 0:
        if not move_sent:
            robot.moveJ(*HOME_POS)
            move_sent = True
        
        if robot.is_reached(HOME_POS):
            step = 1
            move_sent = False
        
    # PICK_WAY_POS
    if step == 1:
        if not move_sent:
            robot.moveJ(*PICK_WAY_POS)
            move_sent = True
        
        if robot.is_reached(PICK_WAY_POS):
            step = 2
            move_sent = False
        
    # PICK_POS    
    if step == 2:
        if not move_sent:
            robot.moveL(*PICK_POS)
            move_sent = True
            
        if robot.is_reached(PICK_POS):
            step = 3
            move_sent = False

    # SUCTION
    if step == 3:
        if suction_on_time is None:
            robot.suction(1)
            suction_on_time = time.time()
        
        if (time.time() - suction_on_time) >= 1.0:
            suction_on_time = None
            step = 4

    # PICK_WAY_POS
    if step == 4:
        if not move_sent:
            robot.moveL(*PICK_WAY_POS)
            move_sent = True
        
        if robot.is_reached(PICK_WAY_POS):
            step = 5
            move_sent = False

    # Home
    if step == 5:
        if not move_sent:
            robot.moveJ(*HOME_POS)
            move_sent = True
        
        if robot.is_reached(HOME_POS):
            step = 6
            move_sent = False

    # SORT_WAY_POS
    if step == 6:
        if not move_sent:
            robot.moveJ(*sort_way_pos)
            move_sent = True
        
        if robot.is_reached(sort_way_pos):
            step = 7
            move_sent = False

    # SORT_POS
    if step == 7:
        if not move_sent:
            robot.moveL(*sort_pos)
            move_sent = True
        
        if robot.is_reached(sort_pos):
            step = 8
            move_sent = False

    # DROP
    if step == 8:
        robot.suction(0)
        step = 9

    # SORT_WAY_POS
    if step == 9:
        if not move_sent:
            robot.moveL(*sort_way_pos)
            move_sent = True
        
        if robot.is_reached(sort_way_pos):
            step = 0
            move_sent = False
            suction_on_time = None

    time.sleep(0.01)


