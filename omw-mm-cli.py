#!/usr/bin/env python2.7
# -*- coding: UTF-8 -*-
import os
from argparse import ArgumentParser

from lib.omw import ConfigFile, OmwMod
from lib.esm import Esm
from lib.config import config
from lib import core


def list_mods(omw_cfg, mods_dir=None, path=False):
    """List all mod directories listed in openmw.cfg.

    :omw_cfg: (ConfigFile) openmw.cfg object.
    :mods_dir: (str) Optional, only mods in this directory are listed. Default: None
    :path:    (bool) if True print full path instead of basename. Default: False
    """

    omw_cfg = ConfigFile(core.get_full_path(omw_cfg))
    mods = omw_cfg.mods

    if mods_dir:
        mods_dir = core.get_full_path(mods_dir)
        mods = [m for m in mods if os.path.dirname(m.path) == mods_dir]

    if path:
        for mod in mods:
            print(mod.path)
    else:
        for mod in mods:
            print(mod.name)


def clean_mods(omw_cfg):
    """Remove invalid data and content entries from openmw.cfg

    :omw_cfg: (str) Path to openmw.cfg.
    """
    omw_cfg = ConfigFile(core.get_full_path(omw_cfg))

    # Remove invalid data entries
    bad_mods = []
    for mod in omw_cfg.mods:
        if not os.path.exists(mod.path):
            print("Removing non-existing mod entry for %s" % mod.path)
            mod.disable()
            bad_mods.append(mod)

    if not bad_mods:
        print("No invalid data entries found!")

    # Remove Invalid content entries (Perhaps this should have a user switch?)
    bad_plugins = core.get_plugins_orphaned(omw_cfg)
    if bad_plugins:
        for plugin in bad_plugins:
            print("Removing non-existing plugin entry for %s" % plugin.name)
            plugin.disable()
    else:
        print("No invalid content entries found!")

    if bad_mods or bad_plugins:
        omw_cfg.write()


# TODO: Autoclean and Autodelete options in the config
def uninstall_mod(omw_cfg, mod_name, clean=False, rm=False):
    """Uninstall a mod by removing it from openmw.cfg

    :omw_cfg: (str) Path to openmw.cfg.
    :mod_name: (str) Name or path of the directory containing the mod.
    :clean: (bool) If true then disable plugins that belong to the mod before uninstalling.
    :rm: (bool) If true then delete the mod directory. Default: False
    """

    # Path given
    if os.path.sep in mod_name:
        mod_path = core.get_full_path(mod_name)
    # Only a name was given
    else:
        mod_path = os.path.join(config.get("General", "mods_dir"), mod_name)

    if not os.path.exists(mod_path):
        print("No such file or directory %s. Try the clean command if the mod is already deleted" % mod_name)
        raise SystemExit(1)

    omw_cfg = ConfigFile(core.get_full_path(omw_cfg))

    for mod in omw_cfg.mods:
        if mod.path == mod_path:
            mod = mod
            break
    else:
        print("Could not find any reference to %s, are you sure its installed?" % mod_name)
        raise SystemExit(1)

    if clean:
        for plugin in mod.plugins_enabled:
            plugin.disable()

    print("Disabling %s" % mod.name)
    mod.disable()
    omw_cfg.write()

    if rm:
        print("Deleting mod in %s" % mod.path)
        core.rm_mod_dir(mod.path)


# TODO: Better handling of already installed mods
# TODO: install mod as name command
def install_mod(omw_cfg, src, dest, force=False):
    """Install a mod in openmw.cfg."

    :omw_cfg: (str) Path to openmw.cfg.
    :src: (str) Path to mod.
    :dest: (str) Path to destination mod directory.
    :force: (bool) Force installation. Default: False.
    """
    omw_cfg = ConfigFile(core.get_full_path(omw_cfg))
    src = core.get_full_path(src)
    dest = core.get_full_path(dest)
    mod_source = core.get_modsource(src)
    name = mod_source.name

    if not mod_source.is_mod and not force:
        print("%s is not detected as a mod,\
              if you wish to install it anyway use the --force flag" % name)
        raise SystemExit(1)

    # Copy the mod
    new_dir = mod_source.install(dest)
    print("Copying %s to %s" % (name, new_dir))

    # Enable
    mod = OmwMod(new_dir, omw_cfg)
    print("Enabling %s" % (mod.name))
    mod.enable()
    omw_cfg.write()


def list_plugins(omw_cfg, tree=False):
    """List detected openmw plugins.

    :omw_cfg: (str) Path to openmw.cfg.
    :tree: (bool) If True show parent mods in a tree.
    """

    omw_cfg = ConfigFile(core.get_full_path(omw_cfg))

    if tree:  # Tree View
        for mod in omw_cfg.mods:
            p_enabled, p_disabled = mod.plugins_enabled, mod.plugins_disabled
            if p_enabled or p_disabled:
                print("%s:" % mod.name)
                for plugin in p_enabled:
                    print("\t(%d) %s" % (plugin.order, plugin.name))
                for plugin in p_disabled:
                    print("\t- %s" % plugin.name)

    else:  # List View
        for plugin in core.get_plugins_enabled(omw_cfg):
            print("(%d) %s" % (plugin.order, plugin.name))
        for plugin in core.get_plugins_disabled(omw_cfg):
            print("- " + plugin.name)

    # Print orphaned plugins
    orphaned = core.get_plugins_orphaned(omw_cfg)
    if orphaned:
        print("\nThe following plugins don't belong to any currently installed mod. Use the clean command to remove them.")
        for plugin in orphaned:
            print(plugin.name)


