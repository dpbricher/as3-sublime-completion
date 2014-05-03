import os
import json

import zipfile
import tempfile
import xml.dom.minidom as Xml
from os.path import join
from sys import platform

import io
import re
import subprocess

import sublime, sublime_plugin

SETTING_FILE_NAME       = "ActionScript 3-0.sublime-settings"
FLEX_SDK_PATH_KEY       = "flex_sdk_path"
FLEX_GLOBAL_SWC_DIR     = "frameworks/libs/player"

gaImports   = []
gaTypes     = []

def plugin_loaded():
    try:
        aSettings       = sublime.load_settings(SETTING_FILE_NAME)
        sFlexSdkPath    = aSettings.get(FLEX_SDK_PATH_KEY)
    except (e):
        return

    aSourceSwcs     = [
        os.path.realpath(
            os.path.join(sFlexSdkPath, FLEX_GLOBAL_SWC_DIR, "11.1/playerglobal.swc")
        )
    ]

    global gaImports, gaTypes

    for sPath in aSourceSwcs:
        cReader     = SwcReader(sFlexSdkPath)
        cReader.readSwc(sPath)
        cReader.parseData()

        gaImports   = [(s,) for s in cReader.getImports() if s not in gaImports]
        gaTypes     = cReader.getTypes()

class CompletionsListenerAs3(sublime_plugin.EventListener):
    SCOPE_IMPORT            = "source.actionscript.3 meta.package.actionscript.3 - meta.class.actionscript.3"
    SCOPE_TYPE              = "source.actionscript.3 meta.class.actionscript.3 meta.storage.type.actionscript.3"

    def on_query_completions(self, view, prefix, locations):
        aAutoList   = None

        if len(locations) == 1:
            iCurrentPoint   = locations[0];
            sCurrentScope   = view.scope_name(iCurrentPoint)

            if view.score_selector(iCurrentPoint, self.SCOPE_IMPORT) > 0:
                global gaImports
                aAutoList   = gaImports

            # this is the scope that we want to target:
            #   meta.package.actionscript.3 meta.class.actionscript.3 meta.storage.type.actionscript.3
            # but for some reason the last one isn't showing up in the current scope string...
            else:
                aMatches        = view.find_by_selector(self.SCOPE_TYPE)

                for cRegion in aMatches:
                    if cRegion.contains(iCurrentPoint):
                        global gaTypes
                        aAutoList   = gaTypes
                        break

        return aAutoList

class SwfReader:
    SWFDUMP_NAME    = "swfdump"
    
    ABC_TAG_NAME    = "DoABC2"

    def __init__(self, sFlexSdkPath=""):
        self.sFlexSdkDir    = sFlexSdkPath

        # swf dump for library swf
        self.cLibraryXml    = 0
        
        # list of abc defs
        self.aAbcs          = []

        # definition paths lists
        self.aDefs          = []

        # imports paths list
        self.aImports       = []

        # shortened variable types list
        self.aTypes         = []

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
        self.parseImports()

        self.createImportsList()
        self.createTypesList()

    def parseImports(self):
        aNames          = []

        for cAbc in self.cLibraryXml.getElementsByTagName(self.ABC_TAG_NAME):
            aNames.append(cAbc.getAttribute("name"))

        self.aDefs      = [s.replace("/", ".") for s in aNames]

    def createImportsList(self):
        self.aImports   = [("import " + s + ";") for s in self.aDefs if "." in s]

    def createTypesList(self):
        for sPath in self.aDefs:
            self.aTypes.append(
                (sPath, re.sub(r".*\.", "", sPath))
            )

    def getImports(self):
        return self.aImports
    
    def getTypes(self):
        return self.aTypes

    # takes the name of a flex sdk bin tool along with a list of arguments
    # runs the tool, passing the listed arguments
    # returns the output
    def runTool(self, sToolName, aToolArgs = []):
        aArgs   = [self.getToolPath(sToolName)] + aToolArgs

        return subprocess.check_output(aArgs, universal_newlines=True)

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

class SwcReader(SwfReader):
    CATALOG_NAME    = "catalog.xml"
    LIBRARY_NAME    = "library.swf"

    def __init__(self, sFlexSdkPath=""):
        super().__init__(sFlexSdkPath)

        # catalog xml
        self.cCatalogXml    = 0

    def readSwc(self, sSwcPath):
        cFile               = zipfile.ZipFile(sSwcPath, "r")
        # read catalog file
        sCatalog            = cFile.read(self.CATALOG_NAME)
        # extract library
        cTempDir            = tempfile.TemporaryDirectory()
        cFile.extract(self.LIBRARY_NAME, path=cTempDir.name)
        # read library
        self.readSwf(os.path.join(cTempDir.name, self.LIBRARY_NAME))

        cTempDir.cleanup()
        cTempDir            = None

        cFile.close()

        self.cCatalogXml    = Xml.parseString(sCatalog)

    def parseData(self):
        super().parseData()