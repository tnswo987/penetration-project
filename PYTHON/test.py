NOW_STATE = "START_PROCESS"

def state_wait_signal():
    while True:
        if NOW_STATE == "START_PROCESS":
            return "Hello"
        
        yield

current = state_wait_signal()

try:
    next(current)

except StopIteration as e:
    print(e.value)
    
    
    
    elif NOW_STATE == "CLASSIFY_OBJECT":
        print(f"[DOBOT] Start PICK & SORT")
        
        robot.move(*PICK_POSITION)
        robot.suction(1)
        
        sort_pos = SORT_POSITION[last_detected_color]
        robot.move(*sort_pos)
        robot.suction(0)
        
        NOW_STATE = "COMPLETE_TASK"
        
        
        
        
                
    elif NOW_STATE == "COMPLETE_TASK":
        print(f"[DOBOT] Task Completed")
        comm.send("000")
        
        NOW_STATE = "DETECT_OBJECT"