def enable_plugin(omw_cfg, plugin_name):
    """Enable a plugin by name.

    :omw_cfg: (ConfigFile) openmw.cfg object
    :plugin_name: (str) Plugin name
    """

    omw_cfg = ConfigFile(core.get_full_path(omw_cfg))
    plugin = core.find_plugin(omw_cfg, plugin_name)
    if not plugin:
        print("Could not find plugin %s." % plugin_name)
        raise SystemExit(1)

    if plugin.is_enabled:
        print("Plugin %s is already enabled." % plugin_name)
        raise SystemExit(1)

    print("Enabling %s." % plugin_name)
    plugin.enable()
    omw_cfg.write()


# TODO: Improve this function to be able to handle disabling plugins by index
def disable_plugin(omw_cfg, plugin_name):
    """Disable a currently installed plugin by name.

    :omw_cfg: (ConfigFile) openwm.cfg object.
    :plugin_name: (str) Name of the plugin to be disabled.
    """

    omw_cfg = ConfigFile(core.get_full_path(omw_cfg))
    plugin = core.find_plugin(omw_cfg, plugin_name)

    if not plugin:
        print("Could not find plugin %s." % plugin_name)
        raise SystemExit(1)

    if not plugin.is_enabled:
        print("Plugin %s is already disabled." % plugin_name)
        raise SystemExit(1)

    print("Disabling %s" % plugin_name)
    plugin.disable()
    omw_cfg.write()


def merge_lists(omw_cfg, out=None):
    """Merge leveled lists for every enabled plugin.

    :omw_cfg: (str) Path to openmw.cfg
    :out: (str) Path to output file. Default: ./merged.esp
    """

    cfg = ConfigFile(omw_cfg)
    mods = cfg.mods
    if not mods:
        print("Nothing to merge!")
        raise SystemExit(1)

    blacklist = config.get("General", "never_merge").split(",")
    merged = Esm(os.path.join(core.get_base_dir(), "./Merged.esp"))
    merged.unpack()

    for mod in mods:
        plugins = mod.plugins
        if plugins:
            for plugin in plugins:
                if plugin.name not in blacklist and plugin.is_enabled:
                    print("Merging: %s" % plugin.name)
                    to_merge = Esm(plugin.path)
                    to_merge.unpack()
                    diff = merged.merge_with(to_merge)

                    # Pretty Print stuff
                    for rec in ("LEVC", "LEVI"):
                        if diff[rec]["Merged"]:
                            print("\t%s records merged:" % rec)
                            for record in diff[rec]["Merged"]:
                                print("\t\t%s" % record)

    merged.post_merge()

    if not out:
        out = "./Merged_Lists.esp"
    merged.write(out)


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

    # Install command.
    parser_i = subparser.add_parser("install", help="Install a mod")
    parser_i.add_argument("src", metavar="path",
            help="Path to the archive/directory to be installed")
    parser_i.add_argument("dest", metavar="destination", nargs="?", default=mods_dir,
            help="Destination mods directory")
    parser_i.add_argument("-f", "--force", action="store_true", dest="force", default=False,
            help="Don't check if the archive/directory is an actual mod")

    # Uninstall command
    parser_u = subparser.add_parser("uninstall", help="Uninstall a mod directory")
    parser_u.add_argument("mod", metavar="mod_directory",
            help="Either the name of the mod or a path to the mod directory.\
                    \n(NOTE: If only a name is given then only the configured mods_dir is checked)")
    parser_u.add_argument("-d", "--delete", action="store_true", dest="rm",
            help="Delete the directory (USE AT YOUR OWN RISK!)")
    parser_u.add_argument("-c", "--clean", action="store_true", dest="clean",
            help="Disable plugins for this mod before uninstalling")

    # Enable command
    parser_ep = subparser.add_parser("enable", help="Enable a plugin")
    parser_ep.add_argument("plugin", help="Full name of the plugin eg: Morrowind.esm")

    # Disable command
    parser_dp = subparser.add_parser("disable", help="disable a plugin")
    parser_dp.add_argument("plugin", help="Full name of the plugin eg: Morrowind.esm")

    # List command
    parser_l = subparser.add_parser('list', help="List installed mods")
    parser_l.add_argument("dir", metavar="directory", nargs="?", default=None,
            help="List only mods that exist in directory")
    parser_l.add_argument("-s", "--showpath", action="store_true", dest="path", default=False,
            help="Show paths instead of just names")

    # List plugins
    parser_lp = subparser.add_parser("list-plugins", help="List plugins")
    parser_lp.add_argument("-t", "--tree", action="store_true", dest="tree",
            default=False, help="List plugins in a tree view, showing their parent mods.")

    # Clean command
    subparser.add_parser('clean', help="Clean non existing mod dirs from openmw.cfg")

    # Merge command
    subparser_m = subparser.add_parser("merge", help="Merge all leveled lists into one file")
    subparser_m.add_argument("-o", "--output", metavar="output", default=None, dest="out",
            help="Destination of the merged esp. Default: ./Merged_Lists.esp")

    return parser

if __name__ == "__main__":
    args = create_arg_parser(prog="omw-mm-cli").parse_args()

    if args.command == "list":
        list_mods(args.cfg, args.dir, args.path)

    if args.command == "clean":
        clean_mods(args.cfg)

    if args.command == "install":
        install_mod(args.cfg, args.src, args.dest, args.force)

    if args.command == "uninstall":
        uninstall_mod(args.cfg, args.mod, args.clean, args.rm)

    if args.command == "list-plugins":
        list_plugins(args.cfg, args.tree)

    if args.command == "enable":
        enable_plugin(args.cfg, args.plugin)

    if args.command == "disable":
        disable_plugin(args.cfg, args.plugin)

    if args.command == "merge":
        merge_lists(args.cfg, args.out)
