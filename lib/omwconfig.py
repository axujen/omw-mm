# ConfigEntry and ConfigFile are classes that describe the openmw.cfg file.
# TODO: Refactor these classes, they are an ugly mess.
import omwmod


class ConfigEntry(object):
    """OpenMW config entry.

    If value is ommitted then key is parsed as a raw line (key=value).

    :key:   (str) Line from openmw.cfg as is.
    :value: (str) Value of key, Default: None.
    :config: (ConfigFile) Config object where this entry resides. Default: None
    :raises: (ValueError)
    """

    # TODO: Redo init, it looks like a mess.
    def __init__(self, key, value=None, config=None):
        if not value:  # Value was not given so assuming key is a raw line
            key, value, entry_type = self._parse_line(key)
        else:
            entry_type = "SETTING"

        self._config = config
        self._type = entry_type
        self._key, self._value = self._parse_key_value(key, value)

    def __str__(self):
        entry_type = self.get_type()
        if entry_type == "COMMENT":
            return "#" + self.get_value()
        elif entry_type == "BLANK":
            return self.get_value()
        elif entry_type == "SETTING":
            return "=".join([self.get_key(), self.get_value(raw=True)])
        else:  # Unrecognized type? Raise an error.
            raise ValueError("Entry has an unrecognized type %s" % entry_type)

    def __eq__(self, other):
        """Compare entries by key and value"""
        key_match = self.get_key() == other.get_key()
        value_match = self.get_value() == other.get_value()
        return key_match and value_match

    def _parse_line(self, line):
        """Parse openmw.cfg line entry

        :line: (str): Raw line from openmw.cfg
        :returns: (set) key, value, type
        :raises: (ValueError)
        """
        # TODO: Add support for categories either here or in ConfigFile()
        # to support settings.cfg in the future.
        # for now keep it simple
        if line.isspace():  # Entry is blank
            entry_type = "BLANK"
            key = None
            value = line
            return [key, value, entry_type]

        if line.startswith("#"):  # Entry is a comment
            entry_type = "COMMENT"
            key = None
            value = line[1:]

            return [key, value, entry_type]

        # Other than comments only accept key=value entries.
        # May expand this class later to support settings.cfg [Sections]
        if len(line) < 3 or "=" not in line:
            raise ValueError("Invalid config entry '%s'" % line)

        entry_type = "SETTING"
        key, value = line.split("=")
        return (key.strip(), value.strip(), entry_type)

    def _parse_key_value(self, key, value):
        """Parse a key, value pair and return normalized entries.

        :key: (str)
        :value: (str)
        :returns: (set)
        """
        # Entry keys cannot (or should not?) contain comments
        if "#" in key:
            raise ValueError("Entry key cannot contain a comment. got '%s'" % key)

        # Strip comments from values and raise an error if value
        # turns out to be empty
        old_value = value
        value = value.split("#")[0].strip()
        if not value:
            raise ValueError("Entry value cannot be empty. got '%s'" % old_value)

        # Automatically add quotes for data entries
        if key == "data":
            if not value[0] == value[-1] == '"':  # is the value quoted?
                # then quote it for internal storage.
                value = '"%s"' % value

        return (key, value)

    def get_key(self, raw=False):
        """Return the entry key.

        :raw: (bool) if True return self.__key directly without processing
        :returns: (str)
        """
        return self._key

    def get_value(self, raw=False):
        """Return the entry value.

        :raw: (bool) if True return self.__value directly without processing
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

    def get_type(self):
        """Return the entry type.

        :returns: (string)
        """
        return self._type


class ConfigFile(object):
    """OpenMW config file openmw.cfg

    :file: (str): Path to openmw.cfg, Default: None
    """

    def __init__(self, file=None):
        self._entries = []
        self._mods = []
        if file:
            self.file = file
            self._parse()

    def __contains__(self, entry):
        if not isinstance(entry, ConfigEntry):
            raise ValueError("ConfigFile can only contain ConfigEntry objects, got %s" % entry.__class__.__name__)
        return self.get_entries().__contains__(entry)

    def __iter__(self, *args, **kwargs):
        return self.get_entries().__iter__(*args, **kwargs)

    def tostring(self):
        """Convert entries into a string ready to save on disk."""

        return "\n".join((str(e) for e in self.get_entries(all=True)))

    def find_key(self, key):
        """Return a list object containing entries with matching key.

        :key: (str) name of the search key
        :returns: (list)
        """
        return [e for e in self if e.get_key() == key]

    def find_value(self, value):
        """Return a list object containing entries with matching value

        :value: (str) name of the search value
        :returns: (list)
        """
        return [e for e in self if e.get_value() == value]

    def get_entries(self, all=False):
        """Get the list of entries in the config file

        :all: (bool) If true return all entries including empty lines and comments.
        :returns: (list)
        """
        if all:
            return self._entries
        else:
            return [e for e in self._entries if e.get_type() == "SETTING"]

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
        if not isinstance(entry, ConfigEntry):
            raise ValueError("ConfigFile only accepts ConfigEntry. got %s" % entry)

        if entry not in self:
            raise ValueError("Entry: '%s' not in config file" % entry)

        entry.set_config(None)
        self._entries.remove(entry)

    def insert(self, index, entry):
        if not isinstance(entry, ConfigEntry):
            raise ValueError("ConfigFile only accepts ConfigEntry. got %s" % entry)
        if entry in self:
            raise ValueError("Entry '%s' is already in openmw.cfg" % entry)

        entry.set_config(self)
        self._entries.insert(index, entry)

    def append(self, entry):
        self.insert(len(self.get_entries(all=True)), entry)

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
            index = self.get_entries().index(entries[-1]) + 1
        else:  # Append in the bottom of the config
            index = len(self.get_entries())

        self.insert(index, entry)

    def _parse(self):
        """Read and parse openmw.cfg"""

        with open(self.file, "r") as fh:
            for line in fh.readlines():
                entry = ConfigEntry(line, config=self)
                self.append(entry)

                # Create and keep track of mod objects
                if entry.get_key() == "data":
                    mod = omwmod.OmwMod(entry.get_value(), entry)
                    self._mods.append(mod)

    def write(self, path=None):
        """Save the config file to a location on disk.

        :path: (str) Path to save to. Default: original path
        """

        if not path:
            path = self.file

        with open(path, "w") as fh:
            fh.write(self.tostring())
