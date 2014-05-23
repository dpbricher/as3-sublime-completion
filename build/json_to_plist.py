#!/usr/bin/python

import collections
import json
import os
import plistlib
import sys

# read json file path
sJsonPath	= sys.argv[1]

# parse json
cJsonHandle	= open(sJsonPath, "r")
cJson		= json.load(cJsonHandle, object_pairs_hook=collections.OrderedDict)
cJsonHandle.close()

# determine plist file name
sPlistPath	= os.path.splitext(sJsonPath)[0]

# dump json as plist to plist file

# making an allowance for python version 2.x here...
iPyVersion	= sys.version_info[0]

if iPyVersion == 3:
	cPlist		= open(sPlistPath, "wb")
	plistlib.dump(cJson, cPlist)
	cPlist.close()
else:
	# try version 2
	plistlib.writePlist(cJson, sPlistPath)