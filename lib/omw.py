# Classes that represent openmw config files and mods/plugins
import os


# -- Configuration --
class ConfigFile(object):
    def __init__(self, path=None):
        """OpenMW config file openmw.cfg.

        :path: (str): Path to openmw.cfg, Default: None
        """
        self._entries = []
        self._mods = []

        if path:
            self._path = path
            self.load()

    def find_key(self, key):
        """Return a list object containing entries with matching key.

        :key: (str) name of the search key
        :returns: (list)
        """
        return [e for e in self.entries if e.key == key]

    def find_value(self, value):
        """Return a list object containing entries with matching value

        :value: (str) name of the search value
        :returns: (list)
        """
        return [e for e in self.entries if e.value == value]

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

    def remove(self, entry):
        """Remove entry from ConfigFile.

        :entry: (ConfigEntry) entry to be removed.
        :returns: (int) Index of the removed entry.
        """
        entry.config = None
        self.entries.remove(entry)

    def insert(self, index, entry):
        if not isinstance(entry, ConfigEntry) and not isinstance(entry, ConfigRawEntry):
            raise ValueError("ConfigFile only accepts ConfigEntry and ConfigRawEntry, got %s" % type(entry))
        if entry in self.entries:
            raise ValueError("Entry '%s' is already in openmw.cfg" % entry)

        entry.config = self
        self.entries.insert(index, entry)

    def add_entry(self, entry):
        """Add an entry to the config file, unlike append this method will insert
        the entry near other entries of the same key.

        :entry: (ConfigEntry) Entry to be added.
        """
        if not isinstance(entry, ConfigEntry):
            raise ValueError("Expecting ConfigEntry object. got %s" % entry)

        entries = self.find_key(entry.key)
        if entries:  # If entries with the same key exist then append to bottom of that list
            index = self.entries.index(entries[-1]) + 1
        else:  # Append in the bottom of the config
            index = len(self.entries)

        self.insert(index, entry)

    def load(self):
        """Load the openmw.cfg file into the instance."""
        with open(self.path, "r") as fh:
            for line in fh.readlines():
                if line.isspace():  # Blank line.
                    entry = ConfigRawEntry(line, "BLANK", config=self)
                elif line.strip().startswith("#"):  # Comment
                    entry = ConfigRawEntry(line, "COMMENT", config=self)
                else:  # Normal entry
                    entry = ConfigEntry(line, config=self)
                self.entries.append(entry)

                # Create and keep track of mod objects
                if isinstance(entry, ConfigEntry) and entry.key == "data":
                    mod = OmwMod(entry.value, entry)
                    self.mods.append(mod)

    def _tostring(self):
        """Convert entries into a string ready to save on disk."""
        return "\n".join((str(e) for e in self.entries))

    def write(self, path=None):
        """Save the config file to a location on disk.

        :path: (str) Path to save to. Default: original path
        """
        if not path:
            path = self.path

        with open(path, "w") as handle:
            handle.write(self.tostring())


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
    """Describes an openmw mod and retains useful info about the mod"""

    def __init__(self, path, entry=None):
        """Init with a path (all mods should exist somewhere), and an openmw config entry if it has one.

        :path: (str) Absolute path to the mod.
        :entry: (ConfigEntry) Mods config entry. Default: None
        """
        self._entry = None
        self.init(path=path, entry=entry)

    def init(self, path=None, entry=None):
        """Init the instance with new values.

        :path: (str) Absolute path to the mod. Default: Current path
        :entry: (ConfigEntry) Mods config entry. Default: Current entry
        """
        if not path:
            path = self.path
        if not entry:
            entry = self.entry

        if not os.path.isabs(path):
            raise ValueError("Path must be an absolute path. got %s" % path)

        if entry and not isinstance(entry, ConfigEntry):
            raise ValueError("Entry must be a ConfigEntry object. got %s" % entry)

        self._path = path
        self._entry = entry

    @property
    def path(self):
        return self._path

    @property
    def entry(self):
        return self._entry

    @property
    def is_installed(self):
        return self.entry and self.config

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
        """Get a list of plugins that exist in the mod directory.

        :returns: (list) List of plugins in the mod directory.
        """
        plugins = []
        plugin_extensions = [".esm", ".esp", ".omwaddon"]
        path = self.path
        for fname in self.files:
            # Skip directories
            if not os.path.isfile(os.path.join(path, fname)):
                continue

            for ext in plugin_extensions:
                if fname.lower().endswith(ext):
                    plugins.append(OmwPlugin(self, fname))

        return plugins

    @property
    def config(self):
        """Get the current openmw.cfg object where this mod is referenced.

        :returns: (ConfigFile or None)
        """
        if not self.entry:
            return None
        else:
            return self.entry.config

    @property
    def order(self):
        """Get the mods load order.

        :returns: (int) Mods load order.
        """
        if not self.is_installed:
            raise ValueError("Mod %s is not currently installed" % self.name)

        config = self.config
        if self.entry not in config.entries:
            raise ValueError("%s does not have an entry in %s" % (self.name, config.file))

        index = 1
        for entry in config.find_key("data"):
            if entry.value == self.path:
                return index
            index += 1

        # This shouldn't happen
        raise ValueError("Could not find an entry for %s in %s" % (self.name, config.file))


