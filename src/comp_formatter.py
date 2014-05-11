import re

class CompletionFormatter:
    def __init__(self):
        pass

    def createImportList(self, aFqClassNames):
        aImports    = [
            ("import " + s.replace("/", ".") + ";",) for s in aFqClassNames if re.search(r"[/\.]", s) != None
        ]

        return aImports

    def createTypeList(self, aFqClassNames):
        aTypes  = [
            ( s, re.sub(r".*\.", "", s) ) for s in aFqClassNames
        ]

        return aTypes