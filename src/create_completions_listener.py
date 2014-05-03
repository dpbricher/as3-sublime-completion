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

SETTING_FILE_NAME		= "ActionScript 3-0.sublime-settings"
FLEX_SDK_PATH_KEY		= "flex_sdk_path"

def readCompList():
	try:
		aSettings		= sublime.load_settings(SETTING_FILE_NAME)
		sFlexSdkPath	= aSettings.get(FLEX_SDK_PATH_KEY)
	except (e):
		return

	aSourceSwcs		= [
		os.path.realpath(
			os.path.join(
				sFlexSdkPath, "frameworks/libs/player/11.1/playerglobal.swc"
			)
		)
	]

	for sPath in aSourceSwcs:
		cReader		= SwcReader(sFlexSdkPath)
		cReader.readSwc(sPath)
		cReader.parseData()
		
	createImportComps(cReader.getImports())
	createTypeComps(cReader.getTypes())

def createComps():
	readCompList()

def createImportComps(aCompletions):
	sImportsCompPath	= os.path.join(
		sublime.packages_path(),
		"ActionScript 3-0",
		"as3-imports.sublime-completions"
	)

	# open completions file
	cCompFile	= open(sImportsCompPath, "r")

	# read contents
	sCompDict	= json.load(cCompFile)
	cCompFile.close()

	# replace completions list
	sCompDict["completions"]	= aCompletions

	# write contents
	cCompFile	= open(sImportsCompPath, "w")
	json.dump(sCompDict, cCompFile, indent=4)

def createTypeComps(aCompletions):
	sTypesCompPath	= os.path.join(
		sublime.packages_path(),
		"ActionScript 3-0",
		"as3-types.sublime-completions"
	)

	# open completions file
	cCompFile	= open(sTypesCompPath, "r")

	# read contents
	sCompDict	= json.load(cCompFile)
	cCompFile.close()

	# replace completions list
	sCompDict["completions"]	= aCompletions

	# write contents
	cCompFile	= open(sTypesCompPath, "w")
	json.dump(sCompDict, cCompFile, indent=4)

class CreateCompletionsListener(sublime_plugin.EventListener):
	def on_load_async(self, view):
		createComps()

	# def on_post_save_async(self, view):
	# 	createComps()

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

class SwcReader(SwfReader):
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