import os
import importlib
import threading
import sublime, sublime_plugin

from os.path import join as pjoin

PACKAGE_NAME            = os.path.splitext( os.path.basename( os.path.dirname( os.path.realpath(__file__) ) ) )[0]
PACKAGE_PREFIX          = PACKAGE_NAME + "."

comp_formatter          = importlib.import_module(PACKAGE_PREFIX + "comp_formatter")
completions             = importlib.import_module(PACKAGE_PREFIX + "completions")
flex_config             = importlib.import_module(PACKAGE_PREFIX + "flex_config")
source_dir_as3          = importlib.import_module(PACKAGE_PREFIX + "source_dir_as3")
swc                     = importlib.import_module(PACKAGE_PREFIX + "swc")
settings                = importlib.import_module(PACKAGE_PREFIX + "settings")
# shorthand for settings keys
Keys                    = settings.GlobalKeys

# map of ProjectSettings for each window; keys are that window's id()
gcProjSettingsMap       = {}

# map of Completion instances for each window; keys are that window's id()
gcCompletionsMap        = {}

gcSettings              = settings.GlobalSettings()


def plugin_loaded():
    checkCompletions(sublime.active_window())

def checkCompletions(cWindow):
    if gcCompletionsMap.get(cWindow.id()) is None:
        reloadCompletions(cWindow)

def loadGlobalSettings():
    gcSettings.loadSettings()

def loadProjectSettings(cWindow):
    cProjSettings       = gcProjSettingsMap.get(cWindow.id())
    
    if cProjSettings is None:
        cProjSettings   = settings.ProjectSettings(
            gcSettings.get(Keys.PROJECT_SETTINGS_KEY)
        )
        gcProjSettingsMap[cWindow.id()] = cProjSettings

    cProjSettings.loadSettings(cWindow)

def reloadCompletions(cWindow):
    loadGlobalSettings()

    if gcSettings.hasErrors():
        sublime.error_message(gcSettings.getErrors())
        return

    loadProjectSettings(cWindow)

    # construct list of build config paths to check for here
    aConfigPaths        = []

    # get config path from global settings
    sBuildConfigPath    = pjoin(
        os.path.dirname( cWindow.project_file_name() ),
        gcSettings.get(Keys.BUILD_CONFIG_PATH)
    )

    # add project config path
    aConfigPaths.append(
        gcProjSettingsMap.get(cWindow.id()).getConfigPath()
    )

    # add global config path
    aConfigPaths.append(sBuildConfigPath)

    # load completions using first config file that is found to exist
    for sPath in aConfigPaths:
        if os.path.exists(sPath):
            # ensure that a completions object for this window exists so that checkCompletions() will not attempt to
            # reload the completions whilst they are being generated
            if gcCompletionsMap.get(cWindow.id()) is None:
                gcCompletionsMap[cWindow.id()]  = completions.Completions()

            # start async completions generation
            threading.Thread(target=loadCompletions, args=(cWindow, sPath)).start()
            break

def loadCompletions(cWindow, sConfigPath):
    global gcCompletionsMap

    sFlexSdkPath        = gcSettings.get(Keys.FLEX_SDK_PATH)
    sFlexGlobalSwcDir   = gcSettings.get(Keys.FLEX_GLOBAL_SWC_DIR)

    aSourceDirs         = []
    aSourceSwcs         = []

    sFlashVersion       = ""

    cConfigReader       = flex_config.FlexConfigParser()
    cConfigReader.readConfig(sConfigPath)
    cConfigReader.parseData()

    sFlashVersion       = cConfigReader.getFlashVersion()

    if sFlashVersion == "":
        # set global swc to latest available
        aAllVersions    = os.listdir(
            pjoin(sFlexSdkPath, sFlexGlobalSwcDir)
        )
        aAllVersions.sort()

        sFlashVersion   = aAllVersions.pop()

    if cConfigReader != None:
        aSourceDirs     = cConfigReader.getSourceDirs()
        aSourceSwcs     = cConfigReader.getSourceSwcs()

    # add global swc source path if specified by the build config
    if cConfigReader == None or cConfigReader.getAppendExternalFlag():
        sGlobalSwcPath      = os.path.realpath(
            os.path.expanduser(
                pjoin(sFlexSdkPath, sFlexGlobalSwcDir, sFlashVersion, "playerglobal.swc")
            )
        )

        if sGlobalSwcPath not in aSourceSwcs:
            aSourceSwcs.append(sGlobalSwcPath)

    aImports       = []
    aTypes         = []

    cSwcReader      = swc.SwcReader(sFlexSdkPath)
    cDirReader      = source_dir_as3.SourceDirAs3Reader()

    cFormatter      = comp_formatter.CompletionFormatter()

    for sPath in aSourceDirs:
        cDirReader.readDir(sPath)
        cDirReader.parseData()

        # add any swcs found within source dirs to the swc list
        aSourceSwcs += cDirReader.getSourceSwcs()

        aImports    += cFormatter.createImportList(cDirReader.getFqClassNames())
        aTypes      += cFormatter.createTypeList(cDirReader.getFqClassNames())

    for sPath in aSourceSwcs:
        cSwcReader.readSwc(sPath)
        cSwcReader.parseData()

        aImports    += cFormatter.createImportList(cSwcReader.getFqClassNames())
        aTypes      += cFormatter.createTypeList(cSwcReader.getFqClassNames())

    gcCompletionsMap[cWindow.id()]   = completions.Completions(aImports, aTypes)

