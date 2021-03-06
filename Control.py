import re
from File import File
from Regex import NFA
from Display import Display
from LoadSave import LoadSave

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
            fl.smartmove(-1, 0)

        def right():
            fl.smartmove(1, 0)

        def up():
            fl.smartmove(0, -1)

        def down():
            fl.smartmove(0, 1)

        def bigmiddle():
            limit = dp.height - 1
            half = limit // 2
            fl.set(None, dp.ybufferoffset + half)

        def bigleft():
            half = dp.width // 3
            if dp.xcursor > 0:
                fl.set(dp.xbufferoffset, None)
            else:
                fl.set(dp.xbufferoffset - half, None)

        def bigright():
            limit = dp.width - 1
            half = limit // 3
            if dp.xcursor < limit:
                fl.set(dp.xbufferoffset + limit, None)
            else:
                fl.set(dp.xbufferoffset + limit + half, None)

        def bigup():
            half = dp.height // 3
            if dp.ycursor > 0:
                fl.set(None, dp.ybufferoffset)
            else:
                fl.set(None, dp.ybufferoffset - half)

        def bigdown():
            limit = dp.height - 1
            half = limit // 3
            if dp.ycursor < limit:
                fl.set(None, dp.ybufferoffset + limit)
            else:
                fl.set(None, dp.ybufferoffset + limit + half)

        def offsetleft():
            l = fl.lencolumn()
            dp.xbufferoffset = max(0, dp.xbufferoffset - 1)
            x = fl.get()[0]
            fl.set(x - (x >= dp.xbufferoffset + dp.width), None)
            
        def offsetright():
            l = fl.lencolumn()
            dp.xbufferoffset = min(l, dp.xbufferoffset + 1)
            x = fl.get()[0]
            fl.set(x + (x < dp.xbufferoffset), None)

        def offsetup():
            l = fl.len()
            dp.ybufferoffset = max(0, dp.ybufferoffset - 1)
            y = fl.get()[1]
            fl.set(None, y - (y >= dp.ybufferoffset + dp.height))
            
        def offsetdown():
            l = fl.len()
            dp.ybufferoffset = min(l, dp.ybufferoffset + 1)
            y = fl.get()[1]
            fl.set(None, y + (y < dp.ybufferoffset))

        def startline():
            fl.set(0, 0)

        def endline():
            fl.setend()

        def startcolumn():
            fl.set(0, None)

        def endcolumn():
            fl.setcolumnend()

        def issaved():
            return LoadSave.issaved(self.lim.file, self.lim.path)

        def quit():
            if force or issaved():
                return False
            else:
                self.lim.cmdfile.cleardata()
                msg = "Quitting unsaved file needs force!"
                self.lim.cmdfile.setstring(msg, Display.color["red"])
                return True

        def newline():
            if default:
                endcolumn()
                fl.setchar("\n")
            else:
                startcolumn()
                fl.setchar("\n")
                fl.move(-1)

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

            y = fl.get()[1]
            _, y1, _, y2 = fl.getselection()
            for i in range(y1, y2 + 1):
                n = num
                fl.set(0, i)
                while n > 0:
                    fl.setchar(" ")
                    n -= 1
                while n < 0 and fl.getchar() == " ":
                    fl.setchar("")
                    n += 1

            fl.set(0, y)
            fl.seeknext(lambda a: a == " ", False)

        def paste():
            fl.setstring(self.copy)

        def deletechar():
            fl.setchar("")

        def copyselection():
            self.copy = fl.getstring(*fl.getselection())

        def deleteselection():
            x, y, x2, y2 = fl.getselection()
            fl.set(x2, y2)
            fl.move(1)
            while File.isbigger(*fl.get(), x, y):
                fl.setchar("")

        def nextword():
            fl.seeknext(lambda a: a not in " \n", False)
            fl.seeknext(lambda a: a in " \n", False)

        def wordend():
            if fl.getchar() not in " \n":
                fl.move(1)
            fl.seeknext(lambda a: a in " \n", False)
            fl.seeknext(lambda a: a not in " \n", False)
            fl.move(-1)

        def wordstart():
            if fl.getchar() not in " \n":
                fl.move(-1)
            fl.seekprevious(lambda a: a in " \n", False)
            fl.seekprevious(lambda a: a not in " \n", False)
            if not fl.boundleft():
                fl.move(1)

        def virtualcursor():
            fl.setvirtualcursor()

        def save():
            LoadSave.savefile(self.lim.file, self.lim.path)

        def undo():
            fl.log.undofile(fl)

        def redo():
            fl.log.redofile(fl)

        self.charbuffer = self.charbuffer[max(0, len(self.charbuffer) - Control.maxcharbuffer + 1) : ] + char

        if char == "\x03":
            return False

        elif char == "\t" and self.mode == "control":
            save()
            return False

        elif char == "\x1b":
            force = self.charbuffer[-2 : ] == "\x1b\x1b"
            return quit()

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
                fl.setselection(*fl.get(), *fl.get())

                if cmd[0].isupper():
                    x, y, x2, y2 = fl.getselection()
                    fl.setselection(0, y, fl.lencolumn(y2), y2)

            elif cmd in ["command", "queue"]:
                self.mode = "command"
                self.lim.cmdfile.cleardata()
                self.lim.currentdisplay = self.lim.cmddisplay
                self.lim.cmdfile.setchar(char if cmd == "queue" else ":")

                if cmd == "queue":
                    self.resetselection = False
                    if char in ["Y", "D", "C"]:
                        fl.setselection(0, fl.get()[1], fl.lencolumn(), fl.get()[1])
                        self.mode = "command"
                        self.handlechar("\r")

                    elif fl.getselection()[0] == -1:
                        fl.setselection(*(fl.get() * 2))

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
                fl.setstring("    ")

            elif cmd:
                exec(cmd + "()")

            else:
                fl.setchar(Control.convertchar.get(char, char))

        elif mode == "replace":
            fl = self.lim.file
            dp = self.lim.filedisplay
            cmd = self.replacedct.get(char, "")

            if cmd == "control":
                self.mode = "control"

            elif cmd == "tab":
                for _ in range(4):
                    if fl.getchar() == "\n":
                        fl.move(1)
                    else:
                        fl.resetchar(" ")
            elif cmd:
                exec(cmd + "()")

            elif char == "\x7f":
                fl.move(-1)
                if fl.getchar() != "\n":
                    fl.resetchar(" ")
                    fl.move(-1)

            elif char[0] != "\x1b":
                if fl.getchar() == "\n":
                    fl.move(1)
                else:
                    fl.resetchar(Control.convertchar.get(char, char))

            if self.mode == "replace":
                fl.move(-1)
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

            fl.setupperselection(*fl.get())

            if self.mode[0].isupper():
                x, y, x2, y2 = fl.getselection(False)
                if File.isbigger(x, y, x2, y2):
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
                ins2 = ins.split()
                force = False
                if ins and ins[0] == "!":
                    force = True
                    ins = ins[1 : ]

                cmdfound = True
                if ins == "":
                    pass # display status?
                elif ins2[0].isdigit():
                    x = int(ins2[1]) if len(ins2) > 1 and ins2[1].isdigit() else self.lim.file.smartget()[0]
                    self.lim.file.set(x, int(ins2[0]))
                elif ins in ["w", "write"]:
                    save()
                elif ins in ["re", "reload"]:
                    if force or issaved():
                        self.lim.loadfile()
                        self.lim.skipupdate = True
                        cmdfound = None
                    else:
                        self.lim.cmdfile.cleardata()
                        msg = "Reloading unsaved file needs force!"
                        self.lim.cmdfile.setstring(msg, Display.color["red"])
                        return True
                elif ins in ["rs", "restart"]:
                    if force or issaved():
                        self.lim.restart = True
                        return False
                    else:
                        self.lim.cmdfile.cleardata()
                        msg = "Restarting unsaved file needs force!"
                        self.lim.cmdfile.setstring(msg, Display.color["red"])
                        return True
                elif ins in ["x", "exit"]:
                    save()
                    return False
                elif ins in ["q", "quit"]:
                    return quit()
                elif ins[0] in ["<", ">"]:
                    fl = self.lim.file

                    span = re.match("[<>][0-9<>]*", ins).span()
                    ins, moves = ins[: span[1]], ins[span[1] : ]

                    fl.saveposition()
                    fl.set(*fl.getselection()[2 : ])
                    domoves()
                    fl.setupperselection(*fl.get())
                    fl.loadposition()

                    shiftselection()
                    fl.setselection()
                elif ins[0].lower() in ["y", "d", "c", "p"]:
                    lowins = ins[0].lower()
                    fl = self.lim.file

                    fl.saveposition() # immer noch buggyyy when man von unten nach oben deleted...
                    fl.set(*fl.getselection()[2 : ])
                    moves = ins[1 : ]
                    domoves()
                    fl.setupperselection(*fl.get())
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
                elif ins[0] in ["f"]:
                    fl = self.lim.file
                    nfa = NFA.fromregex(ins[1:])

                    fl.setlowerselection(*fl.get())
                    match = fl.match(nfa)
                    while fl.bound() and not match:
                        fl.move(1, False)
                        fl.setlowerselection(*fl.get())
                        match = fl.match(nfa)

                    if match:
                        fl.move(-1, False)
                        fl.setupperselection(*fl.get())
                        fl.move(1, False)
                    else:
                        fl.setselection()
                else:
                    cmdfound = False

                self.resetselection = True
                fl = self.lim.cmdfile
                if cmdfound is not None:
                    fl.setall({"usercolor" : Display.color["green" if cmdfound else "red"]})

            elif cmd == "control":
                self.lim.file.setselection()
                self.mode = "control"
                self.lim.cmdfile.cleardata()
                self.lim.currentdisplay = self.lim.filedisplay

            elif cmd == "tab":
                fl.setstring("    ")

            elif cmd:
                exec(cmd + "()")

            elif char[0] != "\x1b":
                fl.setchar(Control.convertchar.get(char, char))

            if fl.get()[0] == 0:
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
                      "\x7f" : "offsetleft",
                      "i" : "insert", ":" : "command", "r" : "replace", "R" : "Replace", "v" : "visual", "V" : "Visual",
                      "h" : "left", "l" : "right", "k" : "up", "j" : "down",
                      "H" : "bigleft", "L" : "bigright", "K" : "bigup", "J" : "bigdown", "M" : "bigmiddle",
                      "g" : "startline", "G" : "endline", "0" : "startcolumn", "$" : "endcolumn",
                      "PPAGE" : "startline", "NPAGE" : "endline",
                      "o" : "newline", "O" : "Newline", "A" : "endinsert", "I" : "startinsert",
                      "w" : "nextword", "e" : "wordend", "b" : "wordstart",
                      "x" : "deletechar", "p" : "paste", "\r" : "virtualcursor",
                      ">" : "queue", "<" : "queue", "y" : "queue", "d" : "queue", "Y" : "queue", "D" : "queue",
                      "C" : "queue", "c" : "queue", "f" : "queue", "u" : "undo", "U" : "redo"}

