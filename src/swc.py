import os.path
import zipfile
import xml.dom.minidom as Xml
import importlib

PACKAGE_NAME    = os.path.splitext( os.path.basename( os.path.dirname( os.path.realpath(__file__) ) ) )[0]

swf             = importlib.import_module(PACKAGE_NAME + ".swf")
#
# Class for reading and parsing swc files
#
class SwcReader(swf.SwfReader):
    CATALOG_NAME    = "catalog.xml"
    LIBRARY_NAME    = "library.swf"

    def __init__(self, sFlexSdkPath=""):
        super().__init__(sFlexSdkPath)

        # catalog xml
        self.cCatalogXml    = None

        # set this to true if we hit an error whilst parsing the swc dump
        self.bReadError     = False

    def readSwc(self, sSwcPath):
        # read catalog file
        cFile               = zipfile.ZipFile(sSwcPath, "r")
        sCatalog            = cFile.read(self.CATALOG_NAME)
        cFile.close()

        try:
            self.cCatalogXml    = Xml.parseString(sCatalog)
        except:
            self.bReadError     = True

    def parseData(self):
        aClassDefs          = []
        
        if not self.bReadError:
            cImportList     = self.cCatalogXml.getElementsByTagName("script")

            for cScriptNode in cImportList:
                cDefList    = cScriptNode.getElementsByTagName("def")
                
                for cDefNode in cDefList:
                    aClassDefs.append(cDefNode.getAttribute("id"))
            
        self.aFqClassNames  = [s.replace(":", ".") for s in aClassDefs]