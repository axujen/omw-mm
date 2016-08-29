import os
from omwconfig import ConfigEntry


# OmwMod class that contains usefull info about a given mod.
class OmwMod(object):
    """Describes an openmw mod and retains useful info about the mod"""

    def __init__(self, path, entry=None):
        """Init with a path (all mods should exist somewhere), and an openmw config entry if it has one.

        :path: (str) Absolute path to the mod.
        :entry: (ConfigEntry) Mods config entry. Default: None
        """
        # This is a hack to get the if self.__attribute and not update conditions
        # working properly, really didnt think that through :/
        self.__path = None
        self.__entry = None
        self.__name = None
        self.__dirs = None
        self.__files = None
        self.__plugins = None

        self.init(path=path, entry=entry)

    def init(self, path=None, entry=None):
        """Init the instance with new values.

        :path: (str) Absolute path to the mod. Default: Current path
        :entry: (ConfigEntry) Mods config entry. Default: Current entry
        """

        if not path:
            path = self.get_path()
        if not entry:
            entry = self.get_entry()

        if not os.path.isabs(path):
            raise ValueError("Path must be an absolute path. got %s" % path)

        if entry and not isinstance(entry, ConfigEntry):
            raise ValueError("Entry must be a ConfigEntry object. got %s" % entry)

        self.__path = path
        self.__entry = entry
        self.__name = self.get_name(update=True)
        self.__dirs = self.get_dirs(update=True)
        self.__files = self.get_files(update=True)
        self.__plugins = self.get_plugins(update=True)

    def get_path(self):
        return self.__path

    def get_entry(self):
        return self.__entry

    def is_installed(self):
        if self.get_entry() and self.get_config():
            return True
        else:
            return False

    def get_name(self, update=True):
        """Get the name of the mod.

        :update: (bool) If true, return updated value.
        :returns: (str) Name of the mod.
        """
        if self.__name and not update:
            return self.__name

        return os.path.basename(self.get_path())

    def get_dirs(self, update=False):
        """Get a list of directories that exist in the mod directory.

        :update: (bool) If true updates the current list again
        :returns: (list) List of directories in the mod directory.
        """

        if self.__dirs and not update:
            return self.__dirs

        dirs = []
        for file in os.listdir(self.get_path()):
            if os.path.isdir(os.path.join(self.get_path(), file)):
                dirs.append(file)

        return dirs

    def get_files(self, update=False):
        """Get a list of files that exist in the mod directory.

        :update: (bool) If true updates the current list again
        :returns: (list) List of files in the mod directory.
        """
        if self.__files and not update:
            return self.__files

        files = []
        for file in os.listdir(self.get_path()):
            if os.path.isfile(os.path.join(self.get_path(), file)):
                files.append(file)

        return files

    def get_plugins(self, update=False):
        """Get a list of plugins that exist in the mod directory.

        :update: (bool) If true updates the current list again
        :returns: (list) List of plugins in the mod directory.
        """

        if self.__plugins and not update:
            return self.__plugins

        plugins = []
        plugin_extensions = [".esm", ".esp", ".omwaddon"]
        for file in self.get_files(update):
            # Skip directories
            if not os.path.isfile(os.path.join(self.get_path(), file)):
                continue

            for ext in plugin_extensions:
                if file.lower().endswith(ext):
                    plugins.append(OmwPlugin(self, file))

        return plugins

    def get_config(self):
        """Give the current openmw.cfg object where this mod is referenced.

        :returns: (ConfigFile or None)
        """
        if not self.get_entry():
            return None
        else:
            return self.get_entry().get_config()

    def get_order(self):
        """Get the mods load order. (NOTE this is for mods not plugins).

        :cfg: (ConfigFile) openmw.cfg object.
        :returns: (int) Mods load order.
        """
        if not self.is_installed():
            raise ValueError("Mod %s is not currently installed" % self.get_name())

        cfg = self.get_config()
        if not self.get_entry() in cfg:
            raise ValueError("%s does not have an entry in %s" % (self.get_name(), cfg.file))

        index = 1
        for content in cfg.find_key("data"):
            if content.get_value() == self.get_path():
                return index
            index += 1

        # This shouldn't happen
        raise ValueError("Could not find an entry for %s in %s" % (self.get_name(), cfg.file))


# OmwPlugin is for plugins.
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

    def get_name(self):
        return self._name

    def get_path(self):
        return os.path.join(self.get_mod().get_path(), self.get_name())

    def get_mod(self):
        return self._mod

    def get_config(self):
        if not self.is_installed():
            raise ValueError("Plugin %s is not installed" % self.get_name())

        return self.get_mod().get_config()

    def get_entry(self):
        if not self.is_enabled():
            raise ValueError("Plugin %s is not enabled, cannot retrieve entry" % self.get_name())

        cfg = self.get_config()
        for entry in cfg.find_key("content"):
            if self.get_name() == entry.get_value():
                return entry

    def is_installed(self):
        """Check if the plugin is installed.
        A plugin is considered installed if its parent mod is installed

        :returns: (bool)
        """

        return self.get_mod().is_installed()

    def is_enabled(self):
        """Check if the plugin is installed an enabled.

        :returns: (bool)
        """
        if self.is_installed():
            cfg = self.get_config()
        else:  # Mod not installed, then plugin not installed.
            # TODO: This will return a negative when the mod is not installed
            # But the content entry for the plugin is still there.
            return False

        # dont call self.get_entry() here, it calls this method
        for entry in cfg.find_key("content"):
            if entry.get_value() == self.get_name():
                return True

        return False

    def get_order(self):
        """Find the plugins load order

        :returns: (int)
        """
        if not self.is_enabled():
            raise ValueError("Plugin %s is not enabled, does not have a load order" % self.get_name())

        cfg = self.get_config()
        index = 1
        for entry in cfg.find_key("content"):
            if self.get_name() == entry.get_value():
                return index
            else:
                index += 1

        # This shouldn't happen
        raise ValueError("Could not find an entry for %s in %s" % (self.get_name(), cfg.file))

    def enable(self):
        """Enable the plugin in openmw.cfg"""
        if not self.is_installed():
            raise ValueError("Cannot enable plugin %s, its not installed" % self.get_name())

        if self.is_enabled():
            raise ValueError("Plugin %s is already enabled" % self.get_name())

        cfg = self.get_config()
        entry = ConfigEntry("content", self.get_name())
        cfg.append(entry)

    def disable(self):
        """Disable the plugin by removing its content entry from openmw.cfg"""

        if not self.is_enabled():
            raise ValueError("Plugin %s is already disabled" % self.get_name())

        cfg = self.get_config()
        for entry in cfg.find_key("content"):
            if entry.get_value() == self.get_name():
                cfg.remove(entry)
                return

        # Shouldn't happen
        raise ValueError("Plugin %s does not have a entry in %s" % (self.get_name(), cfg.file))
