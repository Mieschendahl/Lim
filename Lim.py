import sys, datetime, threading, time, shutil, hashlib
from Key import Key
from File import File
from Control import Control
from Display import Display
from LoadSave import LoadSave

class Lim:
    def __init__(self, path):
        self.cuteloading = None
        self.asynckey = None
        try:
            self.key = Key()
            self.asynckey = threading.Thread(target=self.key.storechar, args=(), daemon=False)
            self.asynckey.start()
            self.time = time.time()

            width, height = shutil.get_terminal_size((80, 20))
            sys.stdout.write(Display.showscreen())
            sys.stdout.flush()

            self.cuteloading = threading.Thread(target=Display.startloading, args=(width,), daemon=False)
            self.cuteloading.start()
            Display.setdisplay(width - 1, height)
            self.skipupdate = False
            self.restart = False

            self.path = path
            self.now = datetime.datetime.now()
            self.control = Control(self)

            self.filedisplay = Display(Display.width, Display.height - 1, 0, 0, False, False)
            self.infodisplay = Display(Display.width, Display.height, 0, 0, True, True)
            self.cmddisplay = Display(Display.width, Display.height, 0, 0, False, True)
            self.currentdisplay = self.filedisplay
            self.currentfile = self.filedisplay
            self.loadfile()
            
            Display.stoploading(self.cuteloading)
            self.update()

            self.key.settrackkeys(True)
            self.loop()

        finally:
            Display.stoploading(self.cuteloading)
            Key.close()
            self.asynckey.join()
            if not self.restart:
                sys.stdout.write(Display.hidescreen())
                sys.stdout.flush()

    def loadfile(self):
        self.file = LoadSave.loadfile(self.path)
        self.infofile = LoadSave.loadfile()
        self.cmdfile = LoadSave.loadfile()

        self.infofile.smartsetstring(self.now.strftime("%H:%M:%S %d/%m/%Y"), Display.color["blue"])
        self.cmdfile.smartsetstring(" ".join(self.file.flags + [""]))
        self.cmdfile.smartsetstring(self.path, Display.color["green"])
        self.cmdfile.smartsetstring(" %dTC %dL" % (self.file.lenchars(), self.file.len()))

    def loop(self):
        while True:
            new_time = time.time()
            time.sleep(max(0, 0.01 - new_time + self.time))
            self.time = new_time

            char = self.key.asyncgetchar()

            if not char:
                continue

            if not self.control.handlechar(char):
                break

            msg = repr(char) + " %d/%dC %d/%dL"
            smartx, smarty = self.file.smartgetposition()
            msg %= smartx, self.file.lencolumn(), smarty, self.file.len()
            self.infofile.cleardata()
            self.infofile.smartsetstring(msg, Display.color["blue"])

            self.update()
            self.skipupdate = False

            # 0. Make loading bigscreen in the background
            # 2. Give me ignorierung von /"
            # 4. Für Quotes reicht es theoretisch, wenn man die öffnenden und schließenden positionen speichert,
            # welche ja geordnet werden können und dann guckt ob ein neues insert/delete eine neue öffnende/schließende
            # kreiert bzw die position der anderen quotes ändert.
            # Im Display kann dann geschaut werden, welche chars innerhalb von quotes sind... (wobei es reicht, einmal
            # die vorherige quote zu checken und dann liniar durchzugehen mit dem displaen des buffers.

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
