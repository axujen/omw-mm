# Core functions used in both CLI and GUI
import os
import shutil


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


def get_latest_key_index(key, cfg):
    """Get the index of the last :key: entry in openmw.cfg.

    :key: (str) Name of the key that needs to be indexed
    :cfg: (ConfigFile) openmw.cfg object.
    :returns: (int)
    """
    i = 0
    index = None
    for entry in cfg:
        if entry.get_key() == key:
            index = i
        i += 1

    return index


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


def insert_data_entry(entry, cfg):
    """Insert a data entry into openmw.cfg.

    :entry: (ConfigEntry) openmw.cfg entry object.
    :cfg: (ConfigFile) openmw.cfg config object.
    :returns: (int) Index of the new appended entry.
    """
    index = get_latest_key_index("data", cfg) + 1
    cfg.insert(index, entry)

    return index


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


def get_mod_entry(mod, cfg):
    """Try to find a mods config entry in openmw.cfg

    :mod: (OmwMod) Mod object.
    :cfg: (ConfigFile) openmw.cfg object.
    :returns: (ConfigEntry or None) Config entry referencing the mod. Or None if no entry could be found
    """

    output = None
    entries = cfg.find_key("data")

    for entry in entries:
        if mod.get_path() == entry.get_value():
            output = entry

    return output


def get_plugins(modlist):
    """Get all plugins from a set of mods

    :modlist: (list) List of OmwMod object.
    :returns: (list) List of all plugins contained in these mods.
    """
    plugins = []
    for mod in modlist:
        if not mod.get_plugins():
            continue

        for plugin in mod.get_plugins():
            plugins.append(plugin)

    return plugins


def get_enabled_plugins(cfg):
    """Get a list of enabled plugins sorted by load order.

    :cfg: (ConfigFile) openmw.cfg object.
    :returns: (list) List of enabled plugins sorted by load order.
    """
    entries = cfg.find_key("content")
    return [e.get_value() for e in entries]


def get_disabled_plugins(cfg, modlist):
    """Get a list of plugins that are installed by not enabled.

    :cfg: (ConfigFile) openmw.cfg object.
    :modlist: (List) List containig OmwMod objects.
    :returns: (list)
    """
    enabled_plugins = get_enabled_plugins(cfg)
    plugins = get_plugins(modlist)
    disabled_plugins = []

    for plugin in plugins:
        if plugin not in enabled_plugins:
            disabled_plugins.append(plugin)

    return disabled_plugins


def enable_plugin(cfg, modlist, entry):
    """Enable a plugin by creating a new entry for it in openmw.cfg

    :cfg: (ConfigFile) openmw.cfg object.
    :modlist: (list) List of currently installed mods
    :entry: (ConfigEntry) config entry for the plugin.
    :raises: (ValueError)
    """
    plugin = entry.get_value()
    if plugin not in get_plugins(modlist):
        raise ValueError("No such plugin %s" % plugin)

    if plugin in get_enabled_plugins(cfg):
        raise ValueError("Plugin %s is already enabled" % plugin)

    # Append the new entry behind the latest content entry to keep things clean.
    index = get_latest_key_index("content", cfg)
    cfg.insert(index + 1, entry)


def disable_plugin(cfg, modlist, entry):
    """Disable a plugin from openmw.cfg

    :cfg:  (ConfigFile) openmw.cfg object.
    :modlist: (list) List of currently installed mods.
    :entry:  (ConfigEntry) Plugins config entry.
    :raises: (ValueError)
    """

    plugin = entry.get_value()
    if plugin not in get_enabled_plugins(cfg):
        raise ValueError("Plugin %s is already disabled" % plugin)

    cfg.remove(entry)
