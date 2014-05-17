import os.path
import xml.dom.minidom as Xml

#
# TODO:
# Check if config xml is allowed multiples of source-path, include-libraries, etc
#
class FlexConfigParser:
    def __init__(self):
        self.cConfigXml     = None

        self.aSourceDirs    = None
        self.aSourceSwcs    = None

        self.sFlashVersion  = None

        self.sConfigPath    = None
        self.sConfigDir     = None

        self.bAppendSrcPath = None

    def readConfig(self, sConfigPath):
        self.sConfigPath    = sConfigPath
        self.sConfigDir     = os.path.dirname(sConfigPath)

        self.cConfigXml     = Xml.parse(sConfigPath)

    def parseData(self):
        # (re)initialise vars
        self.aSourceDirs    = []
        self.aSourceSwcs    = []

        self.sFlashVersion  = ""

        self.bAppendSrcPath = False

        # get flash version
        cVersionNodes       = self.cConfigXml.getElementsByTagName("target-player")

        if cVersionNodes != None:
            self.sFlashVersion  = cVersionNodes[0].firstChild.data

        # find additional src paths
        cSourcePaths        = self.cConfigXml.getElementsByTagName("source-path")

        if cSourcePaths.length > 0:
            # only take note of the first source path element since I don't think it accepts multiple, but should check
            cSourcePaths    = cSourcePaths[0]

            # get append setting
            sAppend         = cSourcePaths.getAttribute("append")

            if sAppend == "true":
                self.bAppendSrcPath = True
            
            # extract all paths
            cPathsList      = cSourcePaths.getElementsByTagName("path-element")

            for cPathNode in cPathsList:
                self.aSourceDirs.append(cPathNode.firstChild.data)

        # find include libraries
        cSourceSwcs         = self.cConfigXml.getElementsByTagName("include-libraries")

        if cSourceSwcs.length > 0:
            cSourceSwcs     = cSourceSwcs[0]
            cLibraryList    = cSourceSwcs.getElementsByTagName("library")

            for cLibraryNode in cLibraryList:
                self.aSourceSwcs.append(cLibraryNode.firstChild.data)
        
        # find library paths and external libraries
        for sNodeType in ["library-path", "external-library-path"]:
            cSourceSwcs         = self.cConfigXml.getElementsByTagName(sNodeType)

            if cSourceSwcs.length > 0:
                cSourceSwcs     = cSourceSwcs[0]
                cLibraryList    = cSourceSwcs.getElementsByTagName("path-element")

                for cLibraryNode in cLibraryList:
                    self.aSourceSwcs.append(cLibraryNode.firstChild.data)

        aAbsPaths   = []
        aAbsSwcs    = []

        # make all source paths absolute
        for sPath in self.aSourceDirs:
            if not os.path.isabs(sPath):
                sPath   = os.path.join(self.sConfigDir, sPath)

            aAbsPaths.append(sPath)

        # make all source swcs absolute
        for sPath in self.aSourceSwcs:
            if not os.path.isabs(sPath):
                sPath   = os.path.join(self.sConfigDir, sPath)

            aAbsSwcs.append(sPath)

        self.aSourceDirs    = aAbsPaths
        self.aSourceSwcs    = aAbsSwcs

    def getFlashVersion(self):
        return self.sFlashVersion

    def getSourceDirs(self):
        return self.aSourceDirs

    def getSourceSwcs(self):
        return self.aSourceSwcs

    def getAppendSourceFlag(self):
        return self.bAppendSrcPath