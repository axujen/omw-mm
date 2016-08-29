# Core functions used in both CLI and GUI
import os
import sys
import shutil
from esm import Esm


def is_mod_dir(dir):
    """Check if given directory is an openmw mod directory.

    :dir: (str) Path to the mod directory.
    :returns: (bool)
    """

    # Checking for file/directory names is kind of bad but i cant figure out
    # another method.
    plugin_extensions = [".esp", ".esm", "omwaddon"]
    resource_directories = ["Textures", "Meshes", "Icons", "Fonts", "Sound",
                            "BookArt", "Splash", "Video"]
    for file in os.listdir(dir):
        # Check for morrowind resource folders
        if os.path.isdir(os.path.join(dir, file)):
            for resource_dir in resource_directories:
                if file.lower() == resource_dir.lower():
                    return True
        else:  # Check for morrowind plugin files ( .esm .esp etc)
            for ext in plugin_extensions:
                if file.endswith(ext):
                    return True

    return False


# TODO: This is a delicate operation, make sure its as safe as possible.
def copy_to_mod_dir(dir, dest):
    """Move the given directory to a new folder.

    :dir: (str) Absolute path to the source directory.
    :dest: (str) Absolute path to the destination mod directory.
    :returns: (str) Absolute path to the moved directory.
    """
    new_dir = os.path.join(dest, os.path.basename(dir))
    shutil.copytree(dir, new_dir)
    return new_dir


def get_full_path(path):
    """Return the full expanded path of :path:.

    :path: (str) Path to expand.
    :returns: (str) Expanded path.
    """

    # Expand env variables.
    path = os.path.expandvars(path)
    # Expand user (~)
    path = os.path.expanduser(path)
    # Get the absolute path
    path = os.path.abspath(path)
    # normalize
    path = os.path.normpath(path)
    path = os.path.normcase(path)

    return path


# TODO: Make this function safer.
def rm_mod_dir(mod_dir):
    """Delete a mod directory

    :mod_dir: (str) Path to the mod directory to be deleted.
    :raises: (ValueError)
    """
    if not os.path.exists(mod_dir):
        raise ValueError("'%s' does not exist." % mod_dir)
    if not os.path.isdir(mod_dir):
        raise ValueError("'%s' is not a directory." % mod_dir)

    shutil.rmtree(mod_dir)


# TODO: Deal with plugins who's mods have been uninstalled.
def get_plugins(cfg):
    """Get all plugins enabled and disabled plugins.
    Note: this wont return orphaned plugins since they can't have a plugin object.

    :cfg: (ConfigFile) openmw.cfg object.
    :returns: (list) list of all plugin objects referenced in openmw.cfg.
    """
    mods = cfg.get_mods()
    plugins = []
    for mod in mods:
        if not mod.get_plugins():
            continue

        for plugin in mod.get_plugins():
            plugins.append(plugin)

    return plugins


def get_enabled_plugins(cfg):
    """Get a list of enabled plugins sorted by load order.

    :cfg: (ConfigFile) openmw.cfg object.
    :returns: (list) List of enabled plugin objects sorted by load order.
    """
    plugins = []
    for plugin in get_plugins(cfg):
        if plugin.is_enabled():
            plugins.append(plugin)

    return sorted(plugins, key=lambda plugin: plugin.get_order())


def get_disabled_plugins(cfg):
    """Get a list of plugins that are installed but not enabled.

    :cfg: (ConfigFile) openmw.cfg object.
    :returns: (list) List of disabled plugin objects
    """
    plugins = []
    for plugin in get_plugins(cfg):
        if not plugin.is_enabled():
            plugins.append(plugin)

    return plugins


def get_orphaned_plugins(cfg):
    """Get a list of plugins that have entries in openmw.cfg but have no parent mod.

    :cfg: (ConfigFile) openmw.cfg object
    :returns: (list)
    """

    installed_plugins = [p.get_name() for p in get_plugins(cfg)]
    plugins = [e.get_value() for e in cfg.find_key("content")]
    orphaned = []

    for plugin in plugins:
        if plugin not in installed_plugins:
            orphaned.append(plugin)

    return orphaned


def find_plugin(cfg, plugin_name):
    """Find an installed plugin by name

    :plugin_name: (str) Plugin name
    :returns: (OmwPlugin or None)
    """
    mods = cfg.get_mods()
    for mod in mods:
        plugins = mod.get_plugins()
        if not plugins:
            continue
        for plugin in plugins:
            if plugin.get_name() == plugin_name:
                return plugin

    return None


def merge_levlists(plugins, output):
    """Merge a leveled lists for a list of plugins

    :cfg: (ConfigFile) openmw.cfg object
    :plugins: (list) List of Esm objects
    :output: (str) Path to output file
    """

    levc = []  # Creature lists
    levi = []  # Item lists

    # Merge all records
    for esm in plugins:
        esm.read()
        levc += esm.find_records("LEVC")
        levi += esm.find_records("LEVL")

    # And dump into a file
    mash = Esm(os.path.join(get_base_dir, "./empty.esp"))
    mash.read()
    mash.records += levi + levc
    mash.write(output)


def get_base_dir():
    """Return the path of the base directory where the script is located.
    This should be the directory where lib exists.

    :return: (str) Path
    """
    # os.path.realpath to resolve symlinks
    return os.path.realpath(sys.path[0])
