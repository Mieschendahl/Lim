class Key:
    def __init__(self):
        self.chars = []
        self.csi = False
        Key.closed = False
        self.trackkeys = False
        # TODO: Make an Escape sequence checker for linux!

    def settrackkeys(self, trackkeys=None):
        if trackkeys is None:
            self.trackkeys = not self.trackkeys
        else:
            self.trackkeys = trackkeys

    def storechar(self):
        while not Key.closed:
            char = ""

            if Key.system == "Linux":
                fd = sys.stdin.fileno()
                old_settings = termios.tcgetattr(fd)
                try:
                    tty.setraw(fd)
                    char = sys.stdin.read(1)
                finally:
                    termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

                if not self.trackkeys:
                    continue

                if self.chars and self.chars[-1] == "\x1b" and char == "[":
                    self.csi = True
                    self.chars = self.chars[ : -1] + [self.chars[-1] + char]

                else:
                    if self.csi:
                        self.chars[-1] += char

                        if char.isalpha():
                            self.csi = False
                            self.chars[-1] = Key.convertlinuxchar.get(self.chars[-1], self.chars[-1])
                    else:
                        self.chars.append(char)
            else:
                char = msvcrt.getwch()

                if msvcrt.kbhit():
                    char = Key.convertwindowschar.get(msvcrt.getwch(), char)

                if not self.trackkeys:
                    continue

                self.chars.append(char)

        if Key.system == "Windows":
            while msvcrt.kbhit():
                msvcrt.getch()

    def asyncgetchar(self):
        if not self.chars or self.csi:
            return

        char, self.chars = self.chars[0], self.chars[1 : ]
        return Key.convertchar.get(char, char)

    def close():
        Key.closed = True
        sys.stdout.write("\x1b[6n")
        sys.stdout.flush()

Key.convertchar = {"\r" : "NEWLINE", "\x7f" : "BACKSPACE", "\x08" : "BACKSPACE", "\x1b[Z" : "TAB"}

try:
    import sys, tty, termios
    Key.system = "Linux"
    Key.convertlinuxchar = {"\x1b[A" : "UP", "\x1b[B" : "DOWN", "\x1b[D" : "LEFT", "\x1b[C" : "RIGHT",
                            "\x1b[1;2A" : "SUP", "\x1b[1;2B" : "SDOWN", "\x1b[1;2D" : "SLEFT", "\x1b[1;2C" : "SRIGHT",
                            "\x1b[1;5A" : "KUP", "\x1b[1;5B" : "KDOWN", "\x1b[1;5D" : "KLEFT", "\x1b[1;5C" : "KRIGHT"}
except:
    import msvcrt
    Key.system = "Windows"
    Key.convertwindowschar = {"H" : "UP", "P" : "DOWN", "K" : "LEFT", "M" : "RIGHT",
                              "\x8d" : "KUP", "\x91" : "KDOWN", "t" : "KLEFT", "s" : "KRIGHT"}
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
    except:
        pass
