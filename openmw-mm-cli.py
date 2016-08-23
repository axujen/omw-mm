#!/usr/bin/env python2.7
# TODO: This script needs to have the following functions
#       x Install mods
#       x List installed mods
#       x Uninstall mods (optionally deleting the files)
#       x Clean entries that reference non-existing mod directories
#       - Enable/Disable plugins
#       x Command-line argument parsing.

import os
from argparse import ArgumentParser
from lib.omwconfig import ConfigFile, ConfigEntry
from lib.config import config
from lib import core


def list_mods(omw_cfg, mods_dir=None, path=False):
    """List all mod directories listed in openmw.cfg.

    :omw_cfg: (ConfigFile) openmw.cfg object.
    :mods_dir: (str) Optional, only mods in this directory are listed. Default: None
    :path:    (bool) if True print full path instead of basename. Default: False
    :returns: (ConfigFile) List of ConfigEntry objects refering to the listed mods.
    """

    omw_cfg = ConfigFile(core.get_full_path(omw_cfg))

    if mods_dir:
        entries = ConfigFile()
        mods_dir = core.get_full_path(mods_dir)
        for entry in omw_cfg.find_key("data"):
            if os.path.dirname(entry.get_value()) == mods_dir:
                entries.append(entry)

    else:
        entries = omw_cfg.find_key("data")

    if not path:
        mods = [os.path.basename(mod.get_value()) for mod in entries]
    else:
        mods = [mod.get_value() for mod in entries]

    for mod in mods:
        print(mod)

    return entries


def clean_mods(omw_cfg):
    """Remove data entries that reference non-existing directories from openmw.cfg

    :omw_cfg: (str) Path to openmw.cfg.
    :returns: (list) List of remove ConfigEntry objects.
    """
    omw_cfg = ConfigFile(core.get_full_path(omw_cfg))

    bad_entries = []
    for entry in omw_cfg.find_key("data"):
        if not os.path.exists(entry.get_value()):
            print("Removing entry %s from openmw.cfg." % entry)
            bad_entries.append(entry)
            omw_cfg.remove(entry)

    if bad_entries:
        omw_cfg.write()
    else:
        print("No invalid entries found.")

    return bad_entries


def uninstall_mod(omw_cfg, mod, rm=False):
    """Uninstall a mod by removing its entry from openmw.cfg

    :omw_cfg: (str) Path to openmw.cfg.
    :mod: (str) Name or path of the directory containing the mod.
    :rm: (bool) If true then delete the mod directory. Default: False
    """

    omw_cfg = ConfigFile(core.get_full_path(omw_cfg))

    # TODO: This should be redone, get_installed_mod only checks files
    # in the preconfigured mods_dir, and does not even bother to check openmw.cfg
    entry = core.get_mod_entry(mod, omw_cfg)

    if not entry:
        print("Could not find a reference to %s in openmw.cfg" % mod)
        raise SystemExit(0)

    print("Removing entry %s from openmw.cfg" % entry)
    omw_cfg.remove(entry)
    omw_cfg.write()
    if rm:
        print("Deleting mod in %s" % entry.get_value())
        core.rm_mod_dir(entry.get_value())


def install_mod(omw_cfg, src, dest, force=False):
    """Install a mod directory and add appropriate openmw.cfg entry.

    :omw_cfg: (str) Path to openmw.cfg.
    :src: (str) Path to mod directory.
    :dest: (str) Path to destination mod directory.
    :force: (bool) Force install of mod dir. Default: False.
    """
    omw_cfg = ConfigFile(core.get_full_path(omw_cfg))
    src_dir = core.get_full_path(src)
    dest_dir = core.get_full_path(dest)

    if not os.path.isdir(src_dir):
        print('%s is not a directory.' % src)
        raise SystemExit(1)

    if core.is_mod_dir(src_dir) or force:
        if os.path.exists(os.path.join(dest_dir, os.path.basename(src))):
            print("A file %s already exists in %s. Try renaming the mod or supplying a different destination."
                  % (os.path.basename(src), dest_dir))
            raise SystemExit(0)

        # Copy the mod
        print("Copying %s to %s" % (src_dir, dest_dir))
        new_dir = core.copy_to_mod_dir(src_dir, dest_dir)

        # Add an entry
        entry = ConfigEntry("data", '"%s"' % new_dir)  # data entries have to be quoted
        print("Adding entry %s to openmw.cfg" % entry)
        core.insert_data_entry(entry, omw_cfg)
        omw_cfg.write()
    else:
        print('Directory %s is not a mod directory! Use -f to force.' % src)
        raise SystemExit(1)


