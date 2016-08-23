# Core functions used in both CLI and GUI
import os
import shutil
from config import config


# TODO: Expand "mod dir" definition so it supports pluginless directories
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
    return os.path.abspath(os.path.expanduser(path))


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


def get_installed_mod(mod):
    """Get the path of an installed mod from either a relative path or just the directory name.

    :mod: (str) Directory where the installed mod resides, either a path or just the name.
    :returns: (str) Absolute path to the installed mod.
    :raises: (ValueError) if the mod does not exist in the configured mod directory.

    """
    mods_dir = get_full_path(config.get("General", "mods_dir"))
    # Relative path
    if os.path.sep in mod:
        mod_dir = get_full_path(mod)
    # Directory name
    else:
        mod_dir = get_full_path(os.path.join(mods_dir, mod))

    if os.path.exists(mod_dir) and os.path.dirname(mod_dir) == mods_dir:
        return mod_dir
    else:
        raise ValueError('Could not find directory "%s" inside the mods directory' % mod)
