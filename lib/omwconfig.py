# ConfigEntry and ConfigFile are classes that describe the openmw.cfg file.
# TODO: Refactor these classes, they are an ugly mess.


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
        if config is not None and not isinstance(config, ConfigFile):
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

    def __init__(self, file=None):
        self.__entries = []
        if file:
            self.file = file
            self._parse()

    def __contains__(self, entry):
        if not isinstance(entry, ConfigEntry):
            raise ValueError("ConfigFile can only contain ConfigEntry objects, got %s" % entry.__class__.__name__)
        return self.__entries.__contains__(entry)

    def __iter__(self, *args, **kwargs):
        return self.__entries.__iter__(*args, **kwargs)

    def tostring(self):
        """Convert entries into a string ready to save on disk."""

        return "\n".join((str(i) for i in self))

    def find_key(self, key):
        """Return a ConfigFile object containing entries with matching key.

        :key: (str) name of the search key
        :returns: (ConfigFile)
        """

        output = ConfigFile()
        for entry in self:
            if entry.get_key() == key:
                entry.set_config(self)
                output.__entries.append(entry)

        return output or None

    def find_value(self, value):
        """Return a ConfigFile object containing entries with matching value

        :value: (str) name of the search value
        :returns: (ConfigFile)
        """
        output = ConfigFile()
        for entry in self:
            if entry.get_value(raw=True) == value:
                entry.set_config(self)
                output.__entries.append(entry)

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
        return self.insert(len(self.__entries), entry)

    def _parse(self):
        """Read and parse openmw.cfg"""

        # Entries are stored in a list containing dicts, this is because
        # openmw.cfg has duplicate keys.
        with open(self.file, "r") as fh:
            for line in fh.readlines():
                # Empty lines are ignored.
                # This is the same behaviour as openmw-launcher
                if line.isspace():
                    continue

                self.append(ConfigEntry(line, config=self))

    def write(self, path=None):
        """Save the config file to a location on disk.

        :path: (str) Path to save to. Default: original path
        """

        if not path:
            path = self.file

        with open(path, "w") as fh:
            fh.write(self.tostring())
