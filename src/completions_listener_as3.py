import os
import importlib
import threading
import sublime, sublime_plugin
import pprint

from os.path import join as pjoin

PACKAGE_NAME            = os.path.splitext( os.path.basename( os.path.dirname( os.path.realpath(__file__) ) ) )[0]
PACKAGE_PREFIX          = PACKAGE_NAME + "."

comp_formatter          = importlib.import_module(PACKAGE_PREFIX + "comp_formatter")
completions             = importlib.import_module(PACKAGE_PREFIX + "completions")
flex_config             = importlib.import_module(PACKAGE_PREFIX + "flex_config")
source_dir_as3          = importlib.import_module(PACKAGE_PREFIX + "source_dir_as3")
swc                     = importlib.import_module(PACKAGE_PREFIX + "swc")

SETTING_FILE_NAME       = PACKAGE_NAME + os.extsep + "sublime-settings"
FLEX_SDK_PATH_KEY       = "flex_sdk_path"
BUILD_CONFIG_PATH_KEY   = "build_config_path"
COMPLETIONS_ENABLED_KEY = "completions_enabled"

# completions types, used as keys in the enabled map
IMPORTS_KEY             = "imports"
NEWS_KEY                = "news"
TYPES_KEY               = "types"

FLEX_GLOBAL_SWC_DIR     = "frameworks/libs/player"

# map of Completion instances for each window; keys are that window's id()
gcCompletionsMap        = {}

# map of enabled completion types
gcEnabledMap            = {}

gsFlexSdkPath           = ""

# path to build xml, can be relative to sublime project
gsBuildXmlPath          = ""


def plugin_loaded():
    checkCompletions(sublime.active_window())

def checkCompletions(cWindow):
    if gcCompletionsMap.get(cWindow.id()) is None:
        reloadCompletions(cWindow)

def loadSettings():
    try:
        cPluginSettings = sublime.load_settings(SETTING_FILE_NAME)
    except:
        return

    global gsFlexSdkPath
    gsFlexSdkPath       = os.path.expanduser( cPluginSettings.get(FLEX_SDK_PATH_KEY) )

    # get config xml path
    global gsBuildXmlPath
    gsBuildXmlPath      = os.path.expanduser( cPluginSettings.get(BUILD_CONFIG_PATH_KEY) )

    # get enabled completions map
    global gcEnabledMap
    gcEnabledMap        = cPluginSettings.get(COMPLETIONS_ENABLED_KEY, {})


def reloadCompletions(cWindow):
    loadSettings()

    sBuildConfigPath    = pjoin(
        os.path.dirname( cWindow.project_file_name() ),
        gsBuildXmlPath
    )

    if os.path.exists(sBuildConfigPath):
        # ensure that a completions object for this window exists so that checkCompletions() will not attempt to
        # reload the completions whilst they are being generated
        if gcCompletionsMap.get(cWindow.id()) is None:
            gcCompletionsMap[cWindow.id()]  = completions.Completions()

        # start async completions generation
        threading.Thread(target=loadCompletions, args=(cWindow, sBuildConfigPath)).start()

def loadCompletions(cWindow, sConfigPath):
    global gcCompletionsMap

    if not os.path.exists(gsFlexSdkPath):
        # clear completions instance for this window so that checkCompletions will attempt to reload them
        gcCompletionsMap[cWindow.id()]  = None
        return

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
            pjoin(gsFlexSdkPath, FLEX_GLOBAL_SWC_DIR)
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
                pjoin(gsFlexSdkPath, FLEX_GLOBAL_SWC_DIR, sFlashVersion, "playerglobal.swc")
            )
        )

        if sGlobalSwcPath not in aSourceSwcs:
            aSourceSwcs.append(sGlobalSwcPath)

    aImports       = []
    aTypes         = []

    cSwcReader      = swc.SwcReader(gsFlexSdkPath)
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
    def run(self, edit):
        caretPos    = self.view.sel()[0]
        pprint.pprint(caretPos)
        print("word under caret = " + str(self.view.word(caretPos)))

class LoadSettingsAs3Command(sublime_plugin.WindowCommand):
    def run(self):
        loadSettings()

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
            iCurrentPoint   = locations[0];

            if gcEnabledMap.get(IMPORTS_KEY) != False:
                if view.score_selector(iCurrentPoint, self.SCOPE_IMPORT) > 0:
                    aAutoList   = cCompletions.getImports()
                    return aAutoList

            if gcEnabledMap.get(NEWS_KEY) != False:
                aMatches        = view.find_by_selector(self.SCOPE_NEW)

                for cRegion in aMatches:
                    if cRegion.contains(iCurrentPoint):
                        aAutoList   = cCompletions.getTypes()
                        return aAutoList

            if gcEnabledMap.get(TYPES_KEY) != False:
                # this is the scope that we want to target:
                #   meta.package.actionscript.3 meta.class.actionscript.3 meta.storage.type.actionscript.3
                # but for some reason the last one isn't showing up in the current scope string...
                aMatches        = view.find_by_selector(self.SCOPE_TYPE)

                for cRegion in aMatches:
                    if cRegion.contains(iCurrentPoint):
                        aAutoList   = cCompletions.getTypes()
                        return aAutoList

        return aAutoList