import io
import re
import tempfile
import subprocess
import xml.dom.minidom as Xml

from os.path import join
from sys import platform

class SwfReader:
	SWFDUMP_NAME	= "swfdump"
	
	ABC_TAG_NAME	= "DoABC2"

	def __init__(self, sFlexSdkPath=""):
		self.sFlexSdkDir	= sFlexSdkPath

		# swf dump for library swf
		self.cLibraryXml	= 0
		
		# list of abc defs
		self.aAbcs			= []

		# definition paths lists
		self.aDefs			= []

		# imports paths list
		self.aImports		= []

		# shortened variable types list
		self.aTypes			= []

	# basic dump of swf
	def readSwf(self, sSwfPath):
		self.cLibraryXml	= Xml.parseString(
			self.runTool(self.SWFDUMP_NAME, [sSwfPath])
		)

	# function for reading ActionScript Bytecode (abc) from an swf
	def readSwfAbc(self, sSwfPath):
		cLibraryDump		= io.StringIO(
			self.runTool(self.SWFDUMP_NAME, ["-abc", sSwfPath])
		)

		# extract contents of abc by text parsing, since the xml is not always valid -_-
		sNextLine			= cLibraryDump.readline()

		while sNextLine != "":
			if self.ABC_TAG_NAME in sNextLine:
				sAbc		= ""
				sNextLine	= cLibraryDump.readline()
				
				while ("/" + self.ABC_TAG_NAME) not in sNextLine:
					sAbc		+= sNextLine
					sNextLine	= cLibraryDump.readline()
					
				self.aAbcs.append(sAbc)

			sNextLine		= cLibraryDump.readline()

	# call this to parse read swf data and populate info vars
	def parseData(self):
		self.parseImports()

		self.createImportsList()
		self.createTypesList()

	def parseImports(self):
		aNames			= []

		for cAbc in self.cLibraryXml.getElementsByTagName(self.ABC_TAG_NAME):
			aNames.append(cAbc.getAttribute("name"))

		self.aDefs		= [s.replace("/", ".") for s in aNames]

	def createImportsList(self):
		self.aImports	= [("import " + s + ";") for s in self.aDefs if "." in s]

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

	# takes the name of a flex sdk bin tool along with a list of arguments
	# runs the tool, passing the listed arguments
	# returns the output
	def runTool(self, sToolName, aToolArgs = []):
		aArgs	= [self.getToolPath(sToolName)] + aToolArgs

		return subprocess.check_output(aArgs, universal_newlines=True)

	# takes the name of a tool
	# will append ".exe" for windows systems, and prepend the path to the flex sdk bin folder if the sdk path has been set
	# returns the modified path
	def getToolPath(self, sToolName):
		sPath		= sToolName[:]

		if "win32" in platform:
			sPath	+= ".exe"

		if self.sFlexSdkDir != "":
			sPath	= join(self.sFlexSdkDir, "bin", sPath)

		return sPath