import os
import sublime


class SettingsManager():
    PACKAGE_NAME        = os.path.splitext( os.path.basename( os.path.dirname( os.path.realpath(__file__) ) ) )[0]
    SETTINGS_FILE_NAME  = PACKAGE_NAME + os.extsep + "sublime-settings"

    def __init__(self):
        # settings object as supplied
        self.cRaw       = {}
        # dictionary of formatted settings
        self.cFormatted = {}

        self.aErrors    = []

    def loadSettings(self):
        self.aErrors    = []

        self._validateSettings()

        if self.hasErrors() == False:
            self._formatSettings()

    def get(self, sKey):
        return self.cFormatted.get(sKey)

    def hasErrors(self):
        return len(self.aErrors) > 0

    def getErrors(self):
        return "\n\n".join(self.aErrors)


    def _validateSettings(self):
        try:
            self.cRaw       = sublime.load_settings(self.SETTINGS_FILE_NAME)
        except:
            self.aErrors.append("Problem loading settings file")
            return

        self._checkExists(Keys.FLEX_SDK_PATH, Keys.FLEX_SDK_PATH + " missing")
        self._checkExists(Keys.BUILD_CONFIG_PATH, Keys.BUILD_CONFIG_PATH + " missing")

        self._checkType(Keys.FLEX_SDK_PATH, str)
        self._checkType(Keys.BUILD_CONFIG_PATH, str)

        if self.cRaw.get(Keys.COMPLETIONS_ENABLED) is not None:
            self._checkType(Keys.COMPLETIONS_ENABLED, dict)

    def _formatSettings(self):
        self.cFormatted = {}

        self.cFormatted[Keys.FLEX_SDK_PATH]         = os.path.expanduser( self.cRaw.get(Keys.FLEX_SDK_PATH) )
        self.cFormatted[Keys.BUILD_CONFIG_PATH]     = os.path.expanduser( self.cRaw.get(Keys.BUILD_CONFIG_PATH) )
        self.cFormatted[Keys.COMPLETIONS_ENABLED]   = self.cRaw.get(Keys.COMPLETIONS_ENABLED, {})

        # check paths exist
        # (can't check build config path, since it is relative for each window)
        for sKey in [Keys.FLEX_SDK_PATH]:
            if os.path.exists( self.get(sKey) ) == False:
                self.aErrors.append("Path specified by " + sKey + " does not exist or cannot be accessed")

        # check path types
        if os.path.isdir(self.get(Keys.FLEX_SDK_PATH)) == False:
            self.aErrors.append("Path specified by " + Keys.FLEX_SDK_PATH + " is not a directory")

    def _checkExists(self, sKey, sErrorMessage):
        if self.cRaw.get(sKey) is None:
            self.aErrors.append(sErrorMessage)

    def _checkType(self, sKey, cType):
        cTypeFound  = type(self.cRaw.get(sKey))

        if cTypeFound is not cType:
            self.aErrors.append("Setting for " + sKey + " should be " + str(cType) + ", but " + str(cTypeFound) + " found")


class Keys():
    FLEX_SDK_PATH       = "flex_sdk_path"
    BUILD_CONFIG_PATH   = "build_config_path"
    COMPLETIONS_ENABLED = "completions_enabled"

    # completion keys
    COMP_IMPORTS        = "imports"
    COMP_NEWS           = "news"
    COMP_TYPES          = "types"