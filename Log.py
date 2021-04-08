from File import File

class Log:
    def __init__(self, condition=lambda x: False, limit=1000):
        self.condition = condition
        self.limit = limit
        self.un = []
        self.re = []
        self.lock = False

    def add(self, entry):
        if self.lock:
            return False
        self.re = []
        self.un.append(entry)
        if self.condition(entry):
            self.un.append("STOP")
        while len(self.un) > self.limit:
            self.un.pop(0)
        return True

    def undo(self):
        if self.un:
            entry = self.un.pop()
            self.re.append(entry)
            return entry
        return "DONE"

    def redo(self):
        if self.re:
            entry = self.re.pop()
            self.un.append(entry)
            return entry
        return "DONE"

    def undofile(self, fl):
        self.lock = True
        entry = "STOP"
        while entry == "STOP":
            entry = self.undo()

        while entry not in ["STOP", "DONE"]:
            x, y, pre, post = entry
            ch = post[File.char]

            fl.setposition(x, y)
            if ch == File.insertcode:
                fl.setchar(File.deletechar)
            elif ch == File.deletecode:
                fl.setchar(File.insertchar)
                fl.setchar(pre[:])
            else:
                fl.setchar(pre[:])

            entry = self.undo()
        self.lock = False

    def redofile(self, fl):
        self.lock = True
        entry = "STOP"
        while entry == "STOP":
            entry = self.redo()

        while entry not in ["STOP", "DONE"]:
            x, y, pre, post = entry
            ch = post[File.char]

            fl.setposition(x, y)
            fl.setchar(post)

            entry = self.redo()
        self.lock = False
