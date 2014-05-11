import os.path
import zipfile
import tempfile
import xml.dom.minidom as Xml
import importlib

PACKAGE_NAME    = os.path.splitext( os.path.basename( os.path.dirname( os.path.realpath(__file__) ) ) )[0]

swf             = importlib.import_module(PACKAGE_NAME + ".swf")
fp9_fqcn        = importlib.import_module(PACKAGE_NAME + ".fp9-fqcn")
#
# Class for reading and parsing swc files
#
class SwcReader(swf.SwfReader):
    CATALOG_NAME    = "catalog.xml"
    LIBRARY_NAME    = "library.swf"

    def __init__(self, sFlexSdkPath=""):
        super().__init__(sFlexSdkPath)

        # catalog xml
        self.cCatalogXml    = 0

        # set this to true if we hit an error whilst parsing the swc dump
        self.bReadError     = False

    def readSwc(self, sSwcPath):
        # read catalog file
        cFile               = zipfile.ZipFile(sSwcPath, "r")
        sCatalog            = cFile.read(self.CATALOG_NAME)
        cFile.close()

        self.cCatalogXml    = Xml.parseString(sCatalog)

        # read library
        try:
            self.readSwf(sSwcPath)
        except:
            # fp9 playerglobal.swc has a syntax error in its meta data -_-
            # So, for now just going to assume that if its a playerglobal.swc giving this error then its fp9
            # Lazy I know
            self.bReadError = True

    def parseData(self):
        if not self.bReadError:
            super().parseData()
        else:
            self.parseBackupData()

    def parseBackupData(self):
        self.aFqClassNames  = fp9_fqcn.LIST[:]