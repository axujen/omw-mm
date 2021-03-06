# -*- coding: UTF-8 -*-
# Contains the Esm class that describes morrowinds esm/esp files.
import os.path
from StringIO import StringIO
from struct import unpack, pack


class Esm(object):
    def __init__(self, path):
        """This class describes a morrowind esm/esp file.

        :path: (str) Path to the file.
        """
        self._path = path
        self._records = []
        self.header = self.unpack_file_header()

    def find_records(self, id):
        """Search for a record by id.

        :id: (str) id of the record to search for
        :returns: (list) list of matched records
        """
        records = []
        for record in self._records:
            if record.id == id:
                records.append(record)

        return records

    @property
    def records(self):
        return self._records

    def unpack(self):
        """Unpack the file's records"""
        with open(self._path, "rb") as fh:
            EOF = len(fh.read())
            fh.seek(0)
            records = []
            while not fh.tell() == EOF:  # Because python doesn't support EOF
                # Record
                header = fh.read(16)
                id, size, delflag, recflag = unpack("4s3i", header)
                data = fh.read(size)
                if id == "TES3":  # Seperate the file header
                    self.header = EsmTES3Record(id, size, delflag, recflag, data)
                    continue
                if id in ("LEVC", "LEVI"):
                    record = EsmLEVRecord(id, size, delflag, recflag, data)
                else:
                    record = EsmRecord(id, size, delflag, recflag, data)
                records.append(record)

        self._records = records

    def unpack_file_header(self):
        """Unpack the file header only.

        :returns: (EsmTES3Record)
        """
        with open(self._path, "rb") as handle:
            id, size, delflag, recflag = unpack("4s3i", handle.read(16))
            assert id == "TES3"

            data = handle.read(size)
            return EsmTES3Record(id, size, delflag, recflag, data)

    def pack(self):
        """Pack the file contents into binary format.

        :returns: (str)
        """
        out = ''
        # Pack the header.
        out += self.header.pack()
        # Pack the records.
        for record in self._records:
            out += record.pack()

        return out

    def write(self, path=None):
        """Write the contents of the Esm to a file.

        :path: (str) Path to the file. Default: self._path
        """
        if not path:
            path = self._path

        with open(path, "wb") as handle:
            handle.write(self.pack())

    def merge_with(self, other):
        """Merge leveled lists from another esm with this one.

        :other: (Esm) esm instance to be merged with this.
        :returns: (dict) merged and Added leveled lists
        """
        if not isinstance(other, Esm):
            raise ValueError("Expecting Esm object, got %s" % other)

        diff = {}
        num_diff = 0
        for rec in ("LEVC", "LEVI"):
            diff[rec] = {"Merged": {}, "Added": {}}  # Keep track of whats merged and whats added
            my_records = {r._name: r for r in self.find_records(rec)}
            other_records = {r._name: r for r in other.find_records(rec)}
            for id, record in other_records.items():
                if id not in my_records:  # Add all LEV records so we can tell which ones need merging in the future
                    my_records[id] = record
                    diff[rec]["Added"][id] = my_records[id]
                else:
                    my_records[id].merge_with(record)
                    diff[rec]["Merged"][id] = my_records[id]

            # Replace the old records with the new merged ones:
            for index, record in enumerate(self.records):
                if record.id == rec:
                    if record._name in diff[rec]["Merged"]:
                        self._records[index] = diff[rec]["Merged"][record._name]

            # Add the new records (to the bottom of the file?)
            for _, record in diff[rec]["Added"].items():
                self._records.append(record)

            num_diff += len(diff[rec]["Merged"]) + len(diff[rec]["Added"])

        # Update the header with a new master if we merged any changes.
        if num_diff:
            self.header.add_master(other._path)
            self.header.record_count = len(self.records)

        return diff

    def post_merge(self):
        """Call this function after merging LEV lists to remove unmerged lists."""
        for rec in ("LEVC", "LEVI"):
            unmerged = [r for r in self.find_records(rec) if not r._merged]
            for record in unmerged:
                self._records.remove(record)