Control.insertdct = {"\t" : "control", "TAB" : "tab",
                     "LEFT" : "left", "RIGHT" : "right", "UP" : "up", "DOWN" : "down",
                     "SLEFT" : "bigleft", "SRIGHT" : "bigright", "SUP" : "bigup", "SDOWN" : "bigdown",
                     "\x08" : "offsetleft", "\x0c" : "offsetright", "\x0b" : "offsetup", "\n" : "offsetdown",
                     "KLEFT" : "offsetleft", "KRIGHT" : "offsetright",
                     "KUP" : "offsetup", "KDOWN" : "offsetdown",
                     "PPAGE" : "startline", "NPAGE" : "endline"}

Control.replacedct = {"\t" : "control", "TAB" : "tab", "\r" : "control",
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
                     "H" : "bigleft", "L" : "bigright", "K" : "bigup", "J" : "bigdown", "M" : "bigmiddle",
                     "g" : "startline", "G" : "endline", "0" : "startcolumn", "$" : "endcolumn",
                     "PPAGE" : "startline", "NPAGE" : "endline",
                     "w" : "nextword", "e" : "wordend", "b" : "wordstart"}

Control.commanddct = {"\t" : "control", "TAB" : "tab", "\r" : "execute",
                      "LEFT" : "left", "RIGHT" : "right", "SLEFT" : "bigleft", "SRIGHT" : "bigright"}

Control.convertchar = {"\r" : "\n", "\x7f" : ""}
