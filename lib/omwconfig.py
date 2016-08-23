# ConfigEntry and ConfigFile are classes that describe the openmw.cfg file.


class ConfigEntry(object):
    """OpenMW config entry.

    If value is ommitted then key is parsed to determine the type.

    :key:   (str) Line from openmw.cfg as is.
    :value: (str) Value of key, Default: None.
    :config: (ConfigFile) Config object where this entry resides. Default: None
    :raises: (ValueError)
    """

    # TODO: Redo init, it looks like a mess.
    def __init__(self, key, value=None, config=None):
        if not value:
            key, value, type = self.__parse_line(key)
        else:
            type = "SETTING"

        # Entry keys cannot (or should not?) contain comments
        if "#" in key:
            raise ValueError("Entry key cannot contain a comment. got '%s'" % key)

        # Strip comments from values and raise an error if value
        # turns out to be empty
        # TODO: Preserve comments in their own variable.
        old_value = value
        value = value.split("#")[0].strip()
        if not value:
            raise ValueError("Entry value cannot be empty. got '%s'" % old_value)

        # Automatically add quotes for data entries
        if key == "data":
            if not value[0] == value[-1] == '"':  # is the value quoted?
                # then quote it for internal storage.
                value = '"%s"' % value

        self.set_config(config)
        self.__key = key
        self.__value = value
        self.__type = type

    def __str__(self):
        if self.get_type() == "COMMENT":
            return "#" + self.get_value()
        else:
            return "=".join([self.get_key(), self.get_value(raw=True)])

    __repr__ = __str__

    def __eq__(self, other):
        return str(self) == str(other)

    def __parse_line(self, line):
        """Parse openmw.cfg line entry

        :line: (str): Raw line from openmw.cfg
        :returns: (list) [key, value, type].
        :raises: (ValueError)
        """

        # TODO: Add support for categories either here or in ConfigFile()
        # to support settings.cfg in the future.
        # for now keep it simple
        if line.isspace():
            raise ValueError("Config entry cannot be blank line.")

        if line[0] == "#":
            type = key = "COMMENT"
            value = line[1:]

            return [key, value, type]

        # Other than comments only accept key=value entries.
        # May expand this class later to support settings.cfg [Sections]
        if len(line) < 3 or "=" not in line:
            raise ValueError("Invalid config entry '%s'" % line)

        type = "SETTING"
        key, value = line.split("=")
        return [key.strip(), value.strip(), type]

    def get_key(self, raw=False):
        """Return the entry key.

        :raw: (bool) if True return self.__key directly without processing
        :returns: (str)

        """
        return self.__key

    def get_value(self, raw=False):
        """Return the entry value.

        :raw: (bool) if True return self.__value directly without processing
        :returns: (str)
        """
        if self.__key == "data" and not raw:
            return self.__value.strip('"')

        return self.__value

    def set_config(self, config):
        """Set the entry config object

        :config: (ConfigFile) openmw.cfg object.
        """
        if not isinstance(config, ConfigFile):
            raise ValueError("config must be a ConfigFile object. got %s" % config)
        self.__config = config

    def get_config(self):
        """Get the entry config object.

        :returns: (ConfigFile) openmw.cfg object
        """
        return self.__config

    def get_type(self):
        """Return the entry type.

        :returns: (string)
        """
        return self.__type


class ConfigFile(object):
    """OpenMW config file openmw.cfg

    :file: (str): Path to openmw.cfg, Default: None
    """

    # TODO: Update this class to take file handles instead of filenames
    def __init__(self, file=None):
        self.__entries = []
        if file:
            self.file = file
            self.parse()

    def __len__(self):
        return self.__entries.__len__()

    def __str__(self):
        """Convert entries into a string ready to save on disk."""

        return "\n".join((str(i) for i in self))
    __repr__ = __str__

    def __getitem__(self, index):
        if isinstance(index, slice):
            output = ConfigFile()
            if index.stop:
                stop = index.stop
            else:
                stop = len(self)

            if index.start:
                start = index.start
            else:
                start = 0

            for i in range(start, stop):
                output.append(self.__entries[i])
            return output

        return self.__entries.__getitem__(index)

    def __setitem__(self, index, object):
        return self.__entries.__setitem__(index, object)

    def __delitem__(self, index, object=None):
        return self.__entries.__delitem__(index, object)

    def __contains__(self, entry):
        return self.__entries.__contains__(entry)

    def __iter__(self):
        return self.__entries.__iter__()

    def __get_lines(self):
        """Read the config file and return a list of lines (str)."""
        return open(self.file, "r").readlines()

    def find_key(self, key):
        """Return a ConfigFile object containing entries with matching key.

        :key: (str) name of the search key
        :returns: ConfigFile object

        """

        output = ConfigFile()
        for entry in self:
            if entry.get_key() == key:
                output.append(entry)

        return output or None

    def find_value(self, value):
        """Return a ConfigFile object containing entries with matching value

        :value: (str) name of the search value
        :returns: ConfigFile object

        """
        output = ConfigFile()
        for entry in self:
            if entry.get_value(raw=True) == value:
                output.append(entry)

        return output or None

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
        self.__entries.remove(entry)

    def insert(self, index, entry):
        if not isinstance(entry, ConfigEntry):
            raise ValueError("ConfigFile only accepts ConfigEntry. got %s" % entry)
        if entry in self:
            raise ValueError("Entry '%s' is already in openmw.cfg" % entry)

        entry.set_config(self)
        return self.__entries.insert(index, entry)

    def append(self, entry):
        return self.insert(len(self), entry)

    def parse(self):
        """Read the config file and return a list of dicts for each entry."""

        # Entries are stored in a list containing dicts, this is because
        # openmw.cfg has duplicate keys.
        for line in self.__get_lines():
            # Empty lines are ignored.
            # This is the same behaviour as openmw-launcher
            if line.isspace():
                continue

            self.append(ConfigEntry(line, config=self))

    def write(self, path=None):
        """Save the config file to a location on disk.

        Args:
            path (str): path to save. Default: self.file
        """

        if not path:
            path = self.file

        open(path, "w").write(str(self))
