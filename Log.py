from File import File

class Log:
    def __init__(self, sep, limit=1000):
        self.sep = sep
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

    def undo(self):
        index = self.sep.undex(self.un, self.re)
        self.un, batch = self.un[ : index], self.un[index : ][ : : -1]
        self.re.extend(batch)
        return batch

    def redo(self):
        index = self.sep.redex(self.re, self.un)
        self.re, batch = self.re[ : index], self.re[index : ][ : : -1]
        self.un.extend(batch)
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
                fl.setchar("")
            elif ch == File.deletecode:
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
            fl.setchar(post[:])
        self.lock = False
