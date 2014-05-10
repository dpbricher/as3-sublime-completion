class Completions:
    def __init__(self, aImports = [], aTypes = []):
        self.aImports   = aImports
        self.aTypes     = aTypes

    def setImports(self, aList):
        self.aImports   = aList

    def setTypes(self, aList):
        self.aTypes     = aList

    def getImports(self):
        return self.aImports

    def getTypes(self):
        return self.aTypes