class OmwPlugin(object):
    def __init__(self, mod, name):
        """Class that describes the properties of an openmw plugin

        :mod: (OmwMod) Parent mod
        :name: (str) Name of the plugin with the extension
        """
        if not isinstance(mod, OmwMod):
            raise ValueError("Expecting OmwMod, got %s" % mod)

        plugin_extensions = [".esm", ".esp", ".omwaddon"]
        for ext in plugin_extensions:
            if name.lower().endswith(ext):
                break
        else:  # Confused? see http://python-notes.curiousefficiency.org/en/latest/python_concepts/break_else.html
            raise ValueError("Plugin name must end with a known plugin extension, got %s" % name)

        self._mod = mod
        self._name = name

    @property
    def name(self):
        return self._name

    @property
    def path(self):
        return os.path.join(self.mod.path, self.name)

    @property
    def mod(self):
        return self._mod

    @property
    def config(self):
        if not self.is_installed:
            raise ValueError("Plugin %s is not installed" % self.name)

        return self.mod.config

    @property
    def entry(self):
        if not self.is_enabled:
            raise ValueError("Plugin %s is not enabled, cannot retrieve entry" % self.name)

        cfg = self.config
        for entry in cfg.find_key("content"):
            if self.name == entry.name:
                return entry

    @property
    def is_installed(self):
        """Check if the plugin is installed.
        A plugin is considered installed if its parent mod is installed

        :returns: (bool)
        """
        return self.mod.is_installed

    @property
    def is_enabled(self):
        """Check if the plugin is installed an enabled.

        :returns: (bool)
        """
        if self.is_installed:
            cfg = self.config
        else:  # Mod not installed, then plugin not installed.
            # TODO: This will return a negative when the mod is not installed
            # But the content entry for the plugin is still there.
            return False

        # dont call self.entry here, it calls this method
        for entry in cfg.find_key("content"):
            if self.name == entry.value:
                return True

        return False

    @property
    def order(self):
        """Find the plugins load order

        :returns: (int)
        """
        if not self.is_enabled:
            return None

        index = 1
        for entry in self.config.find_key("content"):
            if self.name == entry.value:
                return index
            else:
                index += 1

        # This shouldn't happen
        raise ValueError("Could not find an entry for %s in %s" % (self.name, self.config.file))

    def enable(self):
        """Enable the plugin in openmw.cfg"""
        if not self.is_installed:
            raise ValueError("Cannot enable plugin %s, its not installed" % self.name)

        if self.is_enabled:
            raise ValueError("Plugin %s is already enabled" % self.name)

        entry = ConfigEntry("content", self.name)
        self.config.add_entry(entry)

    def disable(self):
        """Disable the plugin by removing its content entry from openmw.cfg"""

        if not self.is_enabled:
            raise ValueError("Plugin %s is already disabled" % self.name)

        for entry in self.config.find_key("content"):
            if self.name == entry.value:
                self.config.remove(entry)
                return

        # Shouldn't happen
        raise ValueError("Plugin %s does not have a entry in %s" % (self.name, self.config.file))
