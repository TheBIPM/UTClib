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
import re

from utclib.tabarray import tabarray
from utclib.taiseconds import taiseconds
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
        # Content
        self.flags  = []        # List of possible flags
        self.data   = None      # tabarray object containing the data
        self.timestamps = None  # time stamp of the data lines [obj of taiseconds]
        self.dtypes = []        # dtypes for each columns
        # List of [start, end] couples for fixed format reading/writing
        self.ranges = []
        # List of columns indexes containing data (resp. timetags)
        self.data_cols = []
        self.ttag_cols = []

    def parse_dtypes(self):
        """ extract info from the COLUMNS header
        """
        try:
            col = self.hdr.COLUMNS
        except AttributeError:
            logging.error("No COLUMNS found in header")
        start = 0
        for i, c in enumerate(col):
            # Extract relevant info from format string
            m = p.search(c["format"])
            self.dtypes.append((c['label'], type_conv[m["type"]]))
            # update list of ranges for data reading
            self.ranges.append([start, start + int(m["width"])])
            start += int(m["width"]) + 1
            if 'timetag' in c["label"]:
                self.ttag_cols.append(i)
            else:
                self.data_cols.append(i)


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
        raw_cols = []
        for col in tfex_obj.hdr.COLUMNS:
            raw_cols.append([])
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
                    raw_cols[i].append(val)

        # Separate timetags from data
        dtypes_data = [tfex_obj.dtypes[i] for i in tfex_obj.data_cols]
        dtypes_timetags = [tfex_obj.dtypes[i] for i in tfex_obj.ttag_cols]

        # Allocate data arrays
        tfex_obj.data = tabarray(np.empty((len(raw_cols[0]), ),
                                          dtype=dtypes_data))
        timetags = tabarray(np.empty((len(raw_cols[0]), ),
                                      dtype=dtypes_timetags))
        # Fill data and timetags arrays, cast vectors
        # col = number of the column in raw_cols, i = number in category
        for i, col in enumerate(tfex_obj.data_cols):
            tfex_obj.data[:, i] = tfex_obj.dtypes[col][1](raw_cols[col])
        for i, col in enumerate(tfex_obj.ttag_cols):
            timetags[:, i] = tfex_obj.dtypes[col][1](raw_cols[col])

        # Timestamps : assume MJD / SoD input for now
        tfex_obj.timestamps = taiseconds.fromMJDSoD(
            timetags['timetag_MJD'],
            timetags['timetag_SoD'])
        return tfex_obj

    @classmethod
    def from_arrays(self, input_data: list):
        """create tfex object from existing numpy arrays
        Parameters
        ----------
        input_data : list of (np.array, metadata)
            a numpy list containing arrays and their metadata (COLUMNS dict
            content)
        """
        tfex_obj = self()
        ndata = len(input_data[0][0])
        tfex_obj.hdr.COLUMNS = []
        for arr, metadata in input_data:
            tfex_obj.hdr.COLUMNS.append(metadata)
            if len(arr) != ndata:
                logging.error("Input arrays should have the same size")
                raise SystemExit
        tfex_obj.parse_dtypes()

        # Separate timetags from data
        dtypes_data = [tfex_obj.dtypes[i] for i in tfex_obj.data_cols]
        dtypes_timetags = [tfex_obj.dtypes[i] for i in tfex_obj.ttag_cols]

        # Allocate data arrays
        tfex_obj.data = tabarray(np.empty((ndata, ), dtype=dtypes_data))
        timetags = tabarray(np.empty((ndata, ), dtype=dtypes_timetags))
        # Fill data and timetags arrays, cast vectors
        # col = number in input_data, i = number in category
        for i, col in enumerate(tfex_obj.data_cols):
            tfex_obj.data[:, i] = tfex_obj.dtypes[col][1](input_data[col][0])
        for i, col in enumerate(tfex_obj.ttag_cols):
            timetags[:, i] = tfex_obj.dtypes[col][1](input_data[col][0])

        # Timestamps : assume MJD / SoD input for now
        tfex_obj.timestamps = taiseconds.fromMJDSoD(
            timetags['timetag_MJD'],
            timetags['timetag_SoD'])
        return tfex_obj


    def write_to_file(self,file_path):
        """write tfex object to file
        Parameters
        ----------
        file_path : str
            file path to which the tfex object is written
        """
        raw_cols = []
        # For now only support mjd/sod
        mjds, sods = self.timestamps.getIntMJDSOD()
        # store formats
        fmts = []
        for col in self.hdr.COLUMNS:
            if col['label'] == 'timetag_MJD':
                raw_cols.append(mjds.tolist())
            elif col['label'] == 'timetag_SoD':
                raw_cols.append(sods.tolist())
            else:
                raw_cols.append(self.data[col['label']].tolist())
            fmts.append("{:" + col['format'] + "} ")
        data_output = []
        for i in range(len(raw_cols[0])):
            line = ""
            for j, col in enumerate(self.dtypes):
                line += fmts[j].format(raw_cols[j][i])
            data_output.append(line)

        # Write to output
        with open(file_path, "w") as fp:
            fp.write(self.hdr.write() + "\n")
            fp.write("\n".join(data_output))

