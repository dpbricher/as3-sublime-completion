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
cPlist		= open(sPlistPath, "wb")
plistlib.dump(cJson, cPlist)
cPlist.close()