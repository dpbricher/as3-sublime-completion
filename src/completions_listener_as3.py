import os
import sublime, sublime_plugin
import importlib

from os.path import join as pjoin

PACKAGE_NAME            = os.path.basename( os.path.dirname( os.path.realpath(__file__) ) )
PACKAGE_PREFIX          = PACKAGE_NAME + "."

comp_formatter          = importlib.import_module(PACKAGE_PREFIX + "comp_formatter")
completions             = importlib.import_module(PACKAGE_PREFIX + "completions")
flex_config             = importlib.import_module(PACKAGE_PREFIX + "flex_config")
source_dir_as3          = importlib.import_module(PACKAGE_PREFIX + "source_dir_as3")
swc                     = importlib.import_module(PACKAGE_PREFIX + "swc")

SETTING_FILE_NAME       = PACKAGE_NAME + os.extsep + "sublime-settings"
FLEX_SDK_PATH_KEY       = "flex_sdk_path"
BUILD_CONFIG_PATH_KEY   = "build_config_path"

FLEX_GLOBAL_SWC_DIR     = "frameworks/libs/player"

# map of Completion instances for each window; keys are that window's id()
gcCompletionsMap        = {}

gsBuildXml              = None


def plugin_loaded():
    checkCompletions(sublime.active_window())

def checkCompletions(cWindow):
    if gcCompletionsMap.get(cWindow.id()) is None:
        reloadCompletions(cWindow)

def reloadCompletions(cWindow):
    cPluginSettings = sublime.load_settings(SETTING_FILE_NAME)

    global gsBuildXml
    gsBuildXml      = pjoin(
        os.path.dirname(cWindow.project_file_name()),
        cPluginSettings.get(BUILD_CONFIG_PATH_KEY)
    )

    if os.path.exists(gsBuildXml):
        loadCompletions(cWindow)

def loadCompletions(cWindow):
    try:
        cSettings       = sublime.load_settings(SETTING_FILE_NAME)
        sFlexSdkPath    = cSettings.get(FLEX_SDK_PATH_KEY)
    except (e):
        return

    aSourceDirs         = []
    aSourceSwcs         = []

    sFlashVersion       = ""

    if gsBuildXml:
        cConfigReader   = flex_config.FlexConfigParser()
        cConfigReader.readConfig(gsBuildXml)
        cConfigReader.parseData()

        sFlashVersion   = cConfigReader.getFlashVersion()

    if sFlashVersion == "":
        # set global swc to latest available
        aAllVersions    = os.listdir(
            pjoin(sFlexSdkPath, FLEX_GLOBAL_SWC_DIR)
        )
        aAllVersions.sort()

        sFlashVersion   = aAllVersions.pop()

    if cConfigReader != None:
        aSourceDirs     = cConfigReader.getSourceDirs()
        aSourceSwcs     = cConfigReader.getSourceSwcs()

    # add global swc source path so long as config does not have source-path append="false"
    if cConfigReader == None or cConfigReader.getAppendSourceFlag():
        sGlobalSwcPath      = os.path.realpath(
            pjoin(sFlexSdkPath, FLEX_GLOBAL_SWC_DIR, sFlashVersion, "playerglobal.swc")
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

    global gcCompletionsMap

    gcCompletionsMap[cWindow.id()]   = completions.Completions(aImports, aTypes)

class CreateCompletionsAs3Command(sublime_plugin.WindowCommand):
    def run(self):
        reloadCompletions(self.window)

class CompletionsListenerAs3(sublime_plugin.EventListener):
    SCOPE_IMPORT            = "source.actionscript.3 meta.package.actionscript.3 - meta.class.actionscript.3"
    SCOPE_TYPE              = "source.actionscript.3 meta.class.actionscript.3 meta.storage.type.actionscript.3"

    def on_load_async(self, view):
        checkCompletions(view.window())

    def on_query_completions(self, view, prefix, locations):
        aAutoList       = None

        cWindow         = sublime.active_window()
        cCompletions    = gcCompletionsMap.get(cWindow.id())

        if cCompletions is not None and len(locations) == 1:
            iCurrentPoint   = locations[0];

            if view.score_selector(iCurrentPoint, self.SCOPE_IMPORT) > 0:
                aAutoList   = cCompletions.getImports()

            # this is the scope that we want to target:
            #   meta.package.actionscript.3 meta.class.actionscript.3 meta.storage.type.actionscript.3
            # but for some reason the last one isn't showing up in the current scope string...
            else:
                aMatches        = view.find_by_selector(self.SCOPE_TYPE)

                for cRegion in aMatches:
                    if cRegion.contains(iCurrentPoint):
                        aAutoList   = cCompletions.getTypes()
                        break

        return aAutoList