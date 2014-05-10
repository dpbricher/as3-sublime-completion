#!/usr/bin/python

import os
import zipfile

SRC_DIR			= "../src"
BIN_DIR			= "../bin"
PACKAGE_NAME	= "ActionScript 3-0.sublime-package"

# create bin dir
os.makedirs(BIN_DIR, exist_ok=True)

# open package archive
cPackage		= zipfile.ZipFile( os.path.join(BIN_DIR, PACKAGE_NAME), "w" )
aExcludeDirs	= ["__pycache__"]

# write files
for sRoot, aDirs, aFiles in os.walk(SRC_DIR):
	# add files to archive
	for sName in aFiles:
		cPackage.write( os.path.join(sRoot, sName), arcname=sName )

	# remove excluded firs from the walk operation
	for sDir in aDirs:
		if sDir in aExcludeDirs:
			aDirs.remove(sDir)

# close archive
cPackage.close()