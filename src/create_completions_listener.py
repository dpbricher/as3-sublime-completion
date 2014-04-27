import os
import re
import json
import zipfile
import xml.dom.minidom as Xml

import sublime, sublime_plugin

def read_comp_list():
	aSourceSwcs		= [
		"C:/Users/Dean/Downloads/flex_sdk_4.6/frameworks/libs/player/11.1/playerglobal.swc"
	]

	aRaw			= []
	aCompletions	= []

	for sPath in aSourceSwcs:
		aRaw		+= getImportsFromSwc(sPath)

	for sPath in aRaw:
		aCompletions.append(
			sPath.replace("/", ".")
		)
	
	return aCompletions

def create_comps():
	createImportComps()
	createTypeComps()

def createImportComps():
	aCompletions	= []
	aRaw			= read_comp_list()

	# format completions list
	for sPath in aRaw:
		if "." in sPath:
			aCompletions.append("import " + sPath + ";")

	sImportsCompPath	= os.path.join(
		sublime.packages_path(),
		"ActionScript 3",
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

def createTypeComps():
	aCompletions	= []
	aRaw			= read_comp_list()

	# format completions
	for sPath in aRaw:
		aCompletions.append(
			{
				"trigger" : sPath,
				"contents" : re.sub(r".*\.", "", sPath)
			}
		)

	sTypesCompPath	= os.path.join(
		sublime.packages_path(),
		"ActionScript 3",
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

def getImportsFromSwc(sSwcPath):
	cFile		= zipfile.ZipFile(sSwcPath, "r")
	sCatalog	= cFile.read("catalog.xml")
	cFile.close()

	# xml parsing to find class definitions
	cXml		= Xml.parseString(sCatalog)

	# get others
	aImports	= getNamesFromElementList(
		cXml.getElementsByTagName("script")
	)

	return aImports

def getNamesFromElementList(cElementList):
	aNames	= []

	for cElement in cElementList:
		# This might actually properly be "className" for components, not sure
		aNames.append(cElement.getAttribute("name"))

	return aNames	

class CreateCompletionsListener(sublime_plugin.EventListener):
	def on_load_async(self, view):
		print("on_load_async")
		create_comps()

	# def on_post_save_async(self, view):
	# 	print("on_post_save_async")
	# 	create_comps()