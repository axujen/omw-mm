# Contains the Esm class that describes morrowinds esm/esp files.
from StringIO import StringIO
from struct import unpack
from collections import OrderedDict


class Esm(object):
    def __init__(self, path):
        self._path = path
        self.records = None

    def append(self, *args, **kwargs):
        return self.records.append(*args, **kwargs)

    def remove(self, *args, **kwargs):
        return self.records.remove(*args, **kwargs)

    def find_records(self, name):
        """Search for a record by name.

        :name: (str) Name of the record to search for
        :returns: (list) list of matched records
        """

        records = []
        if not self.records:
            return records

        for record in self.records:
            if record["HEADER"] == name:
                records.append(record)

        return records

    def read(self):
        """Parse the file into a list of records, containing a sublist of subrecords.

        :fh: (file) File object of the plugin
        """
        with open(self._path, "rb") as fh:
            end = len(fh.read())
            records = []
            fh.seek(0)
            while not fh.tell() == end:  # Because python doesn't support EOF
                # Record
                rheader = fh.read(4)
                rsize = fh.read(4)  # 4 bit int
                empty = fh.read(4)  # Unknown/Useless value. Stored for writing
                rflags = fh.read(4)  # 4 bit int
                # Data
                rdata = fh.read(unpack("i", rsize)[0])

                # Parse record data into subrecords.
                # Perhaps this should have its own function though
                raw_data = StringIO(rdata)
                subrecords = []
                while not raw_data.tell() == unpack("i", rsize)[0]:
                    sheader = raw_data.read(4)
                    ssize = raw_data.read(4)
                    sdata = raw_data.read(unpack("i", ssize)[0])

                    subrecord = OrderedDict()
                    subrecord["HEADER"] = sheader
                    subrecord["SIZE"] = ssize
                    subrecord["DATA"] = sdata
                    subrecords.append(subrecord)

                record = OrderedDict()
                record["HEADER"] = rheader
                record["SIZE"] = rsize
                record["EMPTY"] = empty
                record["FLAGS"] = rflags
                record["DATA"] = rdata
                record["SUBRECORDS"] = subrecords
                records.append(record)

            self.records = records

    def write(self, path=None):
        """Write to disk back from self.entries.

        :path: (str) Path to file to write to, Default: self._path
        """
        out = StringIO()
        for record in self.records:
            for key in record.keys()[:-1]:  # -1 because of subrecords
                out.write(record[key])

        if not path:
            path = self.path

        out.seek(0)
        with open(path, "w") as fh:
            fh.write(out.getvalue())
