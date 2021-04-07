import re
from Display import Display
from File import File

class Control:
    def __init__(self, lim):
        self.lim = lim
        self.charbuffer = ""
        self.controldct = Control.controldct
        self.insertdct = Control.insertdct
        self.replacedct = Control.replacedct
        self.visualdct = Control.visualdct
        self.commanddct = Control.commanddct
        self.copy = ""
        self.resetselection = True
        self.mode = "control"
        self.esccount = 0

    def handlechar(self, char):
        def left():
            fl.smartmoveposition(-1, 0)

        def right():
            fl.smartmoveposition(1, 0)

        def up():
            fl.smartmoveposition(0, -1)

        def down():
            fl.smartmoveposition(0, 1)

        def bigleft():
            half = dp.width // 3
            if dp.xcursor > 0:
                fl.smartsetx(dp.xbufferoffset)
            else:
                fl.smartsetx(dp.xbufferoffset - half)

        def bigright():
            limit = dp.width - 1
            half = limit // 3
            if dp.xcursor < limit:
                fl.smartsetx(dp.xbufferoffset + limit)
            else:
                fl.smartsetx(dp.xbufferoffset + limit + half)

        def bigup():
            half = dp.height // 3
            if dp.ycursor > 0:
                fl.smartsety(dp.ybufferoffset)
            else:
                fl.smartsety(dp.ybufferoffset - half)

        def bigdown():
            limit = dp.height - 1
            half = limit // 3
            if dp.ycursor < limit:
                fl.smartsety(dp.ybufferoffset + limit)
            else:
                fl.smartsety(dp.ybufferoffset + limit + half)

        def offsetleft():
            l = fl.lencolumn()
            dp.xbufferoffset = max(0, dp.xbufferoffset - 1)
            x = fl.getx()
            fl.smartsetx(x - (x >= dp.xbufferoffset + dp.width))
            
        def offsetright():
            l = fl.lencolumn()
            dp.xbufferoffset = min(l, dp.xbufferoffset + 1)
            x = fl.getx()
            fl.smartsetx(x + (x < dp.xbufferoffset))

        def offsetup():
            l = fl.len()
            dp.ybufferoffset = max(0, dp.ybufferoffset - 1)
            y = fl.gety()
            fl.smartsety(y - (y >= dp.ybufferoffset + dp.height))
            
        def offsetdown():
            l = fl.len()
            dp.ybufferoffset = min(l, dp.ybufferoffset + 1)
            y = fl.gety()
            fl.smartsety(y + (y < dp.ybufferoffset))

        def startline():
            fl.setposition(0, 0)

        def endline():
            fl.setend()

        def startcolumn():
            fl.setx(0)

        def endcolumn():
            fl.setcolumnend()

        def quit():
            if force or self.lim.file.issaved(self.lim.path):
                return False
            else:
                self.lim.cmdfile.cleardata()
                msg = "Quitting unsaved file needs force!"
                self.lim.cmdfile.smartsetstring(msg, Display.color["red"])
                return True

        def newline():
            if default:
                endcolumn()
                fl.smartsetchar(File.newlinecode)
            else:
                startcolumn()
                fl.smartsetchar(File.newlinecode)
                fl.setprevious()

        def endinsert():
            endcolumn()
            self.mode = "insert"
            
        def startinsert():
            startcolumn()
            self.mode = "insert"

        def domoves():
            m = self.mode
            self.mode = "control"
            for move in moves:
                self.handlechar(move)
            self.mode = m

        def shiftselection():
            num = 0
            if re.match("[<>][0-9]+", ins):
                num = int(ins[1 : ]) * (1 if ins[0] == ">" else -1)
            else:
                num = len(ins) - ins.count("<") * 2

            y = fl.gety()
            _, y1, _, y2 = fl.getselection()
            for i in range(y1, y2 + 1):
                n = num
                fl.setposition(0, i)
                while n > 0:
                    fl.setchar(File.insertchar)
                    n -= 1
                while n < 0 and fl.getchar() == " ":
                    fl.setchar(File.deletechar)
                    n += 1

            fl.setposition(0, y)
            fl.seeknext(lambda a: a == " ", False)

        def paste():
            fl.smartsetstring(self.copy)

        def deletechar():
            fl.setchar(File.deletechar)

        def copyselection():
            self.copy = fl.getstring(*fl.getselection())

        def deleteselection():
            x, y, x2, y2 = fl.getselection()
            fl.setposition(x2, y2)
            fl.setnext()
            while fl.isbigger(*fl.getposition(), x, y):
                fl.smartsetchar(File.deletecode)

        def nextword():
            fl.seeknext(lambda a: a not in " \n", False)
            fl.seeknext(lambda a: a in " \n", False)

        def wordend():
            if fl.getchar() not in " \n":
                fl.setnext()
            fl.seeknext(lambda a: a in " \n", False)
            fl.seeknext(lambda a: a not in " \n", False)
            fl.setprevious()

        def wordstart():
            if fl.getchar() not in " \n":
                fl.setprevious()
            fl.seekprevious(lambda a: a in " \n", False)
            fl.seekprevious(lambda a: a not in " \n", False)
            if not fl.boundleft():
                fl.setnext()

        def virtualcursor():
            fl.setvirtualcursor()

        self.charbuffer = self.charbuffer[max(0, len(self.charbuffer) - Control.maxcharbuffer + 1) : ] + char

        if char == "\x03":
            return False

        if char == "\x1b":
            force = self.charbuffer[-3 : ] == "\x1b\x1b\x1b"
            res = quit()

            self.esccount += 1
            self.lim.cmdfile.smartsetstring(" (" + str(self.esccount) + "/3)", Display.color["red"])
            return res
        else:
            self.esccount = 0

        mode = self.mode.lower()

        if mode == "control":
            fl = self.lim.file
            dp = self.lim.filedisplay
            cmd = self.controldct.get(char, "")

            if cmd == "paste" and fl.getselection()[0] != -1:
                cmd = "queue"

            if cmd == "insert":
                self.mode = "insert"

            elif cmd.lower() == "replace":
                self.mode = cmd

            elif cmd.lower() == "visual":
                self.resetselection = False
                self.mode = cmd
                fl.setselection(*fl.getposition(), *fl.getposition())

                if cmd[0].isupper():
                    x, y, x2, y2 = fl.getselection()
                    fl.setselection(0, y, fl.lencolumn(y2), y2)

            elif cmd in ["command", "queue"]:
                self.mode = "command"
                self.lim.cmdfile.cleardata()
                self.lim.currentdisplay = self.lim.cmddisplay

                if cmd == "queue":
                    self.lim.cmdfile.smartsetstring(char + " ")
                    self.resetselection = False
                    if char in ["Y", "D", "C"]:
                        fl.setselection(0, fl.gety(), fl.lencolumn(), fl.gety())
                        self.mode = "command"
                        self.handlechar("NEWLINE")

                    elif fl.getselection()[0] == -1:
                        fl.setselection(*(fl.getposition() * 2))
                else:
                    self.lim.cmdfile.smartsetchar(":")

            elif cmd.lower() == "newline":
                self.mode = "insert"
                default = cmd[0].islower()
                cmd = cmd.lower()
                newline()

            elif cmd:
                exec(cmd + "()")

            if self.resetselection:
                fl.setselection()
                self.resetselection = False

        elif mode == "insert":
            fl = self.lim.file
            dp = self.lim.filedisplay
            cmd = self.insertdct.get(char, "")

            if cmd == "control":
                self.mode = "control"

            elif cmd == "tab":
                fl.smartsetstring("    ")

            elif cmd:
                exec(cmd + "()")

            else:
                fl.smartsetchar(char)

        elif mode == "replace":
            fl = self.lim.file
            dp = self.lim.filedisplay
            cmd = self.replacedct.get(char, "")

            if cmd == "control":
                self.mode = "control"

            elif cmd == "tab":
                for _ in range(4):
                    if fl.getchar() != "\n":
                        fl.setchar(File.completechar(" "))
                    if not fl.setnext():
                        break

            elif cmd:
                exec(cmd + "()")

            elif char == "BACKSPACE":
                fl.setprevious()
                if fl.getchar() != "\n":
                    fl.setchar(File.completechar(" "))

            elif char[0] != "\x1b":
                if fl.getchar() != "\n":
                    fl.setchar(File.completechar(char))
                fl.setnext()

            if self.mode[0].islower():
                fl.setprevious()
                self.mode = "control"

        elif mode == "visual":
            fl = self.lim.file
            dp = self.lim.filedisplay
            cmd = self.visualdct.get(char, "")

            if cmd:
                exec(cmd + "()")

            else:
                self.resetselection = True
                self.mode = "control"
                self.handlechar(char)
                return True

            fl.setupperselection(*fl.getposition())

            if self.mode[0].isupper():
                x, y, x2, y2 = fl.getselection(False)
                if fl.isbigger(x, y, x2, y2):
                    fl.setselection(fl.lencolumn(y), y, 0, y2)
                else:
                    fl.setselection(0, y, fl.lencolumn(y2), y2)

        elif mode == "command":
            fl = self.lim.cmdfile
            dp = self.lim.cmddisplay
            cmd = self.commanddct.get(char, "")

            if cmd == "execute":
                self.mode = "control"
                self.lim.currentdisplay = self.lim.filedisplay

                ins = fl.getstring().lstrip(":").rstrip("\n") # ins for instruction
                force = False
                if ins and ins[0] == "!":
                    force = True
                    ins = ins[1 : ]

                cmdfound = True
                if ins == "":
                    pass # display status?
                elif ins in ["w", "write"]:
                    self.lim.file.savefile(self.lim.path)
                elif ins in ["re", "reload"]:
                    if force or self.lim.file.issaved(self.lim.path):
                        self.lim.loadfile()
                        self.lim.skipupdate = True
                        cmdfound = None
                    else:
                        self.lim.cmdfile.cleardata()
                        msg = "Reloading unsaved file needs force!"
                        self.lim.cmdfile.smartsetstring(msg, Display.color["red"])
                        return True
                elif ins in ["rs", "restart"]:
                    if force or self.lim.file.issaved(self.lim.path):
                        self.lim.restart = True
                        return False
                    else:
                        self.lim.cmdfile.cleardata()
                        msg = "Restarting unsaved file needs force!"
                        self.lim.cmdfile.smartsetstring(msg, Display.color["red"])
                        return True
                elif ins in ["x", "exit"]:
                    self.lim.file.savefile(self.lim.path)
                    return False
                elif ins in ["q", "quit"]:
                    return quit()
                elif ins[0] in ["<", ">"]:
                    fl = self.lim.file

                    span = re.match("[<>][0-9<>]*", ins).span()
                    ins, moves = ins[: span[1]], ins[span[1] : ]

                    fl.saveposition()
                    fl.setposition(*fl.getselection()[2 : ])
                    domoves()
                    fl.setupperselection(*fl.getposition())
                    fl.loadposition()

                    shiftselection()
                    fl.setselection()
                elif ins[ : 2].lower() in ["y ", "d ", "c ", "p "]:
                    lowins = ins[0].lower()
                    fl = self.lim.file

                    fl.saveposition()
                    fl.setposition(*fl.getselection()[2 : ])
                    moves = ins[2 : ]
                    domoves()
                    fl.setupperselection(*fl.getposition())
                    fl.loadposition()

                    if lowins not in ["p"]:
                        copyselection()

                    if lowins in ["d", "c", "p"]:
                        deleteselection()
                        fl.setselection()

                        if ins[0].lower() == "c":
                            self.mode = "insert"

                    if lowins in ["p"]:
                        paste()
                else:
                    cmdfound = False

                self.resetselection = True
                fl = self.lim.cmdfile
                if cmdfound is not None:
                    fl.smartsetfromto(0, 0, {"usercolor" : Display.color["green" if cmdfound else "red"]})

            elif cmd == "control":
                self.lim.file.setselection()
                self.mode = "control"
                self.lim.cmdfile.cleardata()
                self.lim.currentdisplay = self.lim.filedisplay

            elif cmd == "tab":
                fl.smartsetstring("    ")

            elif cmd:
                exec(cmd + "()")

            elif char[0] != "\x1b":
                fl.smartsetchar(char)

            if fl.getx() == 0:
                self.lim.file.setselection()
                self.mode = "control"
                self.lim.cmdfile.cleardata()
                self.lim.currentdisplay = self.lim.filedisplay

        else:
            raise Exception("Wrong mode: '" + repr(self.mode) + "'")

        return True

