"""
tfex  - A python class to read write manipulate tfex files
Copyright (C) 2024  Giulio Tagliaferro, Frédéric Meynadier

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""
import logging
import numpy as np
from operator import itemgetter
import re

from utclib.tabarray import tabarray
from utclib.taiseconds import taiseconds
from utclib.tabarray import tabarray
import utclib.tfexhdr as tfexhdr


# Regex for parsing format string
p = re.compile(r"(?P<fill>0?)(?P<width>\d+)\.?(?P<prec>\d*)(?P<type>[dfs])")
type_conv = {"d": np.int32,
             "f": np.float64,
             "s": str}

class tfex:
    """
    A class to read write and manipulate time or frequency link using the tfex format

    """
    def __init__(self):
        self.hdr = tfexhdr.tfexhdr()
        # DATA
        self.flags  = []        # List of poosible flags
        self.data   = None      # the data itself
        self.timestamps = None # time stamp of the data lines [obj of taiseconds]
        self.dtypes = []
        # List of [start, end] couples for fixed format reading/writing
        self.ranges = []

    def parse_dtypes(self):
        """ extract info from the COLUMNS header
        """
        try:
            col = self.hdr.COLUMNS
        except AttributeError:
            logging.error("No COLUMNS found in header")
        start = 0
        for c in sorted(col, key=itemgetter("id")):
            # Extract relevant info from format string
            m = p.search(c["format"])
            self.dtypes.append((c['label'], type_conv[m["type"]]))
            # update list of ranges for data reading
            self.ranges.append([start, start + int(m["width"])])
            start += int(m["width"]) + 1

    @classmethod
    def from_file(self,file_path):
        """create tfex object from file
        Parameters
        ----------
        file_path : str
            file path of the tfex file
        """
        tfex_obj = self()
        # First load header and parse the description of the columns
        tfex_obj.hdr.read(file_path)
        tfex_obj.parse_dtypes()
        # Now parse the data itself
        datacols = []
        for i in range(len(tfex_obj.dtypes)):
            datacols.append([])
        with open(file_path) as fp:
            linenum = 0
            for line in fp:
                linenum += 1
                if line[0] == "#":
                    continue
                if len(line) < tfex_obj.ranges[-1][-1]:
                    logging.warning("Line %d incomplete, skipping" % linenum)
                    continue
                # scan all values and store in separate lists
                for i in range(len(tfex_obj.dtypes)):
                    start, end = tfex_obj.ranges[i]
                    try:
                        # take correct field, don't cast yet
                        val = line[start:end]
                    except IndexError:
                        val = np.nan
                    datacols[i].append(val)

        # Allocate data array
        tfex_obj.data = tabarray(np.zeros((len(datacols[0]), ),
                                          dtype=tfex_obj.dtypes))
        # Fill data array, cast vectors
        for i in range(len(tfex_obj.dtypes)):
            tfex_obj.data[:, i] = tfex_obj.dtypes[i][1](datacols[i])

        # Timestamps : assume MJD / SoD input for now
        tfex_obj.timestamps = taiseconds.fromMJDSoD(
            tfex_obj.data['timetag_MJD'],
            tfex_obj.data['timetag_SoD'])
        return self


    def write_to_file(self,file_path):
        """write tfex object to file
        Parameters
        ----------
        file_path : str
            file path to which the tfex object is written
        """

        with open(file_path, "w") as fp:
            fp.write(self.hdr.write())

            format_string_data = ""
            format_string_timestamp = ""
            dtypes_timetag = []
            for col in self.colums:
                if 'timetag' not in col['type'] or 'secondary_timetag' in col['type']:
                    format_string_data += "%" + col['format'] +""
                else:
                    dtypes_timetag.append(("{}_{}".format(col['id'], col['type']), 'int'))
                    format_string_timestamp += "%" + col['format'] +""
            format_string_data += "\n"

            time_stamp = tabarray(np.zeros((len(self.data),), dtype=dtypes_timetag))
            (mjds,sod) = self.time_stamps.getIntMJDSOD();
            for i in range(len(dtypes_timetag)):
                if 'timetag_MJD' in dtypes_timetag[i][0]:
                    time_stamp[:,i] = mjds
                elif 'timetag_SoD' in dtypes_timetag[i][0]:
                    time_stamp[:,i] = sod
            data_string = ""

            #string field to be decoded
            decode_index = []
            for i in range(len(self.data.dtype)):
                if self.data.dtype[i].type is np.string_:
                    decode_index.append(i)


            for i in range(len(self.data)):
                dataline = list(self.data[i])
                for i in decode_index:
                    dataline[i] = dataline[i].decode() #otherwise it is formatted as b'....
                data_string += format_string_timestamp % tuple(time_stamp[i]) + format_string_data % tuple(dataline)

            of.write(data_string)
            of.close()

