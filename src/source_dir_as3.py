import os

class SourceDirAs3Reader():
	AS_EXT			= os.extsep + "as"
	AS_EXT_LEN		= len(AS_EXT)

	SWC_EXT			= os.extsep + "swc"

	def __init__(self):
		self.sSourceDir		= None
		self.aSourceFiles	= None
		self.aSourceSwcs	= None

		self.aFqClassNames  = None

	def readDir(self, sDirPath):
		aPaths	= []

		self.sSourceDir		= sDirPath

		self.aSourceFiles	= []

		# find all ActionScript source files within source dir
		for cInfo in os.walk(self.sSourceDir, True, None, True):
			for sFile in cInfo[2]:
				if sFile.endswith(self.AS_EXT):
					self.aSourceFiles.append( os.path.join(cInfo[0], sFile) )

		self.aSourceSwcs	= [os.path.join(self.sSourceDir, s) for s in os.listdir(self.sSourceDir) if s.endswith(self.SWC_EXT)]

	def parseData(self):
        self.aFqClassNames  = []

        for sPath in self.aSourceFiles:
            sPath   = os.path.relpath(sPath, self.sSourceDir)
            sPath   = sPath[:-self.AS_EXT_LEN]
            sPath   = sPath.replace(os.sep, ".")

            self.aFqClassNames.append(sPath)

    def getFqClassNames(self):
        return self.aFqClassNames

    def getSourceSwcs(self):
        return self.aSourceSwcs