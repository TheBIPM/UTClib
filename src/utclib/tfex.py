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
import copy
from typing import Self
from warnings import warn

from utclib.tabarray import tabarray
from utclib.taiseconds import taiseconds
from utclib.tfexhdr import tfexhdr, UNITS

import allantools

# Regex for parsing format string
p = re.compile(r"(?P<fill>0?)(?P<width>\d+)\.?(?P<prec>\d*)(?P<type>[dfs])")
type_conv = {"d": np.int32,
             "f": np.float64,
             "s": str}

TFEX_VERSION = "0.0.1"

class tfex:
    """
    A class to read write and manipulate time or frequency link using the tfex format

    """
    def __init__(self):
        self.hdr = tfexhdr()
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
            self.dtypes.append((c["label"], type_conv[m["type"]]))
            # update list of ranges for data reading
            self.ranges.append([start, start + int(m["width"])])
            start += int(m["width"]) + 1
            if "timetag" in c and c["timetag"] is True:
                self.ttag_cols.append(i)
            else:
                self.data_cols.append(i)


    @classmethod
    def from_file(cls,file_path):
        """create tfex object from file
        Parameters
        ----------
        file_path : str
            file path of the tfex file
        """
        tfex_obj = cls()
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
                        if val[-1] == "*":
                            # add support for '*' in a int column
                            if tfex_obj.dtypes[i][1] == np.int32:
                                val = np.iinfo(np.int32).max
                            else:
                                val = np.nan
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
        tfex_obj.ingest_timetags(timetags)
        return tfex_obj


    @classmethod
    def from_arrays(cls, input_data: list):
        """create tfex object from existing numpy arrays
        Parameters
        ----------
        input_data : list of (np.array, metadata)
            a numpy list containing arrays and their metadata (COLUMNS dict
            content)
        """
        tfex_obj = cls()
        ndata = len(input_data[0][0])
        tfex_obj.hdr.TFEXVER = TFEX_VERSION
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
        tfex_obj.ingest_timetags(timetags)
        return tfex_obj

    def ingest_timetags(self, timetags):
        """ Take whatever timetags are input and set self.timestamps
        """

        cols = timetags.dtype.names

        # Timestamps : assume MJD / SoD input for now
        if 'MJD' in cols and 'SoD' in cols:
            self.timestamps = taiseconds.fromMJDSoD(
                timetags['MJD'],
                timetags['SoD'])
        else:
            logging.error(
                'Need MJD and SoD timetags, other methods not implemented yet')
            raise SystemExit


    def write_to_file(self,file_path):
        """ write tfex object to file
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
            if col['label'] == 'MJD':
                raw_cols.append(mjds.tolist())
            elif col['label'] == 'SoD':
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

    # TODO
    def interpolate(self, timestamps, cols=None):
        """ Return the columns, interpolated according to the requested array
        of timestamps

        Parameters
        ----------
        timestamps: utclib.taiseconds.taisseconds()
            A taiseconds object containing all timestamps
        cols: list
            List of columns labels to interpolate. If None, take all columns

        Returns
        utclib.tabarray()
        """
        # if cols is None:
        #     cols = self.data.dtype.names

        # ndata = len(timestamps)
        # data = tabarray(np.empty((ndata, ), dtype=dtypes_data))
        pass

    # TODO
    def align(self, tfex2, algo=None):
        """
        Align the tfex object with `tfex2` object using a chosen
        algorithm `algo` acting on the timetags
        """
        pass

    # TODO
    def join(self, tf2):
        """ add columns to the current tfex, taking values from tf2,
        interpolating data if needed"""

    def getDataCol(self, col: str|int):
        """ Return the array corresponding to the 
        requested data column `col` and either the index
        of `col` in the data property, or its name"""
        if type(col) == str:
            column_names = [c[0] for c in [self.dtypes[i] for i in self.data_cols]]
            if col in column_names:
                ic = column_names.index(col)
                return self.data[:,ic], ic
            else:
                raise ValueError(f'Column `{col}` not found.')
        elif type(col) == int:
            if col < len(self.data):
                col_name = self.dtypes[self.data_cols[col]][0]
                return self.data[:,col], col_name
            else:
                raise ValueError(f'Column index `{col}` out of bounds.')
        else:
            raise NotImplementedError()


    def setDataCol(self, col: str|int, data):
        """set `data` into the `col` column of the `data` property
        `col` can be column name or integer index"""
        if type(col) == str:
            column_names = [c[0] for c in [self.dtypes[i] for i in self.data_cols]]
            if col in column_names:
                ic = column_names.index(col)
                self.data[:,ic] = data
            else:
                raise ValueError(f'Column `{col}` not found.')
        elif type(col) == int:
            if col < len(self.data):
                self.data[:,col] = data
            else:
                raise ValueError(f'Column index `{col}` out of bounds.')
        else:
            raise NotImplementedError()



    def regularize(self):
        """ add missing epochs into tfex data
        if MISSING_EPOCHS flag is set then this will do nothing;
        if SAMPLING_INTERVAL_s flag is not set then the sampling
            rate will be inferred from the data
        
        return index of old data in newly regularized data"""

        MISSING_EPOCHS = getattr(self.hdr, 'MISSING_EPOCHS', None)
        if MISSING_EPOCHS:
            srate = getattr(self.hdr, 'SAMPLING_INTERVAL_s', None)
            idx1, idx2 = self.timestamps.regularizeSampling(srate)

            old_data = self.data.copy()
            self.data = tabarray.empty(len(self.timestamps),old_data.dtype)
            self.data[idx1] = old_data[idx2]
           
            setattr(self.hdr, 'MISSING_EPOCHS', False)
        else:
            idx1 = idx2 = []

        return (idx1,idx2)

    def movmean(self, col: str, wind: float, inplace=False):
        """
        Calculate the moving average of the column `col`
        in the tfex data with window length `wind` seconds.
        The window length will be truncated to an integer
        number of data sampling rate.
        Moving average is centered around the sample.
        Data will first be regularized to insert any possible
        gaps; if `inplace` then the tfex obj is modified and
        return None, otherwise return new tfex obj.
        NaNs will be ignored in the average computation of each window
        """
        
        if inplace:
            tf = self
        else:
            tf = self.copy()

        tf.regularize()

        arr, i = tf.getDataCol(col)
        srate = getattr(self.hdr, 'SAMPLING_INTERVAL_s', None)
        Nw = int(np.round(wind/srate))
        if Nw % 2 == 0: Nw += 1 # odd number of samples to perfectly put the current sample in the middle of the window
        # use convolution to perform moving average
        arr_filled = np.nan_to_num(arr, nan=0.0)
        valid_mask = (~np.isnan(arr)).astype(float)
        kernel = np.ones(Nw)
        rolling_sum = np.convolve(arr_filled, kernel, mode='same')
        rolling_count = np.convolve(valid_mask, kernel, mode='same')
        data_avg = rolling_sum / rolling_count
        tf.setDataCol(i, data_avg)
        setattr(tf.hdr, 'AVERAGING_WINDOW_s', wind)
        return (None if inplace else tf)

    #TODO
    @classmethod
    def diff(cls, tfex1: Self, tfex2: Self, col1: int|str = 0, col2: int|str = 0, align_on_right: bool = False, col_label=None):
        """
        Calculate `tfex1` MINUS `tfex2` on selected columns.
        By default:
        - First data column will be considered for both objs; otherwise specify `col1` and/or `col2`, by either column name or integer index.
        - Timestamps of `tfex1` is used as reference  (`align_on_right`=False), otherwise use that of `tfex2` (`align_on_right`=True). Linear interpolation is used to match the data of the other tfex on the reference tfex.
        - `col_label` if not set will be f'{label1}-{label2}' as the output data column. 
        If both column has the `trip` metadata, then merge these metadata.
        
        """

        # Retrieve the selected data column
        data1, c1 = tfex1.getDataCol(col1)
        data2, c2 = tfex2.getDataCol(col2)

        # Retrieve column metadata
        ic1 = c1 if type(col1)==str else col1
        data1_colspec = tfex1.hdr.COLUMNS[tfex1.data_cols[ic1]]
        ic2 = c2 if type(col2)==str else col2
        data2_colspec = tfex2.hdr.COLUMNS[tfex2.data_cols[ic2]]

        # Retrieve data unit to scale properly before making difference
        unit1 = data1_colspec['unit']
        unit2 = data2_colspec['unit']
        if (unit1 in UNITS['time']) and (unit2 in UNITS['time']):
            factor1 = UNITS['time'][unit1]['factor']
            factor2 = UNITS['time'][unit2]['factor']
        else:
            raise NotImplementedError('method is only used to calculate time difference')

        # Retrieve the timestamps in float TAI seconds
        ts1 = tfex1.timestamps.tai_seconds
        t1 = ts1[:,0] + ts1[:,1]/taiseconds.FRAC_MULTIPLIER
        ts2 = tfex2.timestamps.tai_seconds
        t2 = ts2[:,0] + ts2[:,1]/taiseconds.FRAC_MULTIPLIER

        # Interpolate 
        if align_on_right:
            xp = t1
            fp = data1
            x = t2
            data1_int = np.interp(x,xp,fp,left=np.nan,right=np.nan)
            data1 = data1_int
            factor_common = factor2
        else:
            xp = t2
            fp = data2
            x = t1
            data2_int = np.interp(x,xp,fp,left=np.nan,right=np.nan)
            data2 = data2_int
            factor_common = factor1

        # Difference
        data = (data1*factor1 - data2*factor2)/factor_common

        # Construct output tfex
        # get the data column metadata
        trip1 = data1_colspec.get('trip',[])
        trip2 = data2_colspec.get('trip',[])
        data_colspec = copy.deepcopy(data2_colspec) if align_on_right else copy.deepcopy(data1_colspec)
        # merge trip details
        if trip1 or trip2:
            data_colspec['trip'] = trip1 + trip2
        # determine column label
        if not col_label:
            col_label = f'{data1_colspec['label']}-{data2_colspec['label']}'
        data_colspec['label'] = col_label
        # get timestamps
        mjd_sod = tfex2.timestamps.getIntMJDSOD() if align_on_right else tfex1.timestamps.getIntMJDSOD()
        # make the tfex object from timestamps and data array
        #TODO here the format of SoD should be matching the resolution of the reference tfex
        tfex_out = tfex.from_arrays([
            (mjd_sod[0], dict(timetag=True, label='MJD', scale='TAI', unit = 'si:day', format='5d')),
            (mjd_sod[1], dict(timetag=True, label='SoD', scale='TAI', unit = 'si:second', format='8.3f')),
            (data, data_colspec)
        ])
        # merge any comments
        comment1 = getattr(tfex1.hdr,'COMMENT', '')
        comment2 = getattr(tfex2.hdr,'COMMENT', '')
        if comment1 and comment2:
            comment = comment1 + '\n' + comment2
        elif comment1:
            comment = comment1
        elif comment2:
            comment = comment2
        else:
            comment = None
        # merge refpoints
        refpoints1 = getattr(tfex1.hdr,'REFPOINTS',[])
        refpoints2 = getattr(tfex2.hdr,'REFPOINTS',[])
        if refpoints1 or refpoints2:
            refpoints = refpoints1 + refpoints2
        else:
            refpoints = None
        # merge constant_delays
        constantdelays1 = getattr(tfex1.hdr,'CONSTANT_DELAYS',[])
        constantdelays2 = getattr(tfex2.hdr,'CONSTANT_DELAYS',[])
        if constantdelays1 or constantdelays2:
            constantdelays = constantdelays1 + constantdelays2
        else:
            constantdelays = None
        # set extra metadata
        if comment:
            setattr(tfex_out.hdr, 'COMMENT', comment)
        if refpoints:
            setattr(tfex_out.hdr, 'REFPOINTS', refpoints)
        if constantdelays:
            setattr(tfex_out.hdr, 'CONSTANT_DELAYS', constantdelays)

        return tfex_out

    def adev(self, col: str|int = 0, **kwargs):
        """Wrapper on allantools.gradev for the data column `col` (column name or integer index).
        `kwargs`: other keywords argument to allantools.gradev other than `data` and `rate`, e.g. taus=...
        """
        # check sampling rate
        srate = getattr(self.hdr,'SAMPLING_INTERVAL_s', None)
        if not srate:
            raise NotImplementedError('No info on sampling rate.')
        # check data unit
        data, c = self.getDataCol(col)
        ic = c if type(col)==str else col
        data_colspec = self.hdr.COLUMNS[self.data_cols[ic]]
        unit = data_colspec['unit']
        if unit not in UNITS['time']:
            raise NotImplementedError('method is only used on phase time data')
        factor = UNITS['time'][unit]['factor']
        # preliminary check on number of points
        if self.data.shape[0] < 3:
            raise ValueError('not enough data')
        # regularize data just in case
        self.regularize()
        # extract requested data
        data,_ = self.getDataCol(col)
        return allantools.gradev(data=data*factor, rate=1/srate, **kwargs)

    def mdev(self, col: str|int = 0, **kwargs):
        """Wrapper on allantools.mdev for the data column `col` (column name or integer index).
        `kwargs`: other keywords argument to allantools.gradev other than `data` and `rate`, e.g. taus=...
        """
        # check sampling rate
        srate = getattr(self.hdr,'SAMPLING_INTERVAL_s', None)
        if not srate:
            raise NotImplementedError('No info on sampling rate.')
        # check data unit
        data, c = self.getDataCol(col)
        ic = c if type(col)==str else col
        data_colspec = self.hdr.COLUMNS[self.data_cols[ic]]
        unit = data_colspec['unit']
        if unit not in UNITS['time']:
            raise NotImplementedError('method is only used on phase time data')
        factor = UNITS['time'][unit]['factor']
        # preliminary check on number of points
        if self.data.shape[0] < 3:
            raise ValueError('not enough original data')
        # regularize data just in case
        self.regularize()
        # extract requested data
        data,_ = self.getDataCol(col)
        ts = self.timestamps.tai_seconds
        ts = ts[:,0] + ts[:,1]/taiseconds.FRAC_MULTIPLIER
        # find missing data and fill
        idx_nonnan = np.where(~np.isnan(data))[0]
        idx_nan = np.where(np.isnan(data))[0]
        if len(idx_nan)/data.shape[0] > 0.2:
            warn(r'more than 20% of data is missing')
        if idx_nan.any() and idx_nonnan.any():
            data[idx_nan] = np.interp(ts[idx_nan],ts[idx_nonnan],data[idx_nonnan],left=np.nan,right=np.nan)
            idx_nonnan = np.where(~np.isnan(data))[0]
            idx_nan = np.where(np.isnan(data))[0]
        if idx_nonnan.any():
            # trim nans from left and right
            data = data[idx_nonnan[0]:idx_nonnan[-1]+1]
            ts = ts[idx_nonnan[0]:idx_nonnan[-1]+1]
        if not data.size:
            raise ValueError('not enough data')

        return allantools.mdev(data=data*factor, rate=1/srate, **kwargs)
        
    def __str__(self):
        """ create string that represent tfex object
            in a tabular fashion
        """
        raw_cols = []
        # For now only support mjd/sod
        mjds, sods = self.timestamps.getIntMJDSOD()
        # store formats
        fmts = []
        for col in self.hdr.COLUMNS:
            if col['label'] == 'MJD':
                raw_cols.append(mjds.tolist())
            elif col['label'] == 'SoD':
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

        return "\n".join(data_output)

    def copy(self):
        """Make a deep copy of the current tfex obj"""
        new_tf = tfex()
        new_tf.hdr = copy.deepcopy(self.hdr)
        new_tf.flags  = copy.deepcopy(self.flags)
        new_tf.data   = copy.deepcopy(self.data)
        new_tf.timestamps = copy.deepcopy(self.timestamps)
        new_tf.dtypes = copy.deepcopy(self.dtypes)
        new_tf.ranges = copy.deepcopy(self.ranges)
        new_tf.data_cols = copy.deepcopy(self.data_cols)
        new_tf.ttag_cols = copy.deepcopy(self.ttag_cols)
        return new_tf