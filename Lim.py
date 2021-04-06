import sys, datetime, threading, time, shutil, hashlib
from Display import Display
from Control import Control
from File import File
from Key import Key

class Lim:
    def __init__(self, path):
        self.path = path
        self.now = datetime.datetime.now()

        width, height = shutil.get_terminal_size((80, 20))
        Display.setdisplay(width - 1, height)
        self.skipupdate = False

        self.filedisplay = Display(Display.width, Display.height - 1, 0, 0, False, False)
        self.infodisplay = Display(Display.width, Display.height, 0, 0, True, True)
        self.cmddisplay = Display(Display.width, Display.height, 0, 0, False, True)
        self.currentdisplay = self.filedisplay
        self.currentfile = self.filedisplay
        self.current = "main"

        self.control = Control(self)

        self.loadfile()

    def loadfile(self):
        self.file = File.loadfile(self.path, False)
        self.infofile = File()
        self.cmdfile = File()

        self.infofile.smartsetstring(self.now.strftime("%H:%M:%S %d/%m/%Y"), Display.color["blue"])
        self.cmdfile.smartsetstring(" ".join(self.file.flags + [""]))
        self.cmdfile.smartsetstring(self.path, Display.color["green"])
        self.cmdfile.smartsetstring(" %dTC %dL" % (self.file.lenchars(), self.file.len()))

        sys.stdout.write(Display.showscreen())
        self.update()

    def main(self):
        try:
            self.key = Key()
            self.asynckey = threading.Thread(target=self.key.storechar, args=(), daemon=False)
            self.asynckey.start()
            self.time = time.time()

            while True:
                new_time = time.time()
                time.sleep(max(0, 0.01 - new_time + self.time))
                self.time = new_time

                char = self.key.asyncgetchar()

                if char:
                    if not self.control.handlechar(char):
                        break

                    msg = repr(char) + " %d/%dC %d/%dL"
                    smartx, smarty = self.file.smartgetposition()
                    msg %= smartx, self.file.lencolumn(), smarty, self.file.len()
                    self.infofile.cleardata()
                    self.infofile.smartsetstring(msg, Display.color["blue"])

                elif not self.file.isactive():
                    continue

                self.update()
                self.skipupdate = False
        finally:
            Key.close()
            self.asynckey.join()
            sys.stdout.write(Display.hidescreen())
            sys.stdout.flush()

    def update(self):
        if self.skipupdate:
            return

        Display.filldisplay()

        self.filedisplay.applyfile(self.file)
        self.infodisplay.applyfile(self.infofile)
        self.cmddisplay.applyfile(self.cmdfile)
        # Display.applycross(*self.filedisplay.getcursor())

        display = Display.hidecursor()
        display += Display.outputdisplay()
        display += self.currentdisplay.outputcursor()
        display += Display.showcursor()
        sys.stdout.write(display)
        sys.stdout.flush()

# Mach eine Uhr im Hintergrund über Hintergrundfarben (oder irgendeine art von hintergrunddisplay... nice)
# TODO 3: Runtime verbessern...
