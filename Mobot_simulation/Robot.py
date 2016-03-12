from vec2d_jdm import Vec2D
import math

class Robot(object):

    ROBOT_WIDTH = 10
    ROBOT_HEIGHT = 15
    ROBOT_EDGE = 2
    TRAJ_THICKNESS = 4

    def __init__(self, speed, canvaswidth, canvasheight, path, 
        color = "blue", trajColor = "red"):
        self.canvaswidth = canvaswidth
        self.canvasheight = canvasheight
        self.speed = speed
        self.height = Robot.ROBOT_HEIGHT
        self.v = Vec2D(0, speed)
        # Origin is actually at the center top of the 
        self.pos = Vec2D(0, 0)
        self.t = 0
        self.color = color
        self.trajColor = trajColor
        self.path = path
        self.trajectory = []

    def update(self):
        self.t += 1
        self.pos += self.v
        self.trajectory.append(self.pos)
        self.correctError()

    # This is where different algorithms differ 
    def correctError(self):
        pass

    def draw(self, canvas):
        self.drawTrajectory(canvas)
        self.drawRobot(canvas)

    def drawTrajectory(self, canvas):
        for point in self.trajectory:
            x = point.x
            y = point.y
            canvas.create_oval(x + self.canvaswidth / 2 
                                 - Robot.TRAJ_THICKNESS / 2,
                               y - Robot.TRAJ_THICKNESS / 2,
                               x + self.canvaswidth / 2 
                                 + Robot.TRAJ_THICKNESS / 2,
                               y + Path.THICKNESS / 2,
                                   fill = self.trajColor, width = 0)

    def drawRobot(self, canvas):
        angle = self.v.get_angle()
        # The side of the robot that's perpendicular to its velocity
        perpSide = Vec2D(Robot.ROBOT_WIDTH,0)
        perpSide = perpSide.set_angle(angle - 90)
        # The parallel side
        paraSide = Vec2D(Robot.ROBOT_HEIGHT,0)
        paraSide = paraSide.set_angle(angle)
        # The bottom edge
        (x0, y0) = (round((self.pos - perpSide * 0.5).x),
                 round((self.pos - perpSide * 0.5).y))
        (x1, y1) = (round((self.pos + perpSide * 0.5).x),
                 round((self.pos + perpSide * 0.5).y))
        canvas.create_line(x0 + self.canvaswidth / 2, y0,
         x1 + self.canvaswidth / 2, y1, width = Robot.ROBOT_EDGE, 
            fill = self.color)
        # The left edge
        x2 = x0 + round(paraSide.x)
        y2 = y0 + round(paraSide.y)
        canvas.create_line(x0 + self.canvaswidth / 2, y0,
         x2 + self.canvaswidth / 2, y2, width = Robot.ROBOT_EDGE, 
            fill = self.color)
        # The right edge
        x3 = x1 + round(paraSide.x)
        y3 = y1 + round(paraSide.y)
        canvas.create_line(x1 + self.canvaswidth / 2, y1,
         x3 + self.canvaswidth / 2, y3, width = Robot.ROBOT_EDGE, 
            fill = self.color)
        # The top edge
        canvas.create_line(x2 + self.canvaswidth / 2, y2,
         x3 + self.canvaswidth / 2, y3, width = Robot.ROBOT_EDGE, 
            fill = self.color)

class Robot_PID(Robot):
    def __init__(self,speed, canvaswidth, canvasheight, path, 
         P, I, D, color = "blue"):
        super().__init__( speed, canvaswidth, canvasheight, path, color)
        self.P = P
        self.I = I
        self.D = D
        self.lastErr = 0
        self.totalErr = 0

    def correctError(self):
        front = self.pos + self.v.normal() * self.height
        closestPoint = self.path.closestPoint(front)
        errorVec = closestPoint - self.pos
        error = errorVec.length()
        # Determine the sign of the error
        # + if path on the left, - if on the right
        theta = self.v.get_angle_between(errorVec)
        if theta < 0:
            error *= -1
        self.totalErr += error
        derivative = error - self.lastErr
        self.lastErr = error
        correction = (self.P * error +
                      self.I * self.totalErr +
                      self.D * derivative)
        self.v.rotated(correction, True)

class Robot_intelligent(Robot):
    pass


class Path(object):

    THICKNESS = 2

    def __init__(self, f, canvaswidth, canvasheight, 
        color = "black", resolution = 500):
        self.resolution = resolution
        self.path = f
        self.height = canvasheight
        self.width = canvaswidth
        self.color = color

    def getPoint(self, t):
        return self.path(t)

    def closestPoint(self, pos):
        minDistance = None
        for i in range(self.resolution):
            t = i / self.resolution # t in [0, 1)
            point = self.getPoint(t)
            d = ((pos.x - point.x)**2 + (pos.y - point.y)**2)**0.5
            if minDistance == None or d < minDistance:
                minDistance = d
                result = point
        return result

    def draw(self, canvas):
        for i in range(self.resolution):
            t = i / self.resolution # t in [0, 1)
            point = self.getPoint(t)
            x = point.x
            y = point.y
            canvas.create_oval(x + self.width / 2 - Path.THICKNESS / 2,
                               y - Path.THICKNESS / 2,
                               x + self.width / 2 + Path.THICKNESS / 2,
                               y + Path.THICKNESS / 2,
                               fill = self.color)

