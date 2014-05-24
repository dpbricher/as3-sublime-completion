#!/usr/bin/python

import os, os.path
import shutil
import subprocess
import sys

sSettingsPath			= "../src/ActionScript 3-0.sublime-settings"
sSublimePackagesDir		= {
	"darwin"	: "~/Library/Application Support/Sublime Text 3/Packages",
	"win32" 	: "~/AppData/Roaming/Sublime Text 3/Packages",
	"linux" 	: "~/.config/sublime-text-3/Packages"
}.get(sys.platform)

if sSublimePackagesDir is None:
	sSublimePackagesDir	= ""

sSublimePackagesDir		= os.path.expanduser(sSublimePackagesDir)

if not os.path.exists(sSublimePackagesDir):
	print("Cannot find Sublime Text packages directory")
	exit()

sCopyDestDir			= os.path.join(sSublimePackagesDir, "User")

# copy settings file
if os.path.exists(sCopyDestDir):
	shutil.copy(sSettingsPath, sCopyDestDir)
