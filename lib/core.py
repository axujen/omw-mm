#!/usr/bin/env python2
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
    for file in os.listdir(dir):
        if os.path.isdir(file):
            continue
        for ext in config["General"]["mod_extensions"]:
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


def get_latest_index(key, cfg):
    """Get the index of the last :key: entry in openmw.cfg.

    :key: (str) Name of the key that needs to be indexed
    :cfg: (ConfigFile) openmw.cfg object.
    :returns: (int)
    """
    i = 0
    index = None
    for entry in cfg:
        if entry.key == key:
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
    index = get_latest_index("data", cfg) + 1
    cfg.insert(index, entry)

    return index
