import os

class SourceDirAs3Reader():
	AS_EXT			= os.extsep + "as"
	AS_EXT_LEN		= len(AS_EXT)

	def __init__(self):
		self.sSourceDir		= None
		self.aSourceFiles	= None
		self.aSourceSwcs	= None

		self.aFqClassNames  = None

	def readDir(self, sDirPath):
		aPaths	= []

		self.sSourceDir		= sDirPath

		self.aSourceFiles	= []
		self.aSourceSwcs	= []

		for cInfo in os.walk(self.sSourceDir, True, None, True):
			for sFile in cInfo[2]:
				if sFile.endswith(self.AS_EXT):
					self.aSourceFiles.append( os.path.join(cInfo[0], sFile) )

		# for s in self.aSourceFiles:
			# print("found source file : " + s)

	def parseData(self):
        self.aFqClassNames  = []

        for sPath in self.aSourceFiles:
            sPath   = os.path.relpath(sPath, self.sSourceDir)
            sPath   = sPath[:-self.AS_EXT_LEN]
            sPath   = sPath.replace(os.sep, ".")

            self.aFqClassNames.append(sPath)