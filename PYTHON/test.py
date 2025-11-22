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
