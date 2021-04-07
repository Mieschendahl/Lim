import re
from Key import Key
from Regex import NFA
from Display import Display

class Highlight:
    def __init__(self, words, starttonum, numtoendquote, numtocolor):
        self.words = words
        self.starttonum = starttonum
        self.numtoendquote = numtoendquote
        self.numtocolor = numtocolor

    def match(self, fl, word):
        leftword, mainword, rightword = word
        if fl.match(leftword, 1):
            self.leftwordposition = fl.getposition()
            if fl.match(mainword, 1):
                self.rightwordposition = fl.getposition()
                if fl.match(rightword, 1):
                    return True
        return False

    def highlightall(self, fl):
        self.highlightallwords(fl)
        self.highlightallquotes(fl)

    def highlightallwords(self, fl):
        fl.saveposition()
        fl.setposition(-1, 0)
        while True:
            self.lastposition = fl.getposition()
            for word in self.words[1 : ]:
                left, middle, right, color = word
                if self.match(fl, middle):
                    fl.setfromto(*self.leftwordposition, *self.rightwordposition, {"wordcolor" : color})
                fl.setposition(*self.lastposition)
            fl.setlength(1)

            if not fl.contained():
                break

        fl.loadposition()

    def highlightallquotes(self, fl):
        fl.saveposition()

        fl.setposition(-1, 0)
        self.highlightquotes(fl, True)

        fl.loadposition()

    def highlight(self, fl):
        self.highlightwords(fl)
        self.highlightquotes(fl)

    def highlightword(self, left, word, right, dct, fl, setall=True):
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
            if fl.isbiggereq(*self.lastposition, *self.rightposition):
                break

            if self.match(fl, word):
                result = True
                fl.setfromto(*self.leftwordposition, *self.rightwordposition, dct)
            else:
                fl.setposition(*self.lastposition)
                fl.setlength(1)

        if not result:
            fl.setposition(x, y)
        return result

    def highlightwords(self, fl):
        fl.saveposition()
        for left, word, right, color in self.words:
            self.highlightword(left, word, right, {"wordcolor" : color}, fl)
            fl.loadposition(True)
        fl.loadposition()

    def highlightquotes(self, fl, full=False):
        a = fl.getchar()

        x, y = fl.getposition()
        fl.setlength(-1)
        state = fl.getelement("quotemeta")[-1 : ]
        while fl.getelement("quotemeta")[-1 : ] in ["s", "e"]:
            fl.setlength(-1)
        startquote = fl.getelement("quotemeta")[ : -1]
        endquote = self.numtoendquote[startquote]
        color = fl.getelement("quotecolor")


        if endquote != "":
            left, middle, right = endquote
            if self.highlightword(left, middle, right, {}, fl):
                fl.setposition(*self.leftposition)
        else:
            for quote in self.starttonum:
                left, middle, right = quote
                if self.highlightword(left, middle, right, {}, fl):
                    fl.setposition(*self.leftposition)
                    break

        while True:
            self.lastposition = fl.getposition()
            quotemeta = fl.getelement("quotemeta")
            success = False
            if endquote != "":
                left, middle, right = endquote
                if self.match(fl, middle):
                    fl.setfromto(*self.lastposition, *self.rightwordposition, {"quotemeta" : startquote + "e", "quotecolor" : color})
                    startquote = ""
                    endquote = ""
                    color = ""
                    success = True
                else:
                    fl.setposition(*self.lastposition)
            else:
                for quote in self.starttonum:
                    left, middle, right = quote
                    if self.match(fl, middle):
                        startquote = self.starttonum[quote]
                        endquote = self.numtoendquote[startquote]
                        color = self.numtocolor[startquote]
                        success = True
                        fl.setfromto(*self.leftwordposition, *self.rightwordposition, {"quotemeta" : startquote + "s", "quotecolor" : color})
                        break
                    fl.setposition(*self.lastposition)

            if not success:
                fl.setposition(*self.lastposition)
                fl.setelement({"quotemeta" : startquote + ("m" if startquote else ""), "quotecolor" : color})
                fl.setlength(1)

                if fl.isbigger(*fl.getposition(), x, y):
                    if not fl.contained() or (not full and quotemeta[ : -1] == startquote and quotemeta[-1 : ] not in ["e", "s"]):
                        break
        fl.setposition(x, y)

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

    def fromfile(fileending):
        string = ""
        words = []
        starttonum = {}
        numtoendquote = {"" : ""}
        numtocolor = {}

        try:
            with open(Highlight.settingsdir + fileending + Highlight.colorschemeending, "r") as f:
                string = f.read()
        except FileNotFoundError:
            return Highlight(words, starttonum, numtoendquote, numtocolor)

        for span in [*re.finditer("<ignore.*?ignore>", string, re.DOTALL)][ : : -1]:
            span = span.span()
            string = string[ : span[0]] + string[span[1] : ]

        for group in re.findall("<word.*?word>", string, re.DOTALL):
            for line in Highlight.stringtoesc(group.split("\n")[1 : -1]):
                left, word, right, rgb = line.split("||")
                leftword, mainword, rightword = word.split("__")
                words.append((NFA.fromregex(left), (NFA.fromregex(leftword), NFA.fromregex(mainword), NFA.fromregex(rightword)), NFA.fromregex(right), Highlight.rgbtocolor(rgb)))

        n = 0
        start = None
        for group in re.findall("<quote.*?quote>", string, re.DOTALL):
            for line in Highlight.stringtoesc(group.split("\n")[1 : -1]):
                if start is None:
                    start = line
                    continue

                left, word, right, rgb = start.split("||")
                leftword, mainword, rightword = word.split("__")
                startquote = (NFA.fromregex(left), (NFA.fromregex(leftword), NFA.fromregex(mainword), NFA.fromregex(rightword)), NFA.fromregex(right))
                color = Highlight.rgbtocolor(rgb)

                left, word, right = line.split("||")
                leftword, mainword, rightword = word.split("__")
                endquote = (NFA.fromregex(left), (NFA.fromregex(leftword), NFA.fromregex(mainword), NFA.fromregex(rightword)), NFA.fromregex(right))

                start = None
                num, n = str(n), n + 1
                starttonum[startquote] = num
                numtoendquote[num] = endquote
                numtocolor[num] = color
        return Highlight(words, starttonum, numtoendquote, numtocolor)

if Key.system == "Linux":
    # Highlight.settingsdir = ".lim/"
    Highlight.settingsdir = "/mnt/d/source/Lim/.lim/"
else:
    # Highlight.settingsdir = ".lim/"
    Highlight.settingsdir = "D:/source/Lim/.lim/"

Highlight.colorschemeending = ".scheme"
