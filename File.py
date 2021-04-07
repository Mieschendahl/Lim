import sys, os, errno, hashlib
from Regex import NFA
from Display import Display
from Highlight import Highlight

class File:
    def __init__(self, highlight=None):
        self.highlight = [] if highlight is None else highlight
        self.setposition(0, 0)
        self.setselection()
        self.setvirtualcursor(False)
        self.changed = False

        self.data = [[File.endchar[:]]]
        self.positionstack = []
        self.flags = []

    # Getter
    # ======

    def issaved(self, path):
        charstring = File.compressdata(self.data, File.char, False)
        newhexhash = hashlib.md5(charstring.encode("utf-8")).hexdigest()

        try:
            if not {"new file", "new meta"} & set(self.flags):
                dirname, filename = os.path.split(path)
                with open(File.metadir + filename + ".meta", "r") as f:
                    string = f.read()

                charstring = File.compressdata(self.data, File.char, False)
                metastring = File.compressdata(self.data, File.usercolor, True)
                newhexhash = hashlib.md5((charstring + metastring).encode("utf-8")).hexdigest()
        except:
            pass

        return self.hexhash == newhexhash

    def ischanged(self):
        return self.changed

    def iscleared(self):
        return not (len(self.data) > 1 or len(self.data[0]) > 1)

    def len(self):
        return len(self.data)

    def lencolumn(self, y=None):
        y = self.y if y is None else y
        return len(self.data[y])

    def maxlencolumn(self, a=0, b=0):
        if b:
            return max(map(len, self.data[a : b]))
        return max(map(len, self.data[a :]))

    def lenchars(self):
        return sum(len(line) for line in self.data)

    def getselection(self, ordered=True):
        if ordered and self.isbigger(self.sx, self.sy, self.sx2, self.sy2):
            return self.sx2, self.sy2, self.sx, self.sy
        return self.sx, self.sy, self.sx2, self.sy2

    def getdata(self):
        return self.data

    def copydata(self):
        return [[char.copy() for char in line] for line in self.data]

    def saveposition(self):
        self.positionstack.append((self.x, self.y, self.smartx, self.smarty))

    def getposition(self):
        return self.x, self.y

    def smartgetposition(self):
        if self.virtualcursor:
            return self.smartx, self.smarty

        return self.x, self.y

    def getx(self):
        return self.getposition()[0]

    def gety(self):
        return self.getposition()[1]

    def contained(self):
        return self.y >= 0 and self.y < len(self.data) and self.x >= 0 and self.x < len(self.data[self.y])

    def boundleft(self):
        return self.y == 0 and self.x <= 0

    def boundright(self):
        return self.y + 1 >= len(self.data) and self.x + 1 >= len(self.data[self.y])

    def getchar(self, meta=False):
        if self.contained():
            char = self.data[self.y][self.x]
        else:
            char = File.endchar[:]

        if meta:
            return char
        return char[meta]

    def getelement(self, element):
        return self.getchar(True)[File.elementdct[element]]

    def getstring(self, x=0, y=0, x2=-1, y2=-1, meta=False):
        self.saveposition()
        self.setposition(x, y)
        metastring = []
        string = ""

        while x2 == -1 or not self.isbigger(*self.getposition(), x2, y2):
            char = self.getchar(True)
            string += char[File.char]
            metastring.append(char)

            if not self.setnext():
                break
        self.loadposition()

        if meta:
            return string, metastring
        return string

    def getfromposition(self, x, y, element):
        self.saveposition()
        self.setposition(x, y)
        element = self.getelement(element)
        self.loadposition()
        return element

    def notescaped(self):
        self.file.saveposition()
        switch = True
        while self.setprevious() and self.getchar() == "\\":
            switch = not switch
        self.loadposition()
        return switch

    def isbigger(self, x, y, x2, y2):
        return y > y2 or (y == y2 and x > x2)

    def isbiggereq(self, x, y, x2, y2):
        return y > y2 or (y == y2 and x >= x2)

    # Setter
    # ======

    def cleardata(self):
        self.setposition(0, 0)
        while self.len() > 1 or self.lencolumn() > 1:
            self.setchar(File.deletechar)

    def loadposition(self, keep=False):
        if keep:
            self.x, self.y, self.smartx, self.smarty = self.positionstack[-1]
        else:
            self.x, self.y, self.smartx, self.smarty = self.positionstack.pop()

    def dropposition(self):
        self.positionstack.pop()

    def setselection(self, x=-1, y=-1, x2=-1, y2=-1):
        self.sx, self.sy, self.sx2, self.sy2 = x, y, x2, y2

    def setlowerselection(self, x, y):
        self.setselection(x, y, self.sx2, self.sy2)

    def setupperselection(self, x2, y2):
        self.setselection(self.sx, self.sy, x2, y2)

    def setvirtualcursor(self, virtualcursor=None):
        if virtualcursor is None:
            self.virtualcursor = not self.virtualcursor
        else:
            self.virtualcursor = virtualcursor

    def setposition(self, x, y):
        self.x = x
        self.y = y
        self.smartx = x
        self.smarty = y

    def setx(self, x):
        self.setposition(x, self.y)

    def sety(self, y):
        self.setposition(self.x, y)

    def moveposition(self, dx, dy):
        self.setposition(self.x + dx, self.y + dy)

    def smartsetposition(self, x, y): # Should I let this be based on setposition?
        x, y = max(0, x), max(0, y)
        self.y = min(len(self.data) - 1, y)
        self.x = min(len(self.data[self.y]) - 1, x)
        self.smartx = x
        self.smarty = y

    def smartsetx(self, x):
        self.smartsetposition(x, self.smarty)

    def smartsety(self, y):
        self.smartsetposition(self.smartx, y)

    def smartmoveposition(self, dx, dy):
        if self.virtualcursor:
            return self.smartsetposition(self.smartx + dx, self.smarty + dy)

        self.smarty = max(0, min(len(self.data) - 1, self.smarty + dy))
        if dx:
            ylen = len(self.data[self.smarty]) - 1
            self.smartx = max(0, min(ylen, min(ylen, self.smartx) + dx))
        self.smartsetposition(self.smartx, self.smarty)

    def setend(self):
        y = len(self.data) - 1
        self.setposition(len(self.data[y]) - 1, y)

    def setcolumnend(self):
        self.setx(len(self.data[self.y]) - 1)

    def setprevious(self):
        x, y = self.x, self.y
        if x - 1 >= 0:
            x -= 1
        elif y - 1 >= 0:
            x = len(self.data[self.y - 1]) - 1
            y -= 1
        else:
            return False
        self.setposition(x, y)
        return True

    def setnext(self):
        x, y = self.x, self.y
        if x + 1 < len(self.data[self.y]):
            x += 1
        elif y + 1 < len(self.data):
            x = 0
            y += 1
        else:
            return False
        self.setposition(x, y)
        return True

    def setlength(self, length, edge=False):
        while length > 0:
            if not self.setnext():
                if not edge:
                    self.moveposition(length, 0)
                return False
            length -= 1
        while length < 0:
            if not self.setprevious():
                if not edge:
                    self.moveposition(length, 0)
                return False
            length += 1
        return True

    # Nur setchar zu loggen (mit Koordinaten) ist warscheinlich sehr viel effizienter und eleganter
    def setchar(self, char):
        ch = char[File.char]

        if ch == File.insertcode:
            self.data[self.y].insert(self.x, File.newchar[:])
        elif ch == File.deletecode:
            if self.y + 1 == len(self.data) and self.x + 1 == len(self.data[self.y]):
                return False
            if self.getchar() == "\n":
                self.data[self.y].extend(self.data.pop(self.y + 1))
            self.data[self.y].pop(self.x)
        elif ch == File.newlinecode:
            self.data.insert(self.y + 1, self.data[self.y][self.x + 1 : ])
            self.data[self.y] = self.data[self.y][ : self.x] + [File.endchar[:]]
        else:
            if self.y + 1 == len(self.data) and self.x + 1 == len(self.data[self.y]):
                return False
            current = self.getchar()
            self.data[self.y][self.x] = char
            if current == "\n":
                self.data[self.y].extend(self.data.pop(self.y + 1))

        if self.highlight:
            self.highlight.highlight(self)

        self.changed = True
        return True

    def smartsetchar(self, char):
        if type(char) is str and len(char) > 1 and char not in File.chartocmd:
            return False

        if type(char) is not list:
            char = File.completechar(char)

        ch = char[File.char] = File.chartocmd.get(char[File.char], char[File.char])
        if ch == File.deletecode:
            self.setprevious()
            self.setchar(File.deletechar)
        elif ch == File.newlinecode:
            self.setchar(File.insertchar)
            self.setchar(File.newlinechar)
            self.setnext()
        else:
            self.setchar(File.insertchar)
            self.setchar(char)
            self.setnext()

    def smartsetstring(self, string, color=""):
        for char in string:
            char = File.completechar(char)
            char[File.usercolor] = color
            self.smartsetchar(char)

    def setelement(self, dct):
        if {"char"} & dct.keys():
            raise Exception("Can't set usercolor and char with 'setfrom' since changes aren't logged.")

        for key in dct:
            self.getchar(True)[File.elementdct[key]] = dct[key]

    def setfromposition(self, x, y, dct):
        self.saveposition()
        self.setposition(x, y)
        self.setelement(dct)
        self.loadposition()

    def setfromto(self, x, y, x2, y2, dct):
        if {"char"} & dct.keys():
            raise Exception("Can't set usercolor and char with 'setfrom' since changes aren't logged.")

        self.setposition(x, y)
        while not self.isbiggereq(*self.getposition(), x2, y2):
            char = self.getchar(True)
            for key in dct:
                char[File.elementdct[key]] = dct[key]
            if not self.setlength(1):
                return False
        return True

    def smartsetfromto(self, x, y, dct, x2=None, y2=None, length=0):
        if x2 is None:
            y2 = len(self.data) - 1
            x2 = len(self.data[y2])
        self.setposition(x, y)
        self.setlength(length)
        self.setfromto(*self.getposition(), x2, y2, dct)

    def seekprevious(self, condition, full=True):
        distance = 0
        while condition(self.getchar(full)):
            distance += 1
            if not self.setprevious():
                return -1
        return distance

    def seeknext(self, condition, full=True):
        distance = 0
        while condition(self.getchar(full)):
            distance += 1
            if not self.setnext():
                return -1
        return distance

    def match(self, regex, stride=1, prefix=True):
        return regex.filerun(self, prefix, stride)

    def savefile(self, path):
        charstring = File.compressdata(self.data, File.char, False)
        dirname, filename = os.path.split(path)
        File.createpath(dirname)
        with open(path, "w") as f:
           f.write(charstring)

        metastring = File.compressdata(self.data, File.usercolor, True)
        version = "Version:\n" + str(File.version) + "\n"
        self.hexhash = hashlib.md5((charstring + metastring).encode("utf-8")).hexdigest()
        hexhash = "Hash:\n" + self.hexhash + "\n"
        metastring = "Metadata:\n" + metastring + "\n"
        string = File.seperator1.join([version, hexhash, metastring])

        metapath = File.metadir
        File.createpath(File.metadir)
        with open(File.metadir + filename + ".meta", "w") as f:
            f.write(string)

    # classmethods
    # ============

    def completechar(char):
        return [char] + [""] * File.charsize

    def compressdata(data, axis, dynamicsize):
        string = []
        counter = 0
        for line in data:
            for char in line:
                ch = char[axis]
                if dynamicsize and ch == "":
                    counter += 1
                else:
                    if counter:
                        string.append(str(counter))
                        counter = 0
                    string.append(ch)
        if counter:
            string.append(str(counter))

        if dynamicsize:
            return File.seperator0.join(string)
        return "".join(string)

    def decompressdata(string, data, axis, dynamicsize):
        rawdata = string.split(File.seperator0)
        i = 0
        counter = 0
        for line in data:
            for char in line:
                if counter:
                    counter -= 1
                else:
                    if dynamicsize and rawdata[i].isdigit():
                        counter = int(rawdata[i])
                    else:
                        char[axis] = rawdata[i]
                        i += 1

    def createpath(dirname):
        if dirname and not os.path.exists(dirname):
            try:
                os.makedirs(dirname)
            except OSError as e:
                if e.errno != errno.EEXIST:
                    raise e

    def loadfile(path, plain):
        dirname, filename = os.path.split(path)
        fl = File(Highlight.fromfile(os.path.splitext(path)[1][1 : ]))

        try:
            charstring = ""
            with open(path, "r") as f:
                charstring = f.read()

            data = []
            line = []
            for char in charstring:
                line.append(File.completechar(char))
                if char == "\n":
                    data.append(line)
                    line = []

            fl.data = data
            fl.data = fl.data if fl.data else [[File.endchar[:]]]
            fl.hexhash = hashlib.md5((charstring).encode("utf-8")).hexdigest()

            try:
                string = ""
                with open(File.metadir + filename + ".meta", "r") as f:
                    string = f.read()

                version, hexhash, metastring = string.split(File.seperator1)
                version = version[len("Version:\n"): -1]
                hexhash = hexhash[len("Hash:\n"): -1]
                metastring = metastring[len("Metadata:\n"): -1]
                newhexhash = hashlib.md5((charstring + metastring).encode("utf-8")).hexdigest()

                if version != str(File.version):
                    raise Exception("Version missmatch, file '%s' with own '%s'." % (version, str(File.version)))

                if hexhash != newhexhash:
                    raise Exception("File was changed, hash does not match old.")

                data = fl.copydata()
                File.decompressdata(metastring, data, File.usercolor, True)

                fl.data = data
                fl.hexhash = hexhash
            except:
                fl.flags += ["new meta"]

        except FileNotFoundError as e:
            fl.data = [[File.endchar[:]]]
            fl.hexhash = hashlib.md5(("\n").encode("utf-8")).hexdigest()
            fl.flags += ["new file"]

        fl.highlight.highlightall(fl)

        return fl

File.seperator0 = "\x1b\t"
File.seperator1 = "\x1b\n"

File.version = 1.0
File.charsize = 4

File.insertcode = "insert"
File.deletecode = "delete"
File.newlinecode = "newline"
File.insertchar = File.completechar(File.insertcode)
File.deletechar = File.completechar(File.deletecode)
File.newlinechar = File.completechar(File.newlinecode)
File.newchar = File.completechar(" ")
File.endchar = File.completechar("\n")
File.chartocmd = {"BACKSPACE" : File.deletecode, "NEWLINE" : File.newlinecode, "\n" : File.newlinecode,
                  File.deletecode : File.deletecode, File.newlinecode : File.newlinecode, File.insertcode : File.insertcode}

File.char = 0
File.usercolor = 1
File.quotecolor = 2
File.wordcolor = 3
File.quotemeta = 4
File.elementdct = {"char" : File.char, "usercolor" : File.usercolor, "quotecolor" : File.quotecolor,
                   "wordcolor" : File.wordcolor, "quotemeta" : File.quotemeta}

File.loggedelements = {File.char, File.usercolor}

File.metadir = ".meta/"
