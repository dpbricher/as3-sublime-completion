# ActionScript 3.0 Sublime Text Auto Completion

Sublime Text plugin to provide ActionScript 3.0 auto completion.

## Prerequisites

- Sublime Text 3
- Python 2.7+

## Installation

After cloning the project modify the `flex_sdk_path` value of the "ActionScript 3-0.sublime-settings" file (found in "src") so that it points to the location of your flex sdk (you can change this value later).  Then run one of the installation scripts, install-debug.py or install-package.py:

    python [path_to_project]/build/install-package.py

## Configuration

You can access the package settings in sublime, via "Preferences > Settings - ActionScript 3.0".  Currently the following settings are required:

- `flex_sdk_path` : The path to the flex sdk directory
- `build_config_path` : The path to check for the flex config xml file that is used to generate completions (see next section).  Can be relative to the sublime-project file
- `flex_global_swc_dir` : The directory in which the flex player global swcs are located.  Can be relative to the `flex_sdk_path` (You shouldn't need to change this setting)
- `project_settings_key` : The json key to use for specifying per project settings

And one optional setting:

- `completions_enabled` : Boolean flags that can be used to disable specific types of completions, by setting that flag to "false"

It is also possible to specify a unique path to the flex config xml per project.  You can do this by creating a dictionary in the sublime-project file using the value of `project_settings_key` as the key, and giving it a `build_config_path` value, i.e.

    "actionscript-3.0":
    {
        "build_config_path" : "my/custom/path/build-config.xml"
    }

## Flex Config XML

This plugin generates completions by parsing a [flex configuration file](http://help.adobe.com/en_US/flex/using/WS2db454920e96a9e51e63e3d11c0bf69084-7fca.html), which it will attempt to find by following the `build_config_path` set first in the current project and then in the package settings (the idea being that you supply the path of the xml file you are using to actually compile your as3 code).  An example of a minimalist configuration file:

    <flex-config>
        <compiler>
            <source-path>
                <path-element>src</path-element>
            </source-path>
        </compiler>
        <file-specs>
            <path-element>src/com/dricher/example/Main.as</path-element>
        </file-specs>
    </flex-config>

## Usage

This package comes with its own syntax, ActionScript 3.0.  In order to receive plugin generated auto completions you have to be using this syntax.  Currently it will provide completions for "import" statements, var "type" (i.e. var myClip:MovieClip) and "new" declarations.  Completion generation can be forced manually via the `create_completions_as3` command.

I have also added a command for automatically inserting "import" statements into a document based on the current position of the caret, `auto_import_as3`.  Running it will trigger a drop down list of import statements matching the type under the caret (so long as there is at least one match), and selecting an item from the list will insert it into the current document on the highest line possible within that document's "package" statement, indented with a single tab.

Some example [key bindings](http://docs.sublimetext.info/en/sublime-text-3/customization/key_bindings.html) for these commands:

    { "keys": ["alt+c"], "command": "create_completions_as3" },
    { "keys": ["alt+shift+c"], "command": "auto_import_as3" }

(If you don't know how these work then you can just add them inside your default user sublime keymap, which you can open from Sublime via "Preferences > Key Bindings - User")

## Caveats

- Currently "var" declarations must be terminated with semi-colons in order for the syntax for this package to work correctly, even though they are technically optional
- Completions for each project are generated automatically when sublime first opens or when a file is loaded within a window attached to that project.  Once completions have been generated they will not be regenerated, even if new files are added or the flex config xml is changed.  In order to update the completions you have to manually trigger the `create_completions_as3` command

## Bugs

Sadly the syntax definitions for this package still need a little work.  Here is a list of some of the bugs that are already on my radar:

- Shorthand "if" statements within variable declarations erroneously get picked up as a variable declaration if both the true and false actions are variables (e.g. var maxNum:Number = numA > numB ? numA : numB;)
- The auto completion for imports gets triggered when naming/extending classes
- "const"s used as default arguments in function declarations get scoped (and thus coloured) as function parameters