# -*- coding: UTF-8 -*-
# Classes that represent openmw config files and mods/plugins
import os


# -- Config file --
class ConfigFile(object):
    def __init__(self, path=None):
        """OpenMW config file openmw.cfg.

        :path: (str): Path to openmw.cfg, Default: None
        """
        self._entries = []
        self._mods = []
        self._plugins = []
        self._plugins_orphaned = []

        if path:
            self._path = path
            self.load()

    @property
    def path(self):
        return self._path

    @property
    def entries(self):
        """Get the list of entries in the config file

        :returns: (list)
        """
        return self._entries

    @property
    def mods(self):
        """Get the list of installed mods

        :returns: (list)
        """
        return self._mods

    @property
    def plugins(self):
        return self._plugins

    @plugins.setter
    def plugins(self, plugins):
        self._plugins = plugins

    @property
    def plugins_orphaned(self):
        return [p for p in self.plugins if p.is_orphan]

    def load(self):
        """Load the openmw.cfg file into the instance."""
        enabled_plugins = []
        with open(self.path, "r") as fh:
            for line in fh.readlines():
                if line.isspace():  # Blank line.
                    entry = ConfigRawEntry(line, "BLANK", config=self)
                elif line.strip().startswith("#"):  # Comment
                    entry = ConfigRawEntry(line, "COMMENT", config=self)
                else:  # Normal entry
                    entry = ConfigEntry(line, config=self)

                    # -- Seperate mods and plugins from self.entries
                    if entry.key == "data":  # Mod
                        self.mods.append(OmwMod(entry.value, self))
                        continue
                    elif entry.key == "content":  # plugins list is populated later
                        enabled_plugins.append(entry.value)
                        continue

                self.entries.append(entry)

        # Populate plugins list
        self._load_plugins(enabled_plugins)

    def _load_plugins(self, plist):
        enabled = []
        for mod in self.mods:
            for plugin in mod.plugins:
                if plugin.name in plist:
                    plugin.enable()
                    enabled.append(plugin.name)

        orphans = tuple(p for p in plist if p not in enabled)
        for pname in orphans:
            plugin = OmwPlugin(pname, self)
            plugin.enable()

        self.plugins.sort(key=lambda p: plist.index(p.name))

    def write(self, path=None):
        """Save the config file to a location on disk.

        :path: (str) Path to save to. Default: original path
        """
        if not path:
            path = self.path

        out = "\n".join((str(e) for e in self.entries)).rstrip("\n")
        for mod in self.mods:
            out = out + '\ndata="%s"' % mod.path
        for plugin in self.plugins:
            out = out + '\ncontent=%s' % plugin.name

        with open(path, "w") as handle:
            handle.write(out)


# TODO: Simplify the following two classes since they will no longer be used
# to manage mods
class ConfigEntry(object):
    """OpenMW config entry.

    If value is ommitted then key is parsed as a raw line (key=value).

    :key:   (str) Line from openmw.cfg as is.
    :value: (str) Value of key, Default: None.
    :config: (ConfigFile) Config object where this entry resides. Default: None
    """

    def __init__(self, key, value=None, config=None):
        if not value:  # Value was not given so assuming key is a raw line
            key, value, comment = self.unpack_line(key)
        else:
            comment = None

        self._config = config
        self._key, self._value = self.process_key_value(key, value)
        self._comment = comment

    def __str__(self):
        if self._comment:
            return "=".join((self._key, self._value)) + " " + self._comment
        else:
            return "=".join((self._key, self._value))

    def __eq__(self, other):
        """Compare entries by key and value"""
        if isinstance(other, ConfigRawEntry):
            return False

        key_match = self.key == other.key
        value_match = self.value == other.value
        return key_match and value_match

    def unpack_line(self, line):
        """Parse openmw.cfg line entry

        :line: (str): Raw line from openmw.cfg
        :returns: (set) key, value, type
        """
        key, value = (i.strip() for i in line.split("="))
        if "#" in value:
            value, comment = value.split("#")
            value = value.strip()
            comment = "#" + comment
        else:
            comment = None

        if "#" in key:
            raise ValueError("ConfigEntry key cannot contain a comment, got %s" % line)
        if value.isspace():
            raise ValueError("ConfigEntry value cannot be empty, got %s" % line)

        return (key, value, comment)

    def process_key_value(self, key, value):
        """Process a key, value pair and return normalized entries.

        :key: (str)
        :value: (str)
        :returns: (set)
        """
        # Automatically add quotes for data entries
        if key == "data":
            if not value[0] == value[-1] == '"':  # is the value quoted?
                # then quote it for internal storage.
                value = '"%s"' % value

        return (key, value)

    @property
    def key(self):
        """Return the entry key.

        :raw: (bool) if True return self._key directly without processing
        :returns: (str)
        """
        return self._key

    @property
    def value(self, raw=False):
        """Return the entry value.

        :raw: (bool) if True return self._value directly without processing
        :returns: (str)
        """
        if self.key == "data" and not raw:
            return self._value.strip('"')

        return self._value

    @property
    def config(self):
        return self._config

    @config.setter
    def config(self, config):
        """Set the ConfigFile object this entry belongs to.

        :config: (ConfigFile or None)
        """
        if config is not None and not isinstance(config, ConfigFile):
            raise ValueError("config must be a ConfigFile object. got %s" % config)
        self._config = config


