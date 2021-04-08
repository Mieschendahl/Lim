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

    def __undo(self):
        if self.un:
            entry = self.un.pop()
            self.re.append(entry)
            return entry
        return "DONE"

    def __redo(self):
        if self.re:
            entry = self.re.pop()
            self.un.append(entry)
            return entry
        return "DONE"

    def undo(self):
        entry = "STOP"
        while entry == "STOP":
            entry = self.__undo()

        batch = []
        while entry not in ["STOP", "DONE"]:
            batch.append(entry)
            entry = self.__undo()

        if entry == "STOP":
            self.un.append(entry)
            self.re.pop()
        return batch

    def redo(self):
        entry = "STOP"
        while entry == "STOP":
            entry = self.__redo()

        batch = []
        while entry not in ["STOP", "DONE"]:
            batch.append(entry)
            entry = self.__redo()

        if entry == "STOP":
            self.re.append(entry)
            self.un.pop()
        return batch

    def undofile(self, fl):
        self.lock = True
        for entry in self.undo():
            x, y, pre, post = entry
            if post is None:
                fl.setposition(x, y)
                continue
            ch = post[File.char]
            fl.setposition(x, y)
            if ch == File.insertcode:
                fl.setchar(File.deletechar)
            elif ch == File.deletecode:
                fl.setchar(File.insertchar)
                fl.setchar(pre[:])
            else:
                fl.setchar(pre[:])
        self.lock = False

    def redofile(self, fl):
        self.lock = True
        for entry in self.redo():
            x, y, pre, post = entry
            if post is None:
                fl.setposition(x, y)
                continue
            ch = post[File.char]
            fl.setposition(x, y)
            fl.setchar(post)
        self.lock = False