class AutoImportAs3Command(sublime_plugin.TextCommand):
    def __init__(self, arg2):
        super().__init__(arg2)

        self.aMatches   = None
        self.cEdit      = None

    def run(self, edit):
        cWindow         = sublime.active_window()
        cCompletions    = gcCompletionsMap.get(cWindow.id())

        if cCompletions is not None:
            caretPos        = self.view.sel()[0]
            typeUnderCaret  = self.view.substr(
                self.view.word(caretPos)
            )

            self.aMatches   = [t[0] for t in cCompletions.getImports() if t[0].endswith("." + typeUnderCaret + ";")]

            if len(self.aMatches) > 0:
                self.cEdit  = edit
                self.view.show_popup_menu(self.aMatches, self.onImportSelection)

    def onImportSelection(self, index):
        if index > -1:
            cPackageRegion  = self.view.find(r"package[^\{]*\{[^\n]*\n", 0)

            self.view.insert(
                self.cEdit,
                cPackageRegion.b,
                "\t" + self.aMatches[index] + "\n"
            )

class CreateCompletionsAs3Command(sublime_plugin.WindowCommand):
    def run(self):
        reloadCompletions(self.window)

class CompletionsListenerAs3(sublime_plugin.EventListener):
    SCOPE_IMPORT            = "source.actionscript.3 meta.package.actionscript.3 - meta.class.actionscript.3"
    SCOPE_NEW               = "source.actionscript.3 meta.class.actionscript.3 meta.storage.new.actionscript.3"
    SCOPE_TYPE              = "source.actionscript.3 meta.class.actionscript.3 meta.storage.type.actionscript.3"

    def on_load_async(self, view):
        checkCompletions(view.window())

    def on_query_completions(self, view, prefix, locations):
        aAutoList       = None

        cWindow         = sublime.active_window()
        cCompletions    = gcCompletionsMap.get(cWindow.id())

        if cCompletions is not None and len(locations) == 1:
            cEnabledMap     = gcSettings.get(Keys.COMPLETIONS_ENABLED)

            iCurrentPoint   = locations[0];

            if cEnabledMap.get(Keys.COMP_IMPORTS) != False:
                if view.score_selector(iCurrentPoint, self.SCOPE_IMPORT) > 0:
                    aAutoList   = cCompletions.getImports()
                    return aAutoList

            if cEnabledMap.get(Keys.COMP_NEWS) != False:
                aMatches        = view.find_by_selector(self.SCOPE_NEW)

                for cRegion in aMatches:
                    if cRegion.contains(iCurrentPoint):
                        aAutoList   = cCompletions.getTypes()
                        return aAutoList

            if cEnabledMap.get(Keys.COMP_TYPES) != False:
                # this is the scope that we want to target:
                #   meta.package.actionscript.3 meta.class.actionscript.3 meta.storage.type.actionscript.3
                # but for some reason the last one isn't showing up in the current scope string...
                aMatches        = view.find_by_selector(self.SCOPE_TYPE)

                for cRegion in aMatches:
                    if cRegion.contains(iCurrentPoint):
                        aAutoList   = cCompletions.getTypes()
                        return aAutoList

        return aAutoList