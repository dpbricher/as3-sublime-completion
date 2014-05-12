import io
import re
import subprocess
import xml.dom.minidom as Xml

from os.path import join
from sys import platform

class SwfReader:
    SWFDUMP_NAME    = "swfdump"

    ABC_TAG_NAME    = "DoABC2"

    def __init__(self, sFlexSdkPath=""):
        self.sFlexSdkDir    = sFlexSdkPath

        # swf dump for library swf
        self.cLibraryXml    = 0

        # list of abc defs
        self.aAbcs          = []

        # fully qualified class names list, . separated
        self.aFqClassNames  = None

    # basic dump of swf
    def readSwf(self, sSwfPath):
        self.cLibraryXml    = Xml.parseString(
            self.runTool(self.SWFDUMP_NAME, [sSwfPath])
        )

    # function for reading ActionScript Bytecode (abc) from an swf
    def readSwfAbc(self, sSwfPath):
        cLibraryDump        = io.StringIO(
            self.runTool(self.SWFDUMP_NAME, ["-abc", sSwfPath])
        )

        # extract contents of abc by text parsing, since the xml is not always valid -_-
        sNextLine           = cLibraryDump.readline()

        while sNextLine != "":
            if self.ABC_TAG_NAME in sNextLine:
                sAbc        = ""
                sNextLine   = cLibraryDump.readline()

                while ("/" + self.ABC_TAG_NAME) not in sNextLine:
                    sAbc        += sNextLine
                    sNextLine   = cLibraryDump.readline()

                self.aAbcs.append(sAbc)

            sNextLine       = cLibraryDump.readline()

    # call this to parse read swf data and populate info vars
    def parseData(self):
        aNames              = []

        for cAbc in self.cLibraryXml.getElementsByTagName(self.ABC_TAG_NAME):
            aNames.append(cAbc.getAttribute("name"))

        self.aFqClassNames  = [s.replace("/", ".") for s in aNames]

    def getFqClassNames(self):
        return self.aFqClassNames

    # takes the name of a flex sdk bin tool along with a list of arguments
    # runs the tool, passing the listed arguments
    # returns the output
    def runTool(self, sToolName, aToolArgs = []):
        aArgs                   = [self.getToolPath(sToolName)] + aToolArgs

        # prevent a new terminal window from opening on windows machines
        if "win32" in platform:
            startupInfo             = subprocess.STARTUPINFO()
            startupInfo.dwFlags     |= subprocess.STARTF_USESHOWWINDOW
            sOutput                 = subprocess.check_output(aArgs, universal_newlines=True, startupinfo=startupInfo)
        else:
            sOutput                 = subprocess.check_output(aArgs, universal_newlines=True)

        return sOutput

    # takes the name of a tool
    # will append ".exe" for windows systems, and prepend the path to the flex sdk bin folder if the sdk path has been set
    # returns the modified path
    def getToolPath(self, sToolName):
        sPath       = sToolName[:]

        if "win32" in platform:
            sPath   += ".exe"

        if self.sFlexSdkDir != "":
            sPath   = join(self.sFlexSdkDir, "bin", sPath)

        return sPath