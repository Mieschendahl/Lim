from File import File

class Log:
    def __init__(self, unsep, resep, limit=1000):
        self.unsep = unsep
        self.resep = resep
        self.limit = limit
        self.un = []
        self.re = []
        self.lock = False

    def add(self, entry):
        if self.lock:
            return False
        self.re = []
        self.un.append(entry)
        while len(self.un) > self.limit:
            self.un.pop(0)
        return True

    def __undo(self):
        if self.un:
            entry = self.un.pop()
            self.re.append(entry)
            return entry
        return None

    def __redo(self):
        if self.re:
            entry = self.re.pop()
            self.un.append(entry)
            return entry
        return None

    def undo(self):
        batch = []
        while True:
            entry = self.__undo()
            if entry is None:
                break
            batch.append(entry)
            if self.unsep(batch):
                break
        return batch

    def redo(self):
        batch = []
        while True:
            entry = self.__redo()
            if entry is None:
                break
            batch.append(entry)
            if self.resep(batch):
                break
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
