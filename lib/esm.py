# Contains the Esm class that describes morrowinds esm/esp files.
from StringIO import StringIO
from struct import unpack, pack


class Esm(object):
    def __init__(self, path):
        """This class describes a morrowind esm/esp file.

        :path: (str) Path to the file.
        """
        self._path = path
        self._records = []

    def find_records(self, id):
        """Search for a record by id.

        :id: (str) id of the record to search for
        :returns: (list) list of matched records
        """
        records = []
        for record in self._records:
            if record.get_id() == id:
                records.append(record)

        return records

    def parse_records(self):
        """Parse the file into a list of records, containing a sublist of subrecords.

        :data: (str) The plugins data.
        """
        with open(self._path, "r") as fh:
            EOF = len(fh.read())
            fh.seek(0)
            records = []
            while not fh.tell() == EOF:  # Because python doesn't support EOF
                # Record
                header = fh.read(16)
                id, size, delflag, recflag = self.unpack_record_header(header)
                data = fh.read(size)
                if id in ("LEVC", "LEVI"):
                    record = EsmLEVRecord(id, size, delflag, recflag, data)
                else:
                    record = EsmRecord(id, size, delflag, recflag, data)
                records.append(record)

        self._records = records

    def write(self, path=None):
        """Write the contents of the Esm to a file.

        :path: (str) Path to the file. Default: self.path
        """
        if not path:
            path = self.path

        with open(path, "wb") as handle:
            for record in self.get_records():
                handle.write(record.pack())

    def unpack_record_header(self, header):
        """Unpack the header of a record

        :header: (str) Must be exactly 16 bytes
        :returns: (set) id, size, delflag?, recflag?
        """
        if not isinstance(header, str):
            raise ValueError("unpack_header expects a string argument" % header)
        if not len(header) == 16:
            raise ValueError("Header must be 16 bytes long exactly, got %s" % header)

        return unpack("4s3i", header)

    def get_records(self):
        return self._records

    def merge_with(self, other):
        """Merge leveled lists from another esm with this one.

        :other: (Esm) esm instance to be merged with this.
        :returns: (set) (diff, num_diff) diff is a dictionary of changed and merged lists, num_diff is the number of changes.
        """
        if not isinstance(other, Esm):
            raise ValueError("Expecting Esm object, got %s" % other)

        diff = {}
        num_diff = 0
        for rec in ("LEVC", "LEVI"):
            diff[rec] = {"Merged": {}, "Added": {}}
            my_records = {r._name: r for r in self.find_records(rec)}
            other_records = {r._name: r for r in other.find_records(rec)}
            for id, record in other_records.items():
                if id not in my_records:
                    my_records[id] = record
                    diff[rec]["Added"][id] = my_records[id]
                else:
                    my_records[id].merge_with(record)
                    diff[rec]["Merged"][id] = my_records[id]

            # Replace the old records with the new merged ones:
            for index, record in enumerate(self.get_records()):
                if record.get_id() == rec:
                    if record._name in diff[rec]["Merged"]:
                        self._records[index] = diff[rec]["Merged"][record._name]

            # Add the new records (to the bottom of the file?)
            for _, record in diff[rec]["Added"].items():
                self._records.append(record)

            num_diff += len(diff[rec]["Merged"]) + len(diff[rec]["Added"])

        return (diff, num_diff)


class EsmRecord(object):
    """Describes a esm record"""

    def __init__(self, id, size, delflag, recflag, data):
        """Takes a record id size flags and its raw data, parses the data into subrecords.

        :id: (str) id of the record.
        :size: (int) Size of the data of the record.
        :data: (str) Raw binary data of the record.
        """
        self._id, self._size, self._data = id, size, data
        self._delflag, self._recflag = delflag, recflag
        self._subrecords = self.unpack_subrecords(data)
        self._changed = False

    def get_id(self):
        return self._id

    def get_size(self):
        if self._changed:
            self._size = len(self.get_data())

        return self._size

    def get_data(self):
        if self._changed:
            self._data = self.pack_subrecords()
            self._changed = False

        return self._data

    def get_subrecords(self):
        return self._subrecords

    def unpack_subrecords(self, data):
        """Unpack the data of a record into subrecords.

        :data: (str) Records data
        :returns: (list) List of subrecords
        """
        subrecords = []
        stream = StringIO(data)
        EOF = len(data)
        while not stream.tell() == EOF:
            header = stream.read(8)
            id, size = self.unpack_subrecord_header(header)
            data = stream.read(size)
            subrecords.append(EsmSubrecord(id, size, data))
        return subrecords

    def unpack_subrecord_header(self, header):
        """Unpack the header of a subrecord

        :header: (str) Must be exactly 8 bytes
        :returns: (set) id, size
        """
        if not isinstance(header, str):
            raise ValueError("unpack_header expects a string argument" % header)
        if not len(header) == 8:
            raise ValueError("Header must be 16 bytes long exactly, got %s" % header)

        return unpack("4si", header)

    def pack_header(self):
        """Convert the records header back into binary format.

        :returns: (str)
        """
        return pack("4s3i", self.get_id(), self.get_size(), self._delflag, self._recflag)

    def pack_subrecords(self):
        """Convert the records subrecords back into binary format.
        The output should equivalent to self._data

        :return: (str)
        """
        out = ''
        for sub in self.get_subrecords():
            out += sub.pack()

        return out

    # This class does not modify its records.
    def pack(self):
        """Convert the record back to binary format.

        :returns: (str)
        """
        packed = ''

        # Pack the header
        packed += self.pack_header()

        # Pack data
        packed += self.get_data()

        return packed


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

    def get_id(self):
        return self._id

    def get_size(self):
        return self._size

    def get_data(self):
        return self._data

    def pack_header(self):
        """Convert the subrecord header back to binary format.

        :returns: (str)
        """
        return pack("4si", self.get_id(), self.get_size())

    def pack(self):
        """Convert the subrecord to binary format.

        :returns: (str)
        """
        packed = ''

        # Write the header
        packed += self.pack_header()

        # Write the data
        packed += self.get_data()

        return packed


