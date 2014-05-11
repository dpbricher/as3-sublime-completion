#!/usr/bin/python

import os, os.path
import shutil

sPackageName		= "ActionScript 3-0.sublime-package"
sPackagePath		= os.path.join("../bin/", sPackageName)
sSublimePackagesDir	= "C:/Program Files/Sublime Text 3/Packages"

if not os.path.exists(sPackagePath):
	os.system("build-package.py")

if os.path.exists(sSublimePackagesDir):
	sCopyDest	= os.path.join(sSublimePackagesDir, sPackageName)
	
	if os.path.exists(sCopyDest):
		os.remove(sCopyDest)
	
	shutil.copy(sPackagePath, sSublimePackagesDir)