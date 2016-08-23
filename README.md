# openmw-utils
openmw-utils is my attempt at creating a suite of utils to manage openmw mods.

Right only a script to install and uninstall mods exists.
But the project aims to provide the ability to manage plugins, merge leveled lists and sort the load order automatically

In the distant future i may even add windows support and a GUI (Don't ask me when though, i dont even know where to begin)
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
    list                List installed mods
    clean               Clean non existing mod dirs from openmw.cfg
    install             Install a directory as mod
    uninstall           Uninstall a mod directory

```