Control.maxcharbuffer = 100

Control.controldct = {"LEFT" : "left", "RIGHT" : "right", "UP" : "up", "DOWN" : "down",
                      "SLEFT" : "bigleft", "SRIGHT" : "bigright", "SUP" : "bigup", "SDOWN" : "bigdown",
                      "KLEFT" : "offsetleft", "KRIGHT" : "offsetright",
                      "KUP" : "offsetup", "KDOWN" : "offsetdown",
                      "\x08" : "offsetleft", "\x0c" : "offsetright", "\x0b" : "offsetup", "\n" : "offsetdown",
                      "BACKSPACE" : "offsetleft",
                      "i" : "insert", ":" : "command", "r" : "replace", "R" : "Replace", "v" : "visual", "V" : "Visual",
                      "h" : "left", "l" : "right", "k" : "up", "j" : "down",
                      "H" : "bigleft", "L" : "bigright", "K" : "bigup", "J" : "bigdown",
                      "g" : "startline", "G" : "endline", "0" : "startcolumn", "$" : "endcolumn",
                      "PPAGE" : "startline", "NPAGE" : "endline",
                      "o" : "newline", "O" : "Newline", "A" : "endinsert", "I" : "startinsert",
                      "w" : "nextword", "e" : "wordend", "b" : "wordstart",
                      "x" : "deletechar", "p" : "paste", "NEWLINE" : "virtualcursor",
                      ">" : "queue", "<" : "queue", "y" : "queue", "d" : "queue", "Y" : "queue", "D" : "queue",
                      "C" : "queue", "c" : "queue"}

