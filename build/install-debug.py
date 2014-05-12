#!/usr/bin/python

import os, os.path
import shutil
import subprocess
import sys

sPackagePath			= "../src"
sSublimePackagesDir		= {
	"darwin"	: "~/Library/Application Support/Sublime Text 3/Packages",
	"win32" 	: "~/AppData/Roaming/Sublime Text 3/Packages"
	# "linux" 	: ""
}.get(sys.platform)

if sSublimePackagesDir is None:
	sSublimePackagesDir	= ""

sSublimePackagesDir		= os.path.expanduser(sSublimePackagesDir)

if not os.path.exists(sSublimePackagesDir):
	print("Cannot find Sublime Text packages directory")
	exit()

sCopyDestDir		= os.path.join(sSublimePackagesDir, "ActionScript 3-0")

# convert language json to plist
subprocess.call(["python", "json_to_plist.py", os.path.join(sPackagePath, "ActionScript 3-0.tmLanguage.json")])

# copy package files
if os.path.exists(sSublimePackagesDir):
	shutil.rmtree(sCopyDestDir, ignore_errors=True)

	shutil.copytree(sPackagePath, sCopyDestDir)