# TODO Proper inheritence between ConfigEntr and ConfigRawEntry
class ConfigRawEntry(object):
    """Raw openmw.cfg entry, used for storing comments and blank lines"""
    def __init__(self, line, etype, config):
        """"
        :line: (str) Raw line from openmw.cfg
        :etype: (str) Type of the link (COMMENT or BLANK)
        """
        self.line = line.rstrip("\n")  # Remove newlines
        self.etype = etype
        self.config = config

    def __str__(self):
        return self.line


# -- Mods and Plugins --
class OmwMod(object):
    """Describes an installed openmw mod and retains useful info about the mod"""
    def __init__(self, path, config):
        """
        :path: (str) Absolute path to the mod.
        :config: (ConfigFile) openmw.cfg instance this mod belongs to.
        """
        self._path = path
        self._config = config
        self._plugins = self._load_plugins()

    def _load_plugins(self):
        """Get a list of plugins that exist in the mod directory.

        :returns: (list) List of plugins in the mod directory.
        """
        plugins = []
        plugin_extensions = [".esm", ".esp", ".omwaddon"]
        for fname in self.files:
            for ext in plugin_extensions:
                if fname.lower().endswith(ext):
                    plugins.append(OmwPlugin(fname, self.config, self))

        return plugins

    def enable(self):
        self.config.mods.append(self)

    def disable(self):
        self.config.mods.remove(self)

    @property
    def path(self):
        return self._path

    @property
    def name(self):
        return os.path.basename(self.path)

    @property
    def dirs(self):
        """Get a list of directories that exist in the mod directory.

        :returns: (list) List of directories in the mod directory.
        """
        dirs = []
        path = self.path
        for fname in os.listdir(path):
            if os.path.isdir(os.path.join(path, fname)):
                dirs.append(fname)

        return dirs

    @property
    def files(self):
        """Get a list of files that exist in the mod directory.

        :returns: (list) List of files in the mod directory.
        """
        files = []
        path = self.path
        for fname in os.listdir(path):
            if os.path.isfile(os.path.join(path, fname)):
                files.append(fname)

        return files

    @property
    def plugins(self):
        return self._plugins

    @property
    def plugins_enabled(self):
        plugins = [p for p in self.plugins if p.is_enabled]
        plugins.sort(key=lambda p: self.config.plugins.index(p))
        return plugins

    @property
    def plugins_disabled(self):
        return [p for p in self.plugins if not p.is_enabled]

    @property
    def config(self):
        return self._config

    @property
    def order(self):
        return self.config.mods.index(self) + 1


class OmwPlugin(object):
    def __init__(self, name, config, mod=None):
        """Class that describes the properties of an openmw plugin

        :name: (str) basename of the plugin
        :config: (ConfigFile) openmw.cfg instance
        :mod: (OmwMod) Parent mod
        """
        self._name = name
        self._config = config
        self._mod = mod
        self._enabled = False

    @property
    def name(self):
        return self._name

    @property
    def path(self):
        if self.mod:
            return os.path.join(self.mod.path, self.name)
        else:
            return None

    @property
    def mod(self):
        return self._mod

    @mod.setter
    def mod(self, mod):
        self._mod = mod

    @property
    def config(self):
        return self._config

    @property
    def is_enabled(self):
        return self._enabled

    @property
    def is_orphan(self):
        if not self.mod:  # :'(
            return True
        else:
            return False

    @property
    def order(self):
        """Get the plugins load order

        :return: (int or None)
        """
        if not self.is_enabled:
            return None

        return self.config.plugins.index(self) + 1

    def enable(self, order=None):
        """Enable the plugin in openmw.cfg"""
        if self.is_enabled:
            raise ValueError("Plugin %s is already enabled" % self.name)

        if order is None:
            order = len(self.config.plugins)

        self.config.plugins.insert(order, self)
        self._enabled = True

    def disable(self):
        """Disable the plugin by removing its content entry from openmw.cfg"""
        if not self.is_enabled:
            raise ValueError("Plugin %s is already disabled" % self.name)

        self.config.plugins.remove(self)
        self._entry = None
        self._enabled = False
