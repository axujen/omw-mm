# This file contains default configuration options for openmw-mm
from ConfigParser import SafeConfigParser
import os.path
import core


def init(path):
    """Create a default config file for openmw-mm"

    :path: (str) Path to the new config file.
    :returns: (SafeConfigParser) Newly created config object.
    """
    config = SafeConfigParser()
    # Defaults
    config.add_section("General")
    config.set("General", "mods_dir", "~/.local/share/openmw/mods")
    config.set("General", "openmw_cfg", "~/.config/openmw/openmw.cfg")

    write_config(config, path)

    return config


def get_config_path():
    """Return the first path to an existing configuration file.
    If no file exists return the first one in the list of possible paths.

    :returns: (str) Absolute path to the config file.
    """
    paths = ["./openmw-mm.cfg", "~/.config/openmw/openmw-mm.cfg"]
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