def list_plugins(omw_cfg, enabled=False, disabled=False):
    """List detected openmw plugins.

    :omw_cfg: (str) Path to openmw.cfg.
    :enabled: (bool) Only list enabled plugins. Default: False
    :disabled: (bool) Only list disabled plugins. Default: False
    :returns: TODO
    """

    omw_cfg = ConfigFile(core.get_full_path(omw_cfg))
    entries = omw_cfg.find_key("data")
    plugin_extensions = [".esm", ".esp", ".omwaddon"]
    plugins = []

    for entry in entries:
        mod_dir = entry.get_value()
        for file in os.listdir(mod_dir):
            # Skip directories
            if not os.path.isfile(os.path.join(mod_dir, file)):
                    continue

            for ext in plugin_extensions:
                if file.endswith(ext):
                    plugins.append(file)

    if enabled and not disabled:
        plugins = [entry.get_value() for entry in omw_cfg.find_key("content")]

    if disabled and not enabled:
        enabled_plugins = [entry.get_value() for entry in omw_cfg.find_key("content")]
        plugins = [plugin for plugin in plugins if plugin not in enabled_plugins]

    if plugins:
        for plugin in plugins:
            print(plugin)
    else:
        print("No plugin files were found")

    return plugins


def create_arg_parser(*args, **kwargs):
    """Create the argument parser.

    :returns: (ArgumentParser)
    """
    parser = ArgumentParser(*args, **kwargs)
    subparser = parser.add_subparsers(title="Commands", dest="command", metavar="<command>")

    # Defaults
    mods_dir = config.get("General", "mods_dir")   # Destination directory to install mods
    omw_cfg = config.get("General", "openmw_cfg")  # Openmw config object

    # General arguments
    parser.add_argument("-f", "--file", dest="cfg", metavar="file", default=omw_cfg,
            help="Path to openmw.cfg")

    # List command
    parser_l = subparser.add_parser('list', help="List installed mods")
    parser_l.add_argument("dir", metavar="directory", nargs="?", default=None,
            help="List only mods that exist in directory")
    parser_l.add_argument("-s", "--showpath", action="store_true", dest="path", default=False,
            help="Show paths instead of just names")

    # List plugins
    parser_lp = subparser.add_parser("list-plugins", help="List plugins")
    parser_lp.add_argument("-e" "--enabled", action="store_true", dest="enabled",
            default=False, help="Only show installed plugins")
    parser_lp.add_argument("-d", "--disabled", action="store_true", dest="disabled",
            default=False, help="Only show disabled plugins")

    # Clean command
    subparser.add_parser('clean', help="Clean non existing mod dirs from openmw.cfg")

    # Install command.
    parser_i = subparser.add_parser("install", help="Install a directory as mod")
    parser_i.add_argument("src", metavar="directory",
            help="Path to the directory to be installed")
    parser_i.add_argument("dest", metavar="destination", nargs="?", default=mods_dir,
            help="Destination directory")
    parser_i.add_argument("-f", "--force", action="store_true", dest="force", default=False,
            help="Don't check if the directory is an actual mod directory")

    # Uninstall command
    parser_u = subparser.add_parser("uninstall", help="Uninstall a mod directory")
    parser_u.add_argument("mod", metavar="mod_directory",
            help="Either the name of the mod or a path to the mod directory.\
                    \n(NOTE: If only a name is given then only the configured mods_dir is checked)")
    parser_u.add_argument("-d", "--delete", action="store_true", dest="rm",
            help="Delete the directory (USE AT YOUR OWN RISK!)")

    return parser

if __name__ == "__main__":
    args = create_arg_parser(prog="openmw-mm-cli").parse_args()

    if args.command == "list":
        list_mods(args.cfg, args.dir, args.path)

    if args.command == "clean":
        clean_mods(args.cfg)

    if args.command == "install":
        install_mod(args.cfg, args.src, args.dest, args.force)

    if args.command == "uninstall":
        uninstall_mod(args.cfg, args.mod, args.rm)

    if args.command == "list-plugins":
        list_plugins(args.cfg, args.enabled, args.disabled)
