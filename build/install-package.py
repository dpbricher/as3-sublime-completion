#!/usr/bin/python

import os, os.path
import shutil

sPackagePath		= "../bin/ActionScript 3-0.sublime-package"
sSublimePackagesDir	= "C:/Program Files/Sublime Text 3/Packages"

if not os.path.exists(sPackagePath):
	os.system("build-package.py")

if os.path.exists(sSublimePackagesDir):
	shutil.copy(sPackagePath, sSublimePackagesDir)