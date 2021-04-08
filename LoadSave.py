import sys, os, errno, hashlib, re
from Log import Log
from File import File
from Highlight import Highlight

class LoadSave:
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
            return LoadSave.seperator0.join(string)
        return "".join(string)

    def decompressdata(string, data, axis, dynamicsize):
        rawdata = string.split(LoadSave.seperator0)
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

    def issaved(fl, path):
        charstring = LoadSave.compressdata(fl.data, File.char, False)
        newhexhash = hashlib.md5(charstring.encode("utf-8")).hexdigest()
        try:
            if not {"new file", "new meta"} & set(fl.flags):
                dirname, filename = os.path.split(path)
                with open(LoadSave.metadir + filename + ".meta", "r") as f:
                    string = f.read()

                charstring = LoadSave.compressdata(fl.data, File.char, False)
                metastring = LoadSave.compressdata(fl.data, File.usercolor, True)
                newhexhash = hashlib.md5((charstring + metastring).encode("utf-8")).hexdigest()
        except:
            pass
        return fl.hexhash == newhexhash

    def savefile(fl, path):
        if LoadSave.issaved(fl, path):
            return

        charstring = LoadSave.compressdata(fl.data, File.char, False)
        dirname, filename = os.path.split(path)
        LoadSave.createpath(dirname)
        with open(path, "w") as f:
           f.write(charstring)

        metastring = LoadSave.compressdata(fl.data, File.usercolor, True)
        version = "Version:\n" + str(LoadSave.version) + "\n"
        fl.hexhash = hashlib.md5((charstring + metastring).encode("utf-8")).hexdigest()
        hexhash = "Hash:\n" + fl.hexhash + "\n"
        metastring = "Metadata:\n" + metastring + "\n"
        string = LoadSave.seperator1.join([version, hexhash, metastring])

        metapath = LoadSave.metadir
        LoadSave.createpath(LoadSave.metadir)
        with open(LoadSave.metadir + filename + ".meta", "w") as f:
            f.write(string)

    def loadfile(path=""):
        dirname, filename = os.path.split(path)
        log = Log(lambda x: re.match("( |newline)", x[-1][File.char]))
        hl = Highlight.fromfile(os.path.splitext(path)[1][1 : ])
        fl = File(log, hl)

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
                with open(LoadSave.metadir + filename + ".meta", "r") as f:
                    string = f.read()

                version, hexhash, metastring = string.split(LoadSave.seperator1)
                version = version[len("Version:\n"): -1]
                hexhash = hexhash[len("Hash:\n"): -1]
                metastring = metastring[len("Metadata:\n"): -1]
                newhexhash = hashlib.md5((charstring + metastring).encode("utf-8")).hexdigest()

                if version != str(LoadSave.version):
                    raise Exception("Version missmatch, file '%s' with own '%s'." % (version, str(LoadSave.version)))

                if hexhash != newhexhash:
                    raise Exception("File was changed, hash does not match old.")

                data = fl.copydata()
                LoadSave.decompressdata(metastring, data, File.usercolor, True)

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

LoadSave.version = 1.0
LoadSave.seperator0 = "\x1b\t"
LoadSave.seperator1 = "\x1b\n"
LoadSave.metadir = ".meta/"
