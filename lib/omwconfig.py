#!/usr/bin/env python2.7
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

# Python script to manage openmw mods, hopefully (never) will be updated with
# an actual gui.
# Right now it should list, install and remove mods in their seperate folders
# Goals: - List, Install, Remove mods.
#        - Install from archives, auto unpack, auto backup
#        - GUI


# Currently its nothing more than a dictionary, but will probably need to
# be expanded later on
from collections import MutableSequence


class ConfigEntry():
    """OpenMW config entry

    If value is ommitted then key is parsed to determine the type.
    Args:
        key (str): Line from openmw.cfg as is.
        value (str): Value of key, Default: None.
    """

    def __init__(self, key, value=None):
        if value:
            self.__type = "SETTING"
            self.key, self.value = key.strip(), value.strip()
        else:
            self.__parse(key)

    def __str__(self):
        if self.type() == "COMMENT":
            return "#" + self.value
        else:
            return "=".join([self.key, self.value])

    __repr__ = __str__

    def __eq__(self, other):
        return str(self) == str(other)

    def __parse(self, line):
        """Parse openmw.cfg line entry

        line (str): Line from openmw.cfg as is.
        """

        # TODO: Add support for categories either here or in ConfigFile()
        # to support settings.cfg in the future.
        # for now keep it simple
        if line.isspace():
            raise ValueError("Config entry cannot be blank line.")

        if line[0] == "#":
            self.__type = "COMMENT"
            self.key = self.__type
            self.value = line[1:]

            return

        # Other than comments only accept key=value entries.
        # May expand this class later to support settings.cfg [Sections]
        if len(line) < 3 or "=" not in line:
            raise ValueError("Invalid config entry '%s'" % line)

        self.__type = "SETTING"
        k,v = line.split("=")
        self.key, self.value = k.strip(), v.strip()

    def type(self):
        """Return the type of the entry

        :returns: string

        """
        return self.__type


class ConfigFile(object):
    """OpenMW config file openmw.cfg

    Args:
        file (str): Path to openmw.cfg, Default: None
    """
    # TODO: Update this class to take file handles instead of filenames

    def __init__(self, file=None):
        self.entries = []
        if file:
            self.file = file
            self.parse()

    def insert(self, index, object):
        return self.entries.insert(index, object)

    def __len__(self):
        return self.entries.__len__()

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
                output.append(self.entries[i])
            return output

        return self.entries.__getitem__(index)

    def __setitem__(self, index, object):
        return self.entries.__setitem__(index, object)

    def __delitem__(self, index, object=None):
        return self.entries.__delitem__(index, object)

    def __contains__(self, entry):
        return entry in self.entries

    def __get_lines(self):
        """Read the config file and return a list of lines (str)."""
        return open(self.file, "r").read().split("\n")[:-1]

    def find_key(self, key):
        """Return a ConfigFile object containing entries with matching key.

        :key: (str) name of the search key
        :returns: ConfigFile object

        """

        output = ConfigFile()
        for entry in self:
            if entry.key == key:
                output.append(entry)

        return output or None

    def find_value(self, value):
        """Return a ConfigFile object containing entries with matching value

        :value: (str) name of the search value
        :returns: ConfigFile object

        """
        output = ConfigFile()
        for entry in self:
            if entry.value == value:
                output.append(entry)

        return output or None

    def insert(self, index, entry):
        if not isinstance(entry, ConfigEntry):
            raise ValueError("ConfigFile expects ConfigEntry objects, got %s" %s)

        return self.entries.insert(index, entry)

    def append(self, entry):
        return self.insert(len(self), entry)

    def parse(self):
        """Read the config file and return a list of dicts for each entry."""

        # Entries are stored in a list containing dicts, this is because
        # openmw.cfg has duplicate keys.
        for line in self.__get_lines():
            # Empty lines are ignored.
            # This is the same behaviour as openmw-launcher
            if not line:
                continue

            self.append(ConfigEntry(line))

    def write(self, path=None):
        """Save the config file to a location on disk.

        Args:
            path (str): path to save. Default: self.file
        """

        if not path:
            path = self.file

        open(path, "w").write(str(self))
