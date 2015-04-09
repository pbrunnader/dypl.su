from JythonTranslater import Jtrans
import re
import math
import time

class MyJythonFile(Jtrans):

    def __init__(self):
        pass
        integer_variable = "([0-9]+|[a-zA-Z][a-zA-Z0-9]*)\s*(\s*[+*-]\s*([0-9]+|[a-zA-Z][a-zA-Z0-9]*))*"
        self.actions = (
            ("^\s*(?P<FUNCTION>pen down)\s*\n(?P<NEXT>[\w\W]*)", self.pen_down),
            ("^\s*(?P<FUNCTION>pen up)\s*(?P<NEXT>[\w\W]*)", self.pen_up),
            ("^\s*(?P<FUNCTION>move forward)\s*\n(?P<NEXT>[\w\W]*)", self.move_forward),
            ("^\s*(?P<FUNCTION>move backward)\s*\n(?P<NEXT>[\w\W]*)", self.move_backward),
            ("^\s*(?P<FUNCTION>move)\(\s*(?P<STEPS>" + integer_variable + ")\s*,\s*(?P<ANGLE>" + integer_variable + ")\s*\)\s*\n(?P<NEXT>[\w\W]*)", self.move),
            ("^\s*(?P<FUNCTION>turn cw)\(\s*(?P<ANGLE>" + integer_variable + ")\s*\)\s*\n(?P<NEXT>[\w\W]*)", self.turn_cw),
            ("^\s*(?P<FUNCTION>turn ccw)\(\s*(?P<ANGLE>" + integer_variable + ")\s*\)\s*\n(?P<NEXT>[\w\W]*)", self.turn_ccw),
            ("^\s*(?P<FUNCTION>put)\(\s*(?P<XPOS>" + integer_variable + ")\s*,\s*(?P<YPOS>" + integer_variable + ")\s*,\s*(?P<ANGLE>" + integer_variable + ")\s*\)\s*\n(?P<NEXT>[\w\W]*)", self.put),
            ("^\s*((?P<FUNCTION>for) (?P<VARIABLE>[A-Za-z][A-Za-z0-9]*)\s*=\s*(?P<INITIAL>\d+) to (?P<LIMIT>\d+) do)(?P<NEXT>[\w\W\s]*end\s*[\w\W]*)", self.forLoop),
            ("^\s*(?P<FUNCTION>end)\s*\n(?P<NEXT>[\w\W]*)", self.end),
            ("^\s*(?P<FUNCTION>[\w\W]*)", self.error)
        )

    def error(self, param):
        m = re.match("^\s*(?P<ERROR>.*)[\n]?[\w\W\s]*$", param["FUNCTION"])
        if m :
            print "ERROR: Not valid syntax in or close to line '" + m.group("ERROR") + "'"
        else:
            print "ERROR: Not valid syntax. 'unknown'"
        return "error"

    def evaluate(self, param, var):
        d = {}
        for k in param:
            d.update({ k : param[k] })
            if k == "ANGLE" or k == "STEPS" or k == "XPOS" or k == "YPOS":
                arg = param[k]
                for t in var:
                    arg = arg.replace(t, str(var[t]["initial"]))
                d.update({ k : eval(arg) })
        return d

    def process(self, input):
        next = self.process_branch(input, {})
        if len(next) > 0:
            self.reset()
            return False
        return True

    def process_branch(self, input, var):
        if len(input) > 0:
            for regex, action in self.actions:
                m = re.match(regex, input)
                if m:
                    if m.group("FUNCTION") == "for":
                        input = action(self.evaluate(m.groupdict(), var), var)
                    else:
                        input = action(self.evaluate(m.groupdict(), var))

                    if input == "error":
                        return input
                        # return False

                    if m.group("FUNCTION") == "end":
                        return m.group("NEXT");
                    return self.process_branch(input, var)
            return ""
        return ""

    # enable drawing on canvas
    def pen_down(self, param):
        self.draw = True
        return param["NEXT"]

    # disable drawing on canvas
    def pen_up(self, param):
        self.draw = False
        return param["NEXT"]

    # draw one pixel in direction
    def move_forward(self, param):
        self.move(1, 0)
        return param["NEXT"]

    # draw one pixel in opposite direction
    def move_backward(self, param):
        self.turn_cw(180)
        self.move(1, 0)
        self.turn_cw(180)
        return param["NEXT"]

    # draw a given number of pixels in the (changed) direction
    def move(self, param):
        steps, angle = int(param["STEPS"]), int(param["ANGLE"])
        self.turn_cw(param)
        # cos -> x, sin -> y
        x = math.cos(math.radians(self.pointer[2]))
        y = math.sin(math.radians(self.pointer[2]))
        for i in [1] * steps:
            self.pointer[0] = self.pointer[0] + x
            self.pointer[1] = self.pointer[1] + y
            self.log(self.pointer[0], self.pointer[1])
        return param["NEXT"]

    # change angle clock-wise (relative)
    def turn_cw(self, param):
        angle = int(param["ANGLE"])
        self.pointer[2] = (self.pointer[2] + angle) % 360

    # change angle counter-clock-wise (relative)
    def turn_ccw(self, param):
        angle = int(param["ANGLE"])
        self.pointer[2] = (self.pointer[2] + (360 - angle % 360)) % 360
        return param["NEXT"]

    # set position on x and y axis and set angle (absolute)
    def put(self, param):
        xpos, ypos, angle = int(param["XPOS"]), int(param["YPOS"]), int(param["ANGLE"]) + 270
        self.pointer = [xpos, ypos, angle % 360]
        return param["NEXT"]

    def end(self, param):
        return param["NEXT"]

    def forLoop(self, param, var):
        initial, limit, variable, next = param["INITIAL"], param["LIMIT"], param["VARIABLE"], param["NEXT"]
        bit = False
        if variable not in var:
            bit = True
            var[variable] = {"initial" : int(initial), "limit" : int(limit)}
        else:
            var[variable] = {"initial" : int(var[variable]["initial"]), "limit" : int(limit)}
        for i in range(var[variable]["initial"],int(limit)+1):
            var[variable] = {"initial" : i, "limit" : limit}
            next = self.process_branch(param["NEXT"], var)
        if bit:
	        del var[variable]
        return next

   # draw one pixel at given x and y axis
    def paint(self):
        for xpos, ypos in self.points:
            self.object.setPixel(int(xpos),int(ypos))

    def log(self, xpos, ypos):
        if self.draw:
            self.points.append((xpos, ypos))

    def reset(self):
        self.points = []

    def actionPerformed(self, event):
        print("Button clicked.")
        input = self.object.getCode()
        self.reset()
        if self.process(input):
            self.paint()
            print("Painting done.")
        self.reset()
        # print(event)

    def setDYPL( self, obj ):
        self.object = obj
        self.draw = False
        self.pointer = [0, 0, 270] # X, Y, Degree/Direction
        print("Got a DYPL instance: ")
        print(obj)



if __name__ == '__main__':
    import DYPL
    DYPL(MyJythonFile())