Control.insertdct = {"\t" : "control", "TAB" : "tab",
                     "LEFT" : "left", "RIGHT" : "right", "UP" : "up", "DOWN" : "down",
                     "SLEFT" : "bigleft", "SRIGHT" : "bigright", "SUP" : "bigup", "SDOWN" : "bigdown",
                     "\x08" : "offsetleft", "\x0c" : "offsetright", "\x0b" : "offsetup", "\n" : "offsetdown",
                     "KLEFT" : "offsetleft", "KRIGHT" : "offsetright",
                     "KUP" : "offsetup", "KDOWN" : "offsetdown",
                     "PPAGE" : "startline", "NPAGE" : "endline"}

Control.replacedct = {"\t" : "control", "TAB" : "tab", "NEWLINE" : "control",
                      "PPAGE" : "startline", "NPAGE" : "endline",
                      "LEFT" : "left", "RIGHT" : "right", "UP" : "up", "DOWN" : "down",
                      "SLEFT" : "bigleft", "SRIGHT" : "bigright", "SUP" : "bigup", "SDOWN" : "bigdown",
                      "\x08" : "offsetleft", "\x0c" : "offsetright", "\x0b" : "offsetup", "\n" : "offsetdown",
                      "KLEFT" : "offsetleft", "KRIGHT" : "offsetright",
                      "KUP" : "offsetup", "KDOWN" : "offsetdown"}

Control.visualdct = {"LEFT" : "left", "RIGHT" : "right", "UP" : "up", "DOWN" : "down",
                     "SLEFT" : "bigleft", "SRIGHT" : "bigright", "SUP" : "bigup", "SDOWN" : "bigdown",
                     "KLEFT" : "offsetleft", "KRIGHT" : "offsetright",
                     "KUP" : "offsetup", "KDOWN" : "offsetdown",
                     "\x08" : "offsetleft", "\x0c" : "offsetright", "\x0b" : "offsetup", "\n" : "offsetdown",
                     "h" : "left", "l" : "right", "k" : "up", "j" : "down",
                     "H" : "bigleft", "L" : "bigright", "K" : "bigup", "J" : "bigdown",
                     "g" : "startline", "G" : "endline", "0" : "startcolumn", "$" : "endcolumn",
                     "PPAGE" : "startline", "NPAGE" : "endline",
                     "w" : "nextword", "e" : "wordend", "b" : "wordstart"}

Control.commanddct = {"\t" : "control", "TAB" : "tab", "NEWLINE" : "execute",
                      "LEFT" : "left", "RIGHT" : "right", "SLEFT" : "bigleft", "SRIGHT" : "bigright"}
