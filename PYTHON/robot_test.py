from robot.robot import dobot

robot = dobot('COM6')
robot.connect()

robot.home()