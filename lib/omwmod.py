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

        self.reset(path=path, entry=entry)

    def reset(self, path=None, entry=None):
        """Change the mods path or entry and update all other attributes.

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
                if file.endswith(ext):
                    plugins.append(file)

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
