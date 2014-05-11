#!/usr/bin/python

import os, os.path
import shutil
import subprocess

sPackagePath		= "../src"
sSublimePackagesDir	= "C:/Users/Dean/AppData/Roaming/Sublime Text 3/Packages"
sCopyDestDir		= os.path.join(sSublimePackagesDir, "ActionScript 3-0")

# convert language json to plist
subprocess.call(["python", "json_to_plist.py", os.path.join(sPackagePath, "ActionScript 3-0.tmLanguage.json")])

# copy package files
if os.path.exists(sSublimePackagesDir):
	shutil.rmtree(sCopyDestDir, ignore_errors=True)

	shutil.copytree(sPackagePath, sCopyDestDir)
