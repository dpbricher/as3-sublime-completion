import swf
import os.path
import zipfile
import tempfile
import xml.dom.minidom as Xml
#
# Class for reading and parsing swc files
#
class SwcReader(swf.SwfReader):
	CATALOG_NAME	= "catalog.xml"
	LIBRARY_NAME	= "library.swf"

	def __init__(self, sFlexSdkPath=""):
		super().__init__(sFlexSdkPath)

		# catalog xml
		self.cCatalogXml	= 0

	def readSwc(self, sSwcPath):
		cFile				= zipfile.ZipFile(sSwcPath, "r")
		# read catalog file
		sCatalog			= cFile.read(self.CATALOG_NAME)
		# extract library
		cTempDir			= tempfile.TemporaryDirectory()
		cFile.extract(self.LIBRARY_NAME, path=cTempDir.name)
		# read library
		self.readSwf(os.path.join(cTempDir.name, self.LIBRARY_NAME))

		cTempDir.cleanup()
		cTempDir			= None

		cFile.close()

		self.cCatalogXml	= Xml.parseString(sCatalog)

	def parseData(self):
		super().parseData()