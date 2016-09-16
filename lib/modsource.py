# -*- coding: UTF-8 -*-
# This module is used to create an abstraction layer between mods stored in
# directories and mods stored in archives.
import os
import tempfile
import shutil
import core

# see core.py to understand why this was done.
libarchive = core.setup_libarchive()


class ModSource(object):
    """Generic mod source class that defines common methods for directory and archive mods."""
    def __init__(self, path):
        """
        :path: (str) Path to the mod source
        """
        self._path = path
        self._name = os.path.basename(self._path)

        self._files = self._get_files()
        self._dirs = sorted(self._files.keys())

    @property
    def name(self):
        return self._name

    @property
    def path(self):
        return self._path

    @property
    def is_mod(self):
        return bool(self._get_mod_dir())

    @property
    def files(self):
        return self._files

    @property
    def dirs(self):
        return self._dirs

    def _get_resource_dirs(self):
        resources = ("textures", "meshes", "icons", "fonts", "sound", "bookart",
                     "splash", "video")
        resource_dirs = []
        for dirpath in self.dirs:
            if os.path.split(dirpath)[1].lower() in resources:
                resource_dirs.append(dirpath)

        return resource_dirs

    def _get_plugins(self):
        extensions = (".esp", ".esm", "omwaddon")
        plugins = []
        for dirpath in self.dirs:
            for fname in self.files[dirpath]:
                if fname.lower().endswith(extensions):
                    plugins.append(os.path.join(dirpath, fname))

        return plugins

    def _get_mod_dir(self):
        """Find the root directory where the mod is located.

        :returns: (str)
        """
        resources = self._get_resource_dirs()
        plugins = self._get_plugins()
        if plugins:
            root = os.path.split(plugins[0])[0]
        else:
            if len(resources) == 1:
                root = os.path.split(resources[0])[0]
            else:
                root = os.path.commonprefix(resources)
        return root

    def install(self, dest):
        """Install the mod to the destination directory.

        :dest: (str) Destination.
        :returns: (str) The path of the newly installed mod
        """
        if not self.is_mod:
            raise ValueError("%s is not detected as a valid mod" % self.name)

        return self._install(dest)

    # --- Implement these methods in subclasses! ---
    def _install(self, dest):
        raise NotImplementedError

    def _get_files(self):
        """Return a dictionary of directories, each entry is a list of files.

        :returns: (dict)
        """
        # Must return a dict where the keys are paths to directories and directories
        # and directories contain lists of files.
        # / is the root of the mod source and every directory is a full path from /
        # example output:
        # {"/": ["MyPlugin.esp"],
        #  "/textures": ["texture1.dds", "texture2.dds"],
        #  "/textures/subfolder": ["texture3.dds"],
        #  ...
        #  ...
        # }
        raise NotImplementedError


class ModSourceDir(ModSource):
    """Class representing a mod stored in a directory"""
    def __init__(self, *args, **kwargs):
        super(ModSourceDir, self).__init__(*args, **kwargs)

    def _get_files(self):
        my_files = dict()
        for root, _, files in os.walk(self.path):
            if root == self.path:
                my_files["/"] = files
            else:
                my_files[root[len(self.path):]] = files
        return my_files

    def _install(self, dest):
        new_dir = os.path.join(dest, self.name)
        src_dir = os.path.join(self.path, self._get_mod_dir()[1:])
        shutil.copytree(src_dir, new_dir)
        return new_dir


class ModSourceArchive(ModSource):
    """Class representing a mod stored in an archive."""
    def __init__(self, *args, **kwargs):
        super(ModSourceArchive, self).__init__(*args, **kwargs)

    def _get_files(self):
        files = dict()
        with libarchive.file_reader(self.path) as archive:
            # Note using entry.isdir or other bool occasionally does not work
            for entry in archive:
                dir, file = os.path.split(entry.pathname)
                dir = "/" + dir
                if dir not in files.keys():
                    files[dir] = []
                if file:
                    files[dir].append(file)

        return files

    def _install(self, dest):
        root = self._get_mod_dir()
        tempdir = tempfile.mkdtemp()

        # Because libarchive doesn't support extracting to a specific directory
        prev_dir = os.path.abspath(os.getcwd())
        os.chdir(tempdir)
        try:
            for _ in libarchive.file_pour(self.path):
                pass
            if root == "/":
                src = tempdir
                name = os.path.splitext(self.name)[0]
            else:
                src = os.path.join(tempdir, root[1:])
                name = os.path.split(root)[-1]

            # Figure out a proper name for the mod.
            dest = os.path.join(dest, name)

            # Copy to the destination
            shutil.copytree(src, dest)
        finally:
            # Cleanup
            os.chdir(prev_dir)
            shutil.rmtree(tempdir)
        return dest
