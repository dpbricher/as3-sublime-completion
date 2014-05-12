#!/usr/bin/python

import os, os.path
import shutil
import sys

sPackageName            = "ActionScript 3-0.sublime-package"
sPackagePath            = os.path.join("../bin/", sPackageName)

sSublimePackagesDir     = {
    "darwin"    : "C:/Program Files/Sublime Text 3/Packages",
    "win32"     : "C:/Program Files/Sublime Text 3/Packages"
    # "linux"     : ""
}.get(sys.platform)

if sSublimePackagesDir is None:
    sSublimePackagesDir = ""

if not os.path.exists(sSublimePackagesDir):
    print("Cannot find Sublime Text packages directory")
    exit()

if not os.path.exists(sPackagePath):
    os.system("build-package.py")

if os.path.exists(sSublimePackagesDir):
    sCopyDest   = os.path.join(sSublimePackagesDir, sPackageName)

    if os.path.exists(sCopyDest):
        os.remove(sCopyDest)

    shutil.copy(sPackagePath, sSublimePackagesDir)