#!/usr/bin/python

import os
import shutil
import zipfile
import subprocess

SRC_DIR			= "../src"
BIN_DIR			= "../bin"
PACKAGE_NAME	= "ActionScript 3-0.sublime-package"

# create bin dir
shutil.rmtree(BIN_DIR, ignore_errors=True)
os.makedirs(BIN_DIR)

# convert language json to plist
subprocess.call(["python", "json_to_plist.py", os.path.join(SRC_DIR, "ActionScript 3-0.tmLanguage.json")])

# open package archive
cPackage		= zipfile.ZipFile( os.path.join(BIN_DIR, PACKAGE_NAME), "w" )
aExcludeFiles	= ["ActionScript 3-0.tmLanguage.json", "ActionScript 3-0.sublime-settings"]
aExcludeDirs	= ["__pycache__"]

# write files
for sRoot, aDirs, aFiles in os.walk(SRC_DIR):
	# add files to archive
	for sName in aFiles:
		if sName not in aExcludeFiles:
			cPackage.write( os.path.join(sRoot, sName), arcname=sName )

	# remove excluded firs from the walk operation
	for sDir in aDirs:
		if sDir in aExcludeDirs:
			aDirs.remove(sDir)

# close archive
cPackage.close()
