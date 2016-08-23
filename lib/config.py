# This file contains default configuration options for openmw-mm
from ConfigParser import SafeConfigParser
import os.path


def init(path):
    """Create a default config file for openmw-mm"

    :path: (str) Path to the new config file.
    :returns: (SafeConfigParser) Newly created config object.
    """
    config = SafeConfigParser()
    # Defaults
    config.add_section("General")
    config.set("General", "mods_dir", "./unittests/mods")
    config.set("General", "plugin_extensions", ".esm .esp .omwaddon")
    config.set("General", "openmw_cfg", "~/.config/openmw/openmw.cfg")

    write_config(config, path)

    return config


# This function is taken straight from the core module
# This is so we dont have to import core.py since it relies on this module to run
# TODO: Fix above problem in a more elegant way.
def get_full_path(path):
    """Return the full expanded path of :path:.

    :path: (str) Path to expand.
    :returns: (str) Expanded path.
    """
    return os.path.abspath(os.path.expanduser(path))


def get_config_path():
    """Return the first path to an existing configuration file.
    If no file exists return the first one in the list of possible paths.

    :returns: (str) Absolute path to the config file.
    """
    paths = ["./openmw-mm.cfg", "~/.config/openmw/openmw-mm.cfg"]
    for path in paths:
        path = get_full_path(path)
        if os.path.exists(path):
            # Maybe raise an error or print a warrning here?
            if not os.path.isdir(path):
                return path

    # If no existing file can be found, return the first possible path.
    return get_full_path(paths[0])


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
# Im not really sure this is a good ideaa, this module may be imported from different places
# So this code might be executed multiple times which is not good.
path = get_config_path()
if not os.path.exists(path):
    # No config file detected, create a new one
    config = init(path)
else:
    # Config file already exists.
    config = read_config(path)
