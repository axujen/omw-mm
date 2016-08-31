# ConfigEntry and ConfigFile are classes that describe the openmw.cfg file.
# TODO: Make ConfigEntry a subclass of ConfigRawEntry
import omwmod


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

        key_match = self.get_key() == other.get_key()
        value_match = self.get_value() == other.get_value()
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

    def get_key(self, raw=False):
        """Return the entry key.

        :raw: (bool) if True return self._key directly without processing
        :returns: (str)
        """
        return self._key

    def get_value(self, raw=False):
        """Return the entry value.

        :raw: (bool) if True return self._value directly without processing
        :returns: (str)
        """
        if self.get_key() == "data" and not raw:
            return self._value.strip('"')

        return self._value

    def set_config(self, config):
        """Set the ConfigFile object this entry belongs to.

        :config: (ConfigFile or None)
        """
        if config is not None and not isinstance(config, ConfigFile):
            raise ValueError("config must be a ConfigFile object. got %s" % config)
        self._config = config

    def get_config(self):
        """Get the entry config object.

        :returns: (ConfigFile) openmw.cfg object
        """
        return self._config


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

    def set_config(self, config):
        self.config = config

    def get_config(self):
        return self.config


class ConfigFile(object):
    def __init__(self, path=None):
        """OpenMW config file openmw.cfg.

        :path: (str): Path to openmw.cfg, Default: None
        """
        self._entries = []
        self._mods = []
        if path:
            self._path = path
            self.unpack()

    def tostring(self):
        """Convert entries into a string ready to save on disk."""
        out = ''
        for entry in self.get_entries(all=True):
            out += str(entry) + "\n"
        return out

    def find_key(self, key):
        """Return a list object containing entries with matching key.

        :key: (str) name of the search key
        :returns: (list)
        """
        return [e for e in self.get_entries() if e.get_key() == key]

    def find_value(self, value):
        """Return a list object containing entries with matching value

        :value: (str) name of the search value
        :returns: (list)
        """
        return [e for e in self.get_entries() if e.get_value() == value]

    def get_entries(self, all=False):
        """Get the list of entries in the config file

        :all: (bool) If true return all entries including empty lines and comments.
        :returns: (list)
        """
        if all:
            return self._entries
        else:
            return [e for e in self._entries if isinstance(e, ConfigEntry)]

    def get_mods(self):
        """Get the list of installed mods

        :returns: (list)
        """
        return self._mods

    def remove(self, entry):
        """Remove entry from ConfigFile.

        :entry: (ConfigEntry) entry to be removed.
        :returns: (int) Index of the removed entry.
        """
        if not isinstance(entry, ConfigEntry) and not isinstance(entry, ConfigRawEntry):
            raise ValueError("ConfigFile only contains ConfigEntry and ConfigRawEntry, got %s" % type(entry))

        if entry not in self._entries:
            raise ValueError("Entry: '%s' not in config file" % entry)

        entry.set_config(None)
        self._entries.remove(entry)

    def insert(self, index, entry):
        if not isinstance(entry, ConfigEntry) and not isinstance(entry, ConfigRawEntry):
            raise ValueError("ConfigFile only accepts ConfigEntry and ConfigRawEntry, got %s" % type(entry))
        if entry in self._entries:
            raise ValueError("Entry '%s' is already in openmw.cfg" % entry)

        entry.set_config(self)
        self._entries.insert(index, entry)

    def add_entry(self, entry):
        """Add an entry to the config file, unlike append this method will insert
        the entry near other entries of the same key.

        :entry: (ConfigEntry) Entry to be added.
        """
        if not isinstance(entry, ConfigEntry):
            raise ValueError("Expecting ConfigEntry object. got %s" % entry)

        key = entry.get_key()
        entries = self.find_key(key)
        if entries:  # If entries with the same key exist then append to bottom of that list
            index = self.get_entries(all=True).index(entries[-1]) + 1
        else:  # Append in the bottom of the config
            index = len(self.get_entries(all=True))

        self.insert(index, entry)

    def unpack(self):
        """Read and parse openmw.cfg"""
        with open(self._path, "r") as fh:
            for line in fh.readlines():
                if line.isspace():  # Blank line.
                    entry = ConfigRawEntry(line, "BLANK", config=self)
                elif line.strip().startswith("#"):  # Comment
                    entry = ConfigRawEntry(line, "COMMENT", config=self)
                else:  # Normal entry
                    entry = ConfigEntry(line, config=self)
                self._entries.append(entry)

                # Create and keep track of mod objects
                if isinstance(entry, ConfigEntry) and entry.get_key() == "data":
                    mod = omwmod.OmwMod(entry.get_value(), entry)
                    self._mods.append(mod)

    def write(self, path=None):
        """Save the config file to a location on disk.

        :path: (str) Path to save to. Default: original path
        """
        if not path:
            path = self._path

        with open(path, "w") as handle:
            handle.write(self.tostring())