class EsmLEVRecord(EsmRecord):
    """Leveled Items/Creatures Record."""

    def __init__(self, *args, **kwargs):
        """See EsmRecord for arguments."""
        super(EsmLEVRecord, self).__init__(*args, **kwargs)
        self.unpack_sub_data(self.get_subrecords())

    def unpack_sub_data(self, subrecords):
        """Unpack the subrecords into meaningfull values.

        :subrecords: (list) List of subrecords to be unpacked.
        """
        self._objects = []
        for sub in subrecords:
            # List ID
            if sub.get_id() == "NAME":
                self._name = sub.get_data()

            # List specific flags
            elif sub.get_id() == "DATA":
                self._calc_all_levels = False
                self._calc_all_items = False
                flag = unpack("i", sub.get_data())
                # Verify the correct value of these flags.
                # wrye mash uses 1: for all_items and 2: for all_levels
                # while every other source on the esm format says the opposite
                # Note: openmw-cs also uses the same values as wrye mash.
                if self.get_id() == "LEVI":
                    if flag == 1:
                        self._calc_all_items = True
                    elif flag == 2:
                        self._calc_all_levels = True
                    elif flag == 3:
                        self._calc_all_items = self._calc_all_levels = True
                elif self.get_id() == "LEVC":
                    if flag == 1:
                        self._calc_all_levels = True
            # Chance None
            elif sub.get_id() == "NNAM":
                self._chance_none = unpack("B", sub.get_data())[0]

            # Number of creatures/items in the list
            elif sub.get_id() == "INDX":
                self._count = unpack("i", sub.get_data())[0]

            # Creatue/Item ID
            elif sub.get_id() == "CNAM" or sub.get_id() == "INAM":
                object_id = sub.get_data()

            # PC Level for the object
            elif sub.get_id() == "INTV":
                pc_level = unpack("h", sub.get_data())[0]
                self._objects.append((pc_level, object_id))
            # Unknown
            else:
                raise ValueError("Unknown subrecord %s" % sub.get_id())

    def merge_with(self, other):
        """Merge this leveled list with another list.

        :other: (EsmLEVRecord)
        """
        if not isinstance(other, EsmLEVRecord):
            raise ValueError("Cannot merge leveled list record with %s" % other)

        if not self.get_id() == other.get_id():
            raise ValueError("Cannot merge records %s and %s" % (self.get_id(), other.get_id()))

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

    def pack_sub(self, id, data, data_format=None):
        if not data_format:
            data_format = "%ds" % len(data)

        packed_data = pack(data_format, data)
        out = pack("4si", id, len(packed_data))
        out += packed_data
        return out

    def pack_subrecords(self):
        out = ''
        out += self.pack_sub("NAME", self._name)
        # List specific flags
        if self.get_id() == "LEVC":
            flag = 1 * self._calc_all_levels
            otype = "CNAM"
        else:
            flag = 1 * self._calc_all_items + 2 * self._calc_all_levels
            otype = "INAM"
        out += self.pack_sub("DATA", flag, "i")

        # Chance None
        out += self.pack_sub("NNAM", self._chance_none, "B")

        # Count
        out += self.pack_sub("INDX", self._count, "i")

        # Objects
        for lvl, obj in self._objects:
            out += self.pack_sub(otype, obj)
            out += self.pack_sub("INTV", lvl, "h")

        return out