# This class is intended as read-only, Create a subclass so you can tell it how to
# repack its data by redefining the pack_data() method.
class EsmRecord(object):
    """Describes a esm record"""

    def __init__(self, id, size, delflag, recflag, data):
        """Takes a record id size flags and its raw data, parses the data into subrecords.

        :id: (str) id of the record.
        :size: (int) Size of the data of the record.
        :data: (str) Raw binary data of the record.
        """
        self._id, self._size, self.__data = id, size, data
        self._delflag, self._recflag = delflag, recflag
        self._changed = False

    @property
    def id(self):
        return self._id

    @property
    def size(self):
        if self._changed:
            self._size = len(self.data)

        return self._size

    @property
    def data(self):
        if self._changed:
            self.__data = self.pack_data()
            self._changed = False

        return self.__data

    @property
    def subrecords(self):
        """Unpack the data of a record into subrecords.

        :returns: (list) List of subrecords
        """
        subrecords = []
        data = self.data
        stream = StringIO(data)
        EOF = len(data)
        while not stream.tell() == EOF:
            header = stream.read(8)
            id, size = unpack("4si", header)
            data = stream.read(size)
            subrecords.append(EsmSubrecord(id, size, data))
        return subrecords

    def pack_subrecord(self, id, data, data_format=None):
        """Calculate the size of a subrecord and pack into the specified format.

        :id: (str) Subrecord's id.
        :data: (str or tuple) Subrecords's data, can be a tuple of strings or a single string.
        :data_format: (str) Data format, Default: len(data)s
        :returns: (str) Packed subrecord.
        """
        if not data_format:
            data_format = "%ds" % len(data)

        if isinstance(data, tuple):
            packed_data = pack(data_format, *data)
        else:
            packed_data = pack(data_format, data)

        out = pack("4si", id, len(packed_data))
        out += packed_data

        return out

    def pack_header(self):
        """Convert the records header back into binary format.

        :returns: (str)
        """
        return pack("4s3i", self.id, self.size, self._delflag, self._recflag)

    def pack(self):
        """Convert the record back to binary format.

        :returns: (str)
        """
        return self.pack_header() + self.data

    # This method only exists to be overriden by subclasses
    def pack_data(self):
        """Repack the records data.

        :returns: (str) The records data, this is equivalent of self.__data
        """
        return self.__data


class EsmSubrecord(object):
    """Class representing a generic subrecord."""
    def __init__(self, id, size, data):
        """Takes the subrecords id, size and raw data.

        :id: (str) id of the subrecord.
        :size: (int) Size of the subrecords data.
        :data: (str) Subrecords data.
        """
        self._id = id
        self._size = size
        self._data = data

    @property
    def id(self):
        return self._id

    @property
    def size(self):
        return self._size

    @property
    def data(self):
        return self._data

    def pack_header(self):
        """Convert the subrecord header back to binary format.

        :returns: (str)
        """
        return pack("4si", self.id, self.size)

    def pack(self):
        """Convert the subrecord to binary format.

        :returns: (str)
        """
        return self.pack_header() + self.data


