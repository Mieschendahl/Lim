import re
from Key import Key
from File import File
from Regex import NFA
from Display import Display

class Highlight:
    def __init__(self, groups):
        self.groups = groups

    def highlightall(self, fl):
        self.highlightallwords(fl)

    def highlight(self, fl):
        self.highlightwords(fl)

    def match(self, fl, words):
        lastposition = fl.getposition()
        for leftside, rightside, main in words:
            if fl.match(leftside, 1):
                leftwordposition = fl.getposition()
                for color, word in main:
                    if fl.match(word, 1):
                        rightwordposition = fl.getposition()
                        if fl.match(rightside, 1):
                            fl.setfromto(*leftwordposition, *rightwordposition, {"wordcolor" : color})
                        fl.setposition(*leftwordposition)
                fl.setposition(*lastposition)

    def highlightallwords(self, fl):
        fl.saveposition()
        for clear, leftborder, rightborder, words in self.groups:
            if clear is not None:
                fl.setall({"wordcolor" : clear})
                break
        fl.setposition(-1, 0)

        while True:
            for clear, leftborder, rightborder, words in self.groups:
                self.match(fl, words)
            fl.setlength(1)
            if not fl.contained():
                break
        fl.loadposition()

    def highlightwords(self, fl):
        fl.saveposition()
        lastposition = fl.getposition()
        for clear, leftborder, rightborder, words in self.groups:
            fl.match(leftborder, -1)
            fl.setlength(1)
            leftposition = fl.getposition()

            fl.setposition(*lastposition)
            fl.match(rightborder, 1)
            rightposition = fl.getposition()

            if clear is not None:
                fl.setfromto(*leftposition, *rightposition, {"wordcolor" : clear})
            fl.setposition(*leftposition)

            while not File.isbiggereq(*fl.getposition(), *rightposition):
                self.match(fl, words)
                fl.setlength(1)
            fl.setposition(*lastposition)
        fl.loadposition()

    def __highlightword(self, left, word, right, dct, fl, setall=True):
        x, y = fl.getposition()
        self.leftposition = self.rightposition = (x, y)

        fl.match(left, -1)
        fl.setlength(1)
        self.leftposition = fl.getposition()

        fl.setposition(x, y)
        fl.match(right, 1)
        self.rightposition = fl.getposition()
        fl.setposition(*self.leftposition)

        result = False
        while setall or not result:
            self.lastposition = fl.getposition()
            if File.isbiggereq(*self.lastposition, *self.rightposition):
                break

            if self.match(fl, word):
                result = True
                fl.setfromto(*self.leftwordposition, *self.rightwordposition, dct)
            else:
                fl.setlength(1)

        if not result:
            fl.setposition(x, y)
        return result

    def __highlightwords(self, fl):
        fl.saveposition()
        for left, word, right, color in self.words:
            self.highlightword(left, word, right, {"wordcolor" : color}, fl)
            fl.loadposition(True)
        fl.loadposition()

    def stringtoesc(string):
        if type(string) is list:
            return [Highlight.stringtoesc(substring) for substring in string]
        string = string.replace("\\n", "\n")
        string = string.replace("\\t", "\t")
        string = string.replace("a-Z", "a-zA-Z")
        string = string.replace("a-9", "a-zA-Z0-9")
        return string

    def rgbtocolor(rgbs):
        color = ""
        for rgb in rgbs.split():
            if not rgb:
                continue
            if rgb.isdigit():
                color += Display.rgb_to_ansi(*map(int, rgb[ : 3]), color != "")
            else:
                c = Display.color[rgb]
                color += Display.flipansi(c) if color != "" else c
        return color

    def sub(sub, string):
        if sub == string[ : len(sub)]:
            return len(sub)
        return -1

    def parsemain(lines):
        color = None
        greedy = ""
        words = []
        lines2, lines = lines[1 : ], [line[4 : ] for line in lines][1 : ]
        for index, line in enumerate(lines):
            if lines2[index][ : 4] != " " * 4:
                break

            i = Highlight.sub("color:", line)
            if i >= 0:
                color = Highlight.rgbtocolor(line[i : ])
            else:
                i = Highlight.sub("greedy:", line)
                if i >= 0:
                    greedy = "" if "False" == line[i : ] else "+"
                else:
                    words.append(line)

        if color is None:
            raise Exception("A color is missing!")

        return color, NFA.fromregex(greedy + "(" + "|".join(words) + ")")

    def parsewords(lines):
        leftside = None
        rightside = None
        main = []
        lines = [line[4 : ] for line in lines][1 : ]
        for index, line in enumerate(lines):
            if line[ : 1] in " ":
                continue

            i = Highlight.sub("leftside:", line)
            if i >= 0:
                leftside = NFA.fromregex(line[i : ])
            else:
                i = Highlight.sub("rightside:", line)
                if i >= 0:
                    rightside = NFA.fromregex(line[i : ])
                else:
                    i = Highlight.sub("main:", line)
                    if i >= 0:
                        main.append(Highlight.parsemain(lines[index : ]))
                    else:
                        break
        rightside = leftside if rightside is None else rightside
        leftside = rightside if leftside is None else leftside
        return leftside, rightside, main

    def parsegroup(string):
        clear = None
        leftborder = None
        rightborder = None
        words = []
        lines = [Highlight.stringtoesc(line[4 : ]) for line in string.split("\n")][1 : ]
        for index, line in enumerate(lines):
            if line[ : 1] in " ":
                continue

            i = Highlight.sub("leftborder:", line)
            if i >= 0:
                leftborder = NFA.fromregex(line[i : ])
            else:
                i = Highlight.sub("rightborder:", line)
                if i >= 0:
                    rightborder = NFA.fromregex(line[i : ])
                else:
                    i = Highlight.sub("clear:", line)
                    if i >= 0:
                        clear = Highlight.rgbtocolor(line[i : ])
                    else:
                        i = Highlight.sub("words:", line)
                        if i >= 0:
                            words.append(Highlight.parsewords(lines[index : ]))
                        else:
                            break
        rightborder = leftborder if rightborder is None else rightborder
        leftborder = rightborder if leftborder is None else leftborder
        return clear, leftborder, rightborder, words

    def fromfile(fileending):
        string = ""
        groups = []

        try:
            with open(Highlight.settingsdir + fileending + Highlight.colorschemeending, "r") as f:
                string = f.read()
        except FileNotFoundError:
            return Highlight(groups)

        string = "\n" + string + "\n"
        for match in re.finditer("group:", string):
            groups.append(Highlight.parsegroup(string[match.span()[0] : ]))
        return Highlight(groups)

if Key.system == "Linux":
    # Highlight.settingsdir = ".lim/"
    Highlight.settingsdir = "/mnt/d/source/Lim/.lim/"
else:
    # Highlight.settingsdir = ".lim/"
    Highlight.settingsdir = "D:/source/Lim/.lim/"

Highlight.colorschemeending = ".scheme"
