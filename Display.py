import sys, time

class Display:
    def __init__(self, width, height, xoffset=0, yoffset=0, reversehori=False, reversevert=False, effects=None):
        self.width = width
        self.height = height
        self.xoffset = xoffset
        self.yoffset = yoffset
        self.reversehori = reversehori
        self.reversevert = reversevert
        self.effects = effects if effects else []

        self.xbufferoffset = 0
        self.ybufferoffset = 0
        self.xcursor = 0
        self.ycursor = 0

    def getsize(self):
        return self.width, self.height

    def getcursor(self):
        return self.xcursor, self.ycursor

    def getbufferoffset(self):
        return self.xbufferoffset, self.ybufferoffset

    def fillwindow(self, value=" "):
        for i in range(self.yoffset, Display.height):
            row = Display.data[i]
            for j in range(self.xoffset, Display.width):
                row[j] = value

    def setbufferoffset(self, x, y):
        if x < self.xbufferoffset:
            self.xbufferoffset = x
        elif x + 1 >= self.xbufferoffset + self.width:
            self.xbufferoffset = x + 1 - self.width

        self.xcursor = x - self.xbufferoffset

        if y < self.ybufferoffset:
            self.ybufferoffset = y
        elif y + 1 >= self.ybufferoffset + self.height:
            self.ybufferoffset = y + 1 - self.height

        self.ycursor = y - self.ybufferoffset

    # The apply functions won't work in async mode, without coping the data.
    def applyfile(self, fl):
        # data = [[char[:] for char in line] for line in fl.getdata()]
        data = fl.getdata()
        x, y = fl.smartgetposition()
        x1, y1, x2, y2 = fl.getselection()
        x1 -= self.xbufferoffset
        y1 -= self.ybufferoffset
        x2 -= self.xbufferoffset
        y2 -= self.ybufferoffset
        self.setbufferoffset(x, y)

        yoffset = self.yoffset
        if self.reversevert:
            yoffset = max(0, self.height - self.yoffset - fl.len())
        rows = min(fl.len() - self.ybufferoffset, self.height - yoffset)

        xoffset = self.xoffset
        if self.reversehori:
            xoffset = max(0, self.width - self.xoffset - fl.maxlencolumn(self.ybufferoffset, self.ybufferoffset + self.height) + 1)
        self.xcursoroffset = xoffset
        self.ycursoroffset = yoffset
        i = 0
        while i < rows:
            line = data[i + self.ybufferoffset]
            columns = min(len(line) - self.xbufferoffset, self.width - xoffset)
            j = 0
            while j < columns:
                char = line[j + self.xbufferoffset][:]
                pre = ""
                    
                if (i > y1 or (i == y1 and j >= x1)) and (i < y2 or (i == y2 and j <= x2)):
                    pre = Display.color["black"] + Display.color["greyback"]
                    if char[0] == "\n":
                        char[0] = "^"

                if char[0] == "\n":
                    char[0] = " "

                elif char[0] == "\x1b":
                    char[0] = Display.color["cyan"] + "µ"

                Display.data[i + yoffset][j + xoffset] = pre + char[3] + char[2] + char[1] + char[0]
                j += 1
            i += 1

    def outputcursor(self):
        return Display.translate(self.xcursor + self.xcursoroffset, self.ycursor + self.ycursoroffset)

    def rgb_to_ansi(r, g, b, background=False):
        return "\x1b[%d;5;%dm" % (48 if background else 38, 16 + 36 * round(r) + 6 * round(g) + round(b))

    def grey_to_ansi(v, background=False):
        return "\x1b[%d;5;%dm" % (48 if background else 38, 232 + v)

    def flipansi(ansi):
        return ansi[ : 2] + ("3" if ansi[3] == "4" else "4") + ansi[3 : ]

    def translate(x, y):
        return "\x1b[%d;%dH" % (y + 1, x + 1)

    def showscreen():
        return Display.buffer1
        
    def hidescreen():
        return Display.buffer2

    def showcursor():
        return Display.cursor1
        
    def hidecursor():
        return Display.cursor2

    def setdisplay(width, height, xoffset=0, yoffset=0):
        Display.width, Display.height, Display.xoffset, Display.yoffset = width, height, xoffset, yoffset
        Display.data = [[" "] * Display.width for _ in range(Display.height)]

    def filldisplay(value=" "):
        for row in Display.data:
            for j, char in enumerate(row):
                row[j] = value

    def applycross(x, y):
        for i in range(Display.height):
            Display.data[i][x] = Display.crosscolor + Display.data[i][x] + Display.normal
        for j in range(Display.width):
            Display.data[y][j] = Display.crosscolor + Display.data[y][j]
        Display.data[y][Display.width - 1] += Display.normal

    def outputdisplay():
        output = Display.normal
        lastcolor = ""
        i = 0

        for line in Display.data:
            output += Display.translate(Display.xoffset, Display.yoffset + i)
            for char in line:
                char, color = char[-1], char[ : -1]

                if lastcolor != color:
                    output += color if color else Display.normal
                    lastcolor = color

                output += char
            i += 1
        return output

    def startloading(width):
        Display.loading = True

        wheel = ["Loading |", "Loading /", "Loading -", "Loading \\"]
        # wheel = ["Loading .|", "Loading ../", "Loading ...-", "Loading ..\\"]
        i = 0
        while Display.loading:
            l = max(0, width - len(wheel[i]))
            sys.stdout.write("\x1b[%dD" % width + wheel[i] + " " * l + "\x1b[%dD" % (l - 1))
            sys.stdout.flush()

            i = (1 + i) % len(wheel)
            time.sleep(0.1)

        sys.stdout.write("\x1b[2K\x1b[%dD" % width)
        sys.stdout.flush()

    def stoploading(thread):
        if Display.loading:
            Display.loading = False
            thread.join()

Display.cursor1 = "\x1b[?25h"
Display.cursor2 = "\x1b[?25l"

Display.buffer1 = "\x1b[?1049h"
Display.buffer2 = "\x1b[?1049l"

Display.normal = "\x1b[0m"
Display.crosscolor = Display.grey_to_ansi(7, True)

Display.color = {"grey" : Display.rgb_to_ansi(3, 3, 3), "white" : Display.rgb_to_ansi(5, 5, 5),
                 "red" : Display.rgb_to_ansi(4, 1, 1), "blue" : Display.rgb_to_ansi(2, 3, 5),
                 "green" : Display.rgb_to_ansi(1, 4, 1), "yellow" : Display.rgb_to_ansi(4, 4, 1), 
                 "pink" : Display.rgb_to_ansi(4, 1, 4), "cyan" : Display.rgb_to_ansi(1, 4, 4),
                 "purple" : Display.rgb_to_ansi(3, 1, 5), "clear" : "",
                 "black" : Display.rgb_to_ansi(0, 0, 0),
                 "greyback" : Display.flipansi(Display.rgb_to_ansi(3, 3, 3)),
                 "blueback" : Display.flipansi(Display.rgb_to_ansi(1, 1, 3))}