# -- Specific Records.
class EsmLEVRecord(EsmRecord):
    """Leveled Items/Creatures Record."""

    def __init__(self, *args, **kwargs):
        super(EsmLEVRecord, self).__init__(*args, **kwargs)
        self.unpack_data()
        self._merged = False

    def unpack_data(self):
        """Unpack the data into meaningful values."""
        self._objects = []
        subrecords = self.subrecords
        for sub in subrecords:
            # List ID
            if sub.id == "NAME":
                self._name = sub.data

            # List specific flags
            elif sub.id == "DATA":
                self._calc_all_levels = False
                self._calc_all_items = False
                flag = unpack("i", sub.data)
                # Verify the correct value of these flags.
                # wrye mash uses 1: for all_items and 2: for all_levels
                # while every other source on the esm format says the opposite
                # Note: openmw-cs also uses the same values as wrye mash.
                if self.id == "LEVI":
                    if flag == 1:
                        self._calc_all_items = True
                    elif flag == 2:
                        self._calc_all_levels = True
                    elif flag == 3:
                        self._calc_all_items = self._calc_all_levels = True
                elif self.id == "LEVC":
                    if flag == 1:
                        self._calc_all_levels = True
            # Chance None
            elif sub.id == "NNAM":
                self._chance_none = unpack("B", sub.data)[0]

            # Number of creatures/items in the list
            elif sub.id == "INDX":
                self._count = unpack("i", sub.data)[0]

            # Creatue/Item ID
            elif sub.id == "CNAM" or sub.id == "INAM":
                object_id = sub.data

            # PC Level for the object
            elif sub.id == "INTV":
                pc_level = unpack("h", sub.data)[0]
                self._objects.append((pc_level, object_id))
            # Unknown
            else:
                raise ValueError("Unknown subrecord %s" % sub.id)

    def pack_data(self):
        out = ''
        out += self.pack_subrecord("NAME", self._name)
        # List specific flags
        if self.id == "LEVC":
            flag = 1 * self._calc_all_levels
            otype = "CNAM"
        else:
            flag = 1 * self._calc_all_items + 2 * self._calc_all_levels
            otype = "INAM"
        out += self.pack_subrecord("DATA", flag, "i")

        # Chance None
        out += self.pack_subrecord("NNAM", self._chance_none, "B")

        # Count
        out += self.pack_subrecord("INDX", self._count, "i")

        # Objects
        for lvl, obj in self._objects:
            out += self.pack_subrecord(otype, obj)
            out += self.pack_subrecord("INTV", lvl, "h")

        return out

    def merge_with(self, other):
        """Merge this leveled list with another list.

        :other: (EsmLEVRecord)
        """
        if not isinstance(other, EsmLEVRecord):
            raise ValueError("Cannot merge leveled list record with %s" % other)

        if not self.id == other.id:
            raise ValueError("Cannot merge records %s and %s" % (self.id, other.id))

        # Merge flags
        self._calc_all_items = self._calc_all_items or other._calc_all_items
        self._calc_all_levels = self._calc_all_levels or other._calc_all_levels
        self._chance_none = min(self._chance_none, other._chance_none)

        # Merge objects
        # if other._objects and not self._objects == other._objects:
        for obj in other._objects:
            if obj not in self._objects:
                self._objects.append(obj)
        # Sort the object list based on level
        self._objects.sort(key=lambda obj: obj[0])

        # Update object count
        self._count = len(self._objects)

        # Flag as modified
        self._changed = True
        # Flag as merged
        self._merged = True


class EsmTES3Record(EsmRecord):
    """Header record, contains auth and description of the plugin along with its dependencies"""
    def __init__(self, *args, **kwargs):
        super(EsmTES3Record, self).__init__(*args, **kwargs)
        self.unpack_data()

    def unpack_data(self):
        """Unpack the record."""
        mname = []
        msize = []
        for sub in self.subrecords:
            if sub.id == "HEDR":
                ver, ftype, auth, desc, num_records = unpack("fi32s256si", sub.data)
            if sub.id == "MAST":
                mname.append(sub.data.rstrip("\x00"))
            if sub.id == "DATA":
                msize.append(unpack("l", sub.data)[0])

        self._ver = ver
        self._ftype = ftype
        self._auth = auth.rstrip("\x00")
        self._desc = desc.rstrip("\x00")
        self._num_records = num_records
        self._masters = zip(mname, msize)

    def pack_data(self):
        out = ''
        # Pack HEDR subrecord
        data = (self._ver, self._ftype, self._auth, self._desc, self._num_records)
        out += self.pack_subrecord("HEDR", data, "fi32s256si")

        # Pack the masters list
        for master, size in self._masters:
            out += self.pack_subrecord("MAST", master, "%ds" % (len(master) + 1))
            out += self.pack_subrecord("DATA", size, "l")

        return out

    @property
    def author(self):
        return self._auth

    @property
    def desc(self):
        return self._desc

    @property
    def version(self):
        return self._ver

    @property
    def record_count(self):
        return self._num_records

    @property
    def masters(self):
        return self._masters

    @record_count.setter
    def record_count(self, num):
        self._num_records = num
        self._changed = True

    def add_master(self, path):
        """Add a master to the dependencies list.

        :path: (str) Path to the master file.
        """
        if self._ftype != 0:
            raise ValueError("Only esp plugins can have masters")

        name = os.path.basename(path)
        size = os.path.getsize(path)

        self._masters.append((name, size))

        self._changed = True
