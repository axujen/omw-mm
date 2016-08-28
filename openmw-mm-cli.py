#!/usr/bin/env python2.7
import os
from argparse import ArgumentParser
from lib.omwconfig import ConfigFile, ConfigEntry
from lib.omwmod import OmwMod
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

    if mods_dir:
        entries = ConfigFile()
        mods_dir = core.get_full_path(mods_dir)
        for entry in omw_cfg.find_key("data"):
            if os.path.dirname(entry.get_value()) == mods_dir:
                entries.append(entry)

    else:
        entries = omw_cfg.find_key("data")

    mods = [OmwMod(entry.get_value()) for entry in entries]

    if path:
        for mod in mods:
            print(mod.get_path())
    else:
        for mod in mods:
            print(mod.get_name())


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


def uninstall_mod(omw_cfg, mod, clean=False, rm=False):
    """Uninstall a mod by removing its entry from openmw.cfg

    :omw_cfg: (str) Path to openmw.cfg.
    :mod: (str) Name or path of the directory containing the mod.
    :clean: (bool) If true then disable plugins that belong to the mod before uninstalling.
    :rm: (bool) If true then delete the mod directory. Default: False
    """

    # Path given
    if os.path.sep in mod:
        mod_path = core.get_full_path(mod)
    # Only a name was given
    else:
        mod_path = os.path.join(config.get("General", "mods_dir"), mod)

    if not os.path.exists(mod_path):
        print("No such file or directory %s. Try the clean command if the mod is already deleted" % mod)
        raise SystemExit(1)

    omw_cfg = ConfigFile(core.get_full_path(omw_cfg))
    mod_obj = OmwMod(mod_path)
    entry = core.get_mod_entry(mod_obj, omw_cfg)

    if not entry:
        print("Could not find a reference to %s in openmw.cfg" % mod)
        raise SystemExit(0)


    if clean and mod_obj.get_plugins():
        for plugin in mod_obj.get_plugins():
            if plugin in core.get_enabled_plugins(omw_cfg):
                e = ConfigEntry("content", plugin, omw_cfg)
                print("Disabling %s" % plugin)
                core.disable_plugin(omw_cfg, e)

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
        entry = ConfigEntry("data", new_dir)
        print("Adding entry %s to openmw.cfg" % entry)
        core.insert_data_entry(entry, omw_cfg)
        omw_cfg.write()
    else:
        print('Directory %s is not a mod directory! Use -f to force.' % src)
        raise SystemExit(1)


def list_plugins(omw_cfg, tree=False):
    """List detected openmw plugins.

    :omw_cfg: (str) Path to openmw.cfg.
    :tree: (bool) If True show parent mods in a tree.
    """

    omw_cfg = ConfigFile(core.get_full_path(omw_cfg))
    mods = [OmwMod(e.get_value(), e) for e in omw_cfg.find_key("data")]

    if tree:
        printed = []
        for mod in mods:
            plugins = mod.get_plugins()
            if not plugins:  # Skip pluginless mods
                continue
            else:
                print("%s:" % mod.get_name())
                for plugin in plugins:
                    if mod.plugin_is_enabled(plugin):
                        prefix = "+"
                    else:
                        prefix = "-"

                    printed.append(plugin)
                    print("\t%s %s" % (prefix, plugin))
        # Print modless plugins
        modless = True
        for plugin in core.get_enabled_plugins(omw_cfg):
            if plugin not in printed:
                if modless:
                    print("Orphaned Plugins (They don't belong to any mod listed in openmw.cfg):")
                    modless = False
                print("\t+ %s" % plugin)
    else:
        enabled_plugins = core.get_enabled_plugins(omw_cfg)
        disabled_plugins = core.get_disabled_plugins(omw_cfg)

        if enabled_plugins:
            i = 1
            for plugin in enabled_plugins:
                print("(%d) %s" % (i, plugin))
                i += 1
        if disabled_plugins:
            for plugin in disabled_plugins:
                print("- %s" % plugin)


def enable_plugin(omw_cfg, plugin):
    """Enable a plugin by name.

    :omw_cfg: (ConfigFile) openmw.cfg object.
    :plugin: (str) Full plugin name.
    """

    omw_cfg = ConfigFile(core.get_full_path(omw_cfg))

    if plugin in core.get_enabled_plugins(omw_cfg):
        print("Plugin %s is already enabled!" % plugin)
        raise SystemExit(1)

    if plugin not in core.get_disabled_plugins(omw_cfg):
        print("Could not find plugin %s in any of the currently installed mods" % plugin)
        raise SystemExit(1)

    entry = ConfigEntry("content", plugin, omw_cfg)

    print("Enabling %s" % plugin)
    core.enable_plugin(omw_cfg, entry)
    omw_cfg.write()


def disable_plugin(omw_cfg, plugin):
    """Disable a currently installed plugin by name.

    :omw_cfg: (ConfigFile) openwm.cfg object.
    :plugin: (str) Name of the plugin to be disabled.
    """

    omw_cfg = ConfigFile(core.get_full_path(omw_cfg))

    if plugin not in core.get_plugins(omw_cfg):
        print("There is no such plugin %s" % plugin)
        raise SystemExit(0)
    if plugin in core.get_disabled_plugins(omw_cfg):
        print("Plugin %s is already disabled" % plugin)
        raise SystemExit(0)

    print("Disabling %s" % plugin)
    entry = ConfigEntry("content", plugin, omw_cfg)
    core.disable_plugin(omw_cfg, entry)

    omw_cfg.write()


def merge_lists(omw_cfg, out=None):
    """Merge leveled lists for every enabled plugin.

    :omw_cfw: (str) Path to openmw.cfg
    :out: (str) Path to output file. Default: ./merged.esp
    """

    if not out:
        out = "./merged.esp"

    cfg = ConfigFile(omw_cfg)
    mods = [OmwMod(e.get_value(), e) for e in cfg.find_key("data")]
    plugins_esm = []
    blacklist = config.get("General", "never_merge").split(",")
    print(blacklist)
    for mod in mods:
        plugins = mod.get_plugins()
        if plugins:
            for plugin in plugins:
                if plugin not in blacklist and mod.plugin_is_enabled(plugin):
                    print("Merging: %s" % plugin)
                    plugins_esm.append(Esm(os.path.join(mod.get_path(), plugin)))

    core.merge_levlists(plugins_esm, out)


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
            help="Destination of the merged esp. Default: ./merged.esp")

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
        uninstall_mod(args.cfg, args.mod, args.clean, args.rm)

    if args.command == "list-plugins":
        list_plugins(args.cfg, args.tree)

    if args.command == "enable":
        enable_plugin(args.cfg, args.plugin)

    if args.command == "disable":
        disable_plugin(args.cfg, args.plugin)

    if args.command == "merge":
        merge_lists(args.cfg, args.out)
