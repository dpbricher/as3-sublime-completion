import re
import zipfile
import xml.dom.minidom as Xml
#
# Class for reading and parsing swc files; Right now only reads the catalog.xml
#
class SwcReader:
	def __init__(self):
		# catalog xml
		self.cCatalogXml	= 0

		# definition paths lists
		self.aDefs			= ["test"]

		# imports paths list
		self.aImports		= []

		# shortened variable types list
		self.aTypes			= []

	def readSwc(self, sSwcPath):
		cFile				= zipfile.ZipFile(sSwcPath, "r")
		sCatalog			= cFile.read("catalog.xml")
		cFile.close()

		# xml parsing to find class definitions
		self.cCatalogXml	= Xml.parseString(sCatalog)

		self.parseImports()

		self.createImportsList()
		self.createTypesList()

	def parseImports(self):
		cNativeList		= self.cCatalogXml.getElementsByTagName("component")
		cImportList		= self.cCatalogXml.getElementsByTagName("script")

		aImports		= []
		aNatives		= []

		for cElement in cImportList:
			aImports.append(cElement.getAttribute("name"))

		for cElement in cNativeList:
			aNatives.append(cElement.getAttribute("name"))

		aImports		= [s.replace("/", ".") for s in aImports]

		aJoined			= [x for x in aImports if x not in aNatives]
		aJoined			+= aNatives

		self.aDefs		= aJoined

	def createImportsList(self):
		self.aImports	= []

		for sPath in self.aDefs:
			self.aImports.append("import " + sPath + ";")

	def createTypesList(self):
		for sPath in self.aDefs:
			self.aTypes.append({
				"trigger" : sPath,
				"contents" : re.sub(r".*\.", "", sPath)
			})

	def getImports(self):
		return self.aImports
	
	def getTypes(self):
		return self.aTypes