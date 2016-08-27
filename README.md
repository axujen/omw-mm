# openmw-mm
openmw-mm is my attempt at creating an advanced mod management suite for openmw.

Right now a cli script is up and running (expect bugs though).
This script can handle the following operations:
  - Install a mod from a directory (archive support is being considered)
  - Uninstall an already installed mod
  - Enable/Disable plugins
  - List currently installed mods
  - List currently available plugins, sorted by load order for enabled plugins.
  - List currently available plugins in a tree view that shows the parent mod of each plugin
  - Clean openmw.cfg from references to unavailable directories, so you can manually delete mods and have the script clean up openmw.cfg for you

The project also aims to provide cross-platform support for windows (and hopefully mac) as well as the ability to sort mods with mlox and create merged leveled lists.

A GUI is also planned but don't ask me when, i don't even know where to begin with that.
# USAGE

openmw-mm-cli.py
================
```
% openmw-mm-cli.py --help
usage: openmw-mm-cli [-h] [-f file] <command> ...

optional arguments:
  -h, --help            show this help message and exit
  -f file, --file file  Path to openmw.cfg

Commands:
  <command>
    install             Install a directory as mod
    uninstall           Uninstall a mod directory
    enable              Enable a plugin
    disable             disable a plugin
    list                List installed mods
    list-plugins        List plugins
    clean               Clean non existing mod dirs from openmw.cfg
    merge               Merge all leveled lists into one file
```
Run openmw-mm-cli.py command --help for additional help about each command.

# NOTE
The merge command is very simple at the moment, it does not actuallly merge leveled lists, instead it adds them, all of them into a single file, so you will probably end up with duplicate records. Please contact me if you have any ideas on how to improve this feature.

# WARNING
Backup your openmw.cfg file and even your mods directory, this project is in early developement and may (i should say will) cause damage.
