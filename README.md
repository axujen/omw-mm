# omw-mm
omw-mm is my attempt at creating an advanced mod management suite for openmw.

Right now a cli script is up and running (expect bugs though).
This script can handle the following operations:
  - Install a mod from a directory (archive support is being considered)
  - Uninstall an already installed mod
  - List currently installed mods
  - Enable/Disable plugins
  - List currently available plugins, either sorted by load order or in a tree showing parent mods.
  - Clean openmw.cfg from references to unavailable directories and plugins, so you can manually delete mods and have the script clean up openmw.cfg for you
  - *NEW* Merge Leveled Lists (See a note below)

The project also aims to provide cross-platform support for windows (and hopefully mac) as well as the ability to sort mods with mlox and create merged leveled lists.

A GUI is also planned but don't ask me when, i don't even know where to begin with that.
# USAGE

omw-mm-cli.py
================
```
% omw-mm-cli.py --help
usage: omw-mm-cli [-h] [-f file] <command> ...

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
Run omw-mm-cli.py command --help for additional help about each command.

# NOTE
The merge command is still new an experimental, i tries to emulate Wrye Mash and TESTool merged lists feature (without the need for resquencing) but it may not be 100% accurate.

If you have any info on how to improve it, please email me or open an issue in the github tracker


# WARNING
Backup your openmw.cfg file and even your mods directory, this project is in early developement and may (i should say will) cause damage.
