#!/usr/bin/python

import json
import sys
import os
import collections
import xml.etree.ElementTree as ET

def run():
	# read json file path
	sJsonPath	= sys.argv[1]

	# parse json
	cJsonHandle	= open(sJsonPath, "r")
	cJson		= json.load(cJsonHandle, object_pairs_hook=collections.OrderedDict)
	cJsonHandle.close()

	# convert to xml
	cXml		= convertToPlist(cJson)

	# determine plist file name
	sPlistPath	= os.path.splitext(sJsonPath)[0]

	# write xml to plist file
	cPlist		= open(sPlistPath, "w")
	cPlist.write(
		ET.tostring(cXml, encoding="unicode")
	)
	cPlist.close()

def convertToPlist(cDict):
	cXml	= ET.Element("plist")
	cXml.append(
		createXmlFragment(cDict)
	)

	return cXml

def createXmlFragment(cDict):
	cParent	= ET.Element("dict")

	for k, v in cDict.items():
		cChildA			= ET.Element("key")
		cChildA.text	= k

		cChildB			= createValueNode(v)

		cParent.append(cChildA)
		cParent.append(cChildB)

	return cParent

def createValueNode(value):
	valueType		= type(value)

	if valueType is str:
		cNode		= ET.Element("string")
		cNode.text	= value
	elif valueType is int:
		cNode		= ET.Element("number")
		cNode.text	= value
	elif valueType is list:
		cNode		= ET.Element("array")
		for i in value:
			cNode.append(
				createValueNode(i)
			)
	elif valueType is dict or valueType is collections.OrderedDict:
		cNode		= createXmlFragment(value)
	else:
		print("unknown element type found! : " + str(valueType))
		cNode		= ET.Element("string")

	return cNode

run()