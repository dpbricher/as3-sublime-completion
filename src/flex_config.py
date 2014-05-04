import xml.dom.minidom as Xml

class FlexConfigParser:
	def __init__(self):
		self.cConfigXml		= None

		self.aSourceDirs	= None
		self.aSourceSwcs	= None

		self.sFlashVersion	= None

	def readConfig(self, sConfigPath):
		self.cConfigXml	= Xml.parse(sConfigPath)

	def parseData(self):
		# (re)initialise vars
		self.aSourceDirs	= []
		self.aSourceSwcs	= []

		self.sFlashVersion	= ""

		# get flash version
		cVersionNodes   = self.cConfigXml.getElementsByTagName("target-player")
		
		if cVersionNodes != None:
		    self.sFlashVersion	= cVersionNodes[0].firstChild.data
		    
		# find additional src paths
		cSourcePaths    = self.cConfigXml.getElementsByTagName("source-path")

		if cSourcePaths != None:
		    cSourcePaths    = cSourcePaths[0].getElementsByTagName("path-element")

		    for cPath in cSourcePaths:
		        self.aSourceDirs.append(cPath.firstChild.data)

		# need to check the different ways of inluding sources and amnd this as appropriate
		cSourceSwcs		= self.cConfigXml.getElementsByTagName("include-libraries")

		if cSourceSwcs != None:
			cSourceSwcs		= cSourceSwcs[0].getElementsByTagName("library")

			for cLibrary in cSourceSwcs:
				self.aSourceSwcs.append(cLibrary.firstChild.data)

	def getFlashVersion(self):
		return self.sFlashVersion

	def getSourceDirs(self):
		return self.aSourceDirs

	def getSourceSwcs(self):
		return self.aSourceSwcs

	# TODO: implement this :o
	def getAppendSourceFlag(self):
		True
