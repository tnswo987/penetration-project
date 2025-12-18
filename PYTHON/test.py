from robot.robot import dobot

robot = dobot('COM6')
robot.connect()
robot.w_home()

pos = [x, y, z, r]

robot.moveL(*pos)
robot.w_home()
# robot.moveJ(*pos)
# robot.w_home()

robot.disconnect()