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
BUILD_CONFIG_PATH_KEY   = "build_config_path"

FLEX_GLOBAL_SWC_DIR     = "frameworks/libs/player"

gaImports   = None
gaTypes     = None

gsBuildXml  = None

def plugin_loaded():
    cPluginSettings = sublime.load_settings(SETTING_FILE_NAME)

    global gsBuildXml
    gsBuildXml      = join(
        os.path.dirname(sublime.active_window().project_file_name()),
        cPluginSettings.get(BUILD_CONFIG_PATH_KEY)
    )

    loadCompletions()

def loadCompletions():
    try:
        cSettings       = sublime.load_settings(SETTING_FILE_NAME)
        sFlexSdkPath    = cSettings.get(FLEX_SDK_PATH_KEY)
    except (e):
        return

    aSourceDirs         = []
    aSourceSwcs         = []

    sFlashVersion       = ""

    if gsBuildXml:
        cConfigReader   = FlexConfigParser()
        cConfigReader.readConfig(gsBuildXml)
        cConfigReader.parseData()

        sFlashVersion   = cConfigReader.getFlashVersion()

    if sFlashVersion != "":
        # set global swc to latest available
        aAllVersions    = os.listdir(
            os.path.join(sFlexSdkPath, FLEX_GLOBAL_SWC_DIR)
        )
        aAllVersions.sort()

        sFlashVersion   = aAllVersions.pop()

    if cConfigReader != None:
        aSourceDirs     = cConfigReader.getSourceDirs()
        aSourceSwcs     = cConfigReader.getSourceSwcs()
    
    # add global swc source path so long as config does not have source-path append="false"
    if cConfigReader == None or cConfigReader.getAppendSourceFlag():        
        sGlobalSwcPath      = os.path.realpath(
            os.path.join(sFlexSdkPath, FLEX_GLOBAL_SWC_DIR, sFlashVersion, "playerglobal.swc")
        )

        if sGlobalSwcPath not in aSourceSwcs:
            aSourceSwcs.append(sGlobalSwcPath)

    global gaImports, gaTypes

    gaImports       = []
    gaTypes         = []

    cSwcReader      = SwcReader(sFlexSdkPath)
    cDirReader      = SourceDirAs3Reader()
    
    cFormatter      = CompletionFormatter()

    for sPath in aSourceSwcs:
        cSwcReader.readSwc(sPath)
        cSwcReader.parseData()

        gaImports   += cFormatter.createImportList(cSwcReader.getFqClassNames())
        gaTypes     += cFormatter.createTypeList(cSwcReader.getFqClassNames())
    
    for sPath in aSourceDirs:
        cDirReader.readDir(sPath)
        cDirReader.parseData()

        gaImports   += cFormatter.createImportList(cDirReader.getFqClassNames())
        gaTypes     += cFormatter.createTypeList(cDirReader.getFqClassNames())

class CompletionsListenerAs3(sublime_plugin.EventListener):
    SCOPE_IMPORT            = "source.actionscript.3 meta.package.actionscript.3 - meta.class.actionscript.3"
    SCOPE_TYPE              = "source.actionscript.3 meta.class.actionscript.3 meta.storage.type.actionscript.3"

    def on_query_completions(self, view, prefix, locations):
        aAutoList   = None

        if len(locations) == 1:
            iCurrentPoint   = locations[0];

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

class FlexConfigParser:
    def __init__(self):
        self.cConfigXml     = None

        self.aSourceDirs    = None
        self.aSourceSwcs    = None

        self.sFlashVersion  = None

    def readConfig(self, sConfigPath):
        self.cConfigXml = Xml.parse(sConfigPath)

    def parseData(self):
        # (re)initialise vars
        self.aSourceDirs    = []
        self.aSourceSwcs    = []

        self.sFlashVersion  = ""

        # get flash version
        cVersionNodes   = self.cConfigXml.getElementsByTagName("target-player")
        
        if cVersionNodes != None:
            self.sFlashVersion  = cVersionNodes[0].firstChild.data
            
        # find additional src paths
        cSourcePaths    = self.cConfigXml.getElementsByTagName("source-path")

        if cSourcePaths != None:
            cSourcePaths    = cSourcePaths[0].getElementsByTagName("path-element")

            for cPath in cSourcePaths:
                self.aSourceDirs.append(cPath.firstChild.data)

        # need to check the different ways of inluding sources and amnd this as appropriate
        cSourceSwcs     = self.cConfigXml.getElementsByTagName("include-libraries")

        if cSourceSwcs != None:
            cSourceSwcs     = cSourceSwcs[0].getElementsByTagName("library")

            for cLibrary in cSourceSwcs:
                self.aSourceSwcs.append(cLibrary.firstChild.data)

    def getFlashVersion(self):
        return self.sFlashVersion

    def getSourceDirs(self):
        return self.aSourceDirs

    def getSourceSwcs(self):
        return self.aSourceSwcs

    def getAppendSourceFlag(self):
        True

class SourceDirAs3Reader():
    AS_EXT          = os.extsep + "as"
    AS_EXT_LEN      = len(AS_EXT)

    def __init__(self):
        self.sSourceDir     = None
        self.aSourceFiles   = None
        self.aSourceSwcs    = None

        self.aFqClassNames  = None

    def readDir(self, sDirPath):
        aPaths  = []

        self.sSourceDir     = sDirPath

        self.aSourceFiles   = []
        self.aSourceSwcs    = []

        for cInfo in os.walk(self.sSourceDir, True, None, True):
            for sFile in cInfo[2]:
                if sFile.endswith(self.AS_EXT):
                    self.aSourceFiles.append( os.path.join(cInfo[0], sFile) )

    def parseData(self):
        self.aFqClassNames  = []

        for sPath in self.aSourceFiles:
            sPath   = os.path.relpath(sPath, self.sSourceDir)
            sPath   = sPath[:-self.AS_EXT_LEN]
            sPath   = sPath.replace(os.sep, ".")

            self.aFqClassNames.append(sPath)

    def getFqClassNames(self):
        return self.aFqClassNames

class CompletionFormatter:
    def __init__(self):
        pass

    def createImportList(self, aFqClassNames):
        aImports    = [
            ("import " + s.replace("/", ".") + ";",) for s in aFqClassNames
        ]

        return aImports

    def createTypeList(self, aFqClassNames):
        aTypes  = [
            ( s, re.sub(r".*\.", "", s) ) for s in aFqClassNames
        ]

        return aTypes