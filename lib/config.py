# TODO: Rework this module, its kind of messy.
from ConfigParser import SafeConfigParser
import os.path
import core
import sys


def set_defaults(config):
    """Set default configuration options, taking into consideration different platforms.

    :config: (ConfigParser) config object to populate
    :returns: (ConfigParser)
    """
    if sys.platform == "win32":  # Windows
        openmw_cfg = "%USERPROFILE%\My Documents\My Games\openmw\openmw.cfg"
        mods_dir = "%USERPROFILE%\My Documents\My Games\openmw\mods"

    elif sys.platform == "darwin":  # Mac
        openmw_cfg = "$HOME/Library/Preferences/openmw/openmw.cfg"
        mods_dir = "$HOME/Library/Preferences/openmw/mods"

    else:  # Default to linux?
        openmw_cfg = "$HOME/.config/openmw/openmw.cfg"
        mods_dir = "$HOME/.local/share/openmw/mods"

    config.add_section("General")
    config.set("General", "openmw_cfg", core.get_full_path(openmw_cfg))
    config.set("General", "mods_dir", core.get_full_path(mods_dir))
    config.set("General", "never_merge", "Morrowind.esm,Tribunal.esm,Bloodmoon.esm,Merged_Lists.esp")

    return config


def init(path):
    """Create a default config file for omw-mm"

    :path: (str) Path to the new config file.
    :returns: (SafeConfigParser) Newly created config object.
    """
    config = SafeConfigParser()

    # Defaults
    config = set_defaults(config)

    write_config(config, path)
    return config


# TODO: Update this with crossplatform paths.
# Better yet just stop doing this and store the config file next to the script
def get_config_path():
    """Return the first path to an existing configuration file.
    If no file exists return the first one in the list of possible paths.

    :returns: (str) Absolute path to the config file.
    """
    paths = [os.path.join(core.get_base_dir(), "./omw-mm.cfg")]
    for path in paths:
        path = core.get_full_path(path)
        if os.path.exists(path):
            # Maybe raise an error or print a warrning here?
            if not os.path.isdir(path):
                return path

    # If no existing file can be found, return the first possible path.
    return core.get_full_path(paths[0])


def read_config(path):
    """Read the config from a given config file.

    :path: (str) Path to the config file.
    :returns: (SafeConfigParser) Config object.
    """
    config = SafeConfigParser()
    config.read(path)

    return config


def write_config(config, path):
    """Save config to disk.

    :config: (ConfigParser) Config object.
    :path: (str) Path to file to be written into.
    """

    # TODO: More checks before saving.
    with open(path, "w+") as fp:
        config.write(fp)


# Present the config object to be imported here.
path = get_config_path()
if not os.path.exists(path):
    # No config file detected, create a new one
    config = init(path)
else:
    # Config file already exists.
    config = read_config(path)
