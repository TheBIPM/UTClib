"""
tfex  - A python class to read write manipulate tfex files
Copyright (C) 2024  Giulio Tagliaferro, ....

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
import toml
import numpy as np
from tabarray import tabarray
from taiseconds import taiseconds

def parseFixedWithString(string,widths,types):
    lst = [[]]*len(widths)
    p = 0
    for i in range(len(widths)):
        if types[i] == 'd':
            lst[i] = int(string[p:(p+widths[i])])
            p += widths[i]
        elif types[i] == 's':
            lst[i] = string[p:(p+widths[i])]
            p += widths[i]  
        elif types[i] == 'f':
            lst[i] = float(string[p:(p+widths[i])])
            p += widths[i]  
    return tuple(lst)
        

class tfex:
    """
    A class to read write and manipulate time or frequency link using the tfex format

    """
    def __init__(self):

        # HEADER
        self.version = None                    #  Verison of the tfex format
        self.mjd_start = None                  #  First epoch of the link
        self.mjd_stop = None                   #  Last epoch of the link
        self.n_data = None                     #  Number of datapaoints in the link
        self.prefixes = []                     #  Prefixes definitions to be used (e.g. si digital framework)
        self.sampling_interval_s = None        #  Sampling interval of the link
        self.averagion_window_s = None         #  Averagin window generationg the data points 
        self.missing_epochs = None             #  Bool: given the nominal sampling rate are epoch skipped in the link
        self.author = None                     #  Author of the files
        self.date = None                       #  Creation date of the file
        self.refpoints = []                    #  List of refpoints to used to define the data values
        self.colums = []                       #  Column definition
        self.constant_delays = []              #  List of costant delays (e.g Calibrations) applied to the link
        self.comments = []                     #  Comments

        # DATA
        
        self.flags  = []                           # List of poosible flags 
        self.data   = None                         # the data itself
        self.time_stamps = None                     # time stamp of the data lines [obj of taiseconds]

    @classmethod
    def from_file(self,file_path):
        """create tfex object from file
        Parameters
        ----------
        file_path : str
            file path of the tfex file
        """
        tfex_obj = self()
        # read header 
        with open(file_path) as fp:
            line = fp.readline()
            header_lines = ''
            while line and line[0] == '#':
                header_lines = header_lines + line[1:] + '\n'
                line = fp.readline()
            lines = fp.readlines();
        lines.insert(0, line)
        header_data = toml.loads(header_lines)
        
        if 'TFEXVER' in header_data:
            tfex_obj.version = header_data['TFEXVER']
        
        if 'MJDSTART' in header_data:
            tfex_obj.mjd_start = header_data['MJDSTART']
        
        if 'MJDSTOP' in header_data:
            tfex_obj.mjd_stop = header_data['MJDSTOP']
        
        if 'NDATA' in header_data:
            tfex_obj.n_data = header_data['NDATA']
        
        if 'PREFIX' in header_data:
            tfex_obj.prefixes = header_data['PREFIX']
        
        if 'SAMPLING_INTERVAL_s' in header_data:
            tfex_obj.sampling_interval_s = header_data['SAMPLING_INTERVAL_s']
        
        if 'AVERAGING_WINDOW_s' in header_data:
            tfex_obj.averagion_window_s = header_data['AVERAGING_WINDOW_s']
        
        if 'MISSING_EPOCHS' in header_data:
            tfex_obj.missing_epochs = header_data['MISSING_EPOCHS']
            
        if 'AUTHOR' in header_data:
            tfex_obj.author = header_data['AUTHOR']
        
        if 'DATE' in header_data:
            tfex_obj.date = header_data['DATE']
        
        if 'REFPOINTS' in header_data:
            tfex_obj.refpoints = header_data['REFPOINTS']
            
        if 'COLUMNS' in header_data:
            tfex_obj.colums = header_data['COLUMNS']
        
        if 'CONSTANT_DELAYS' in header_data:
            tfex_obj.constant_delays = header_data['CONSTANT_DELAYS']
        
        if 'COMMENT' in header_data:
            tfex_obj.comments = header_data['COMMENT']
            
        dtypes_data = []
        dtypes_timetag = []
        
        widths = []
        f_types= []
        for col in tfex_obj.colums:
            if 'timetag' not in col['type'] or 'secondary_timetag' in col['type']:
                if 'd' in col['format']:
                    dtypes_data.append(("{}_{}".format(col['id'], col['type']), 'int'))
                    widths.append(int(col['format'][0:-1]))
                    f_types.append('d')
                elif 'f' in col['format']:
                    dtypes_data.append(("{}_{}".format(col['id'], col['type']), 'float'))
                    idxdec = col['format'].index('.')
                    idxf = col['format'].index('f')
                    widths.append(int(col['format'][0:min(idxdec,idxf)]))
                    f_types.append('f')
                elif 's' in col['format']:
                    dtypes_data.append(("{}_{}".format(col['id'], col['type']), 'S'+col['format'][:-1]))
                    widths.append(int(col['format'][0:-1]))
                    f_types.append('s')
                else:
                    raise Exception("format {} not recognized, aborting file read".format(col['format'])) 
            else:
                if 'd' in col['format']:
                    dtypes_timetag.append(("{}_{}".format(col['id'], col['type']), 'int'))
                    widths.append(int(col['format'][0:-1]))
                    f_types.append('d')
                elif 'f' in col['format']:
                    dtypes_timetag.append(("{}_{}".format(col['id'], col['type']), 'float'))
                    idxdec = col['format'].index('.')
                    idxf = col['format'].index('f')
                    widths.append(int(col['format'][0:min(idxdec,idxf)]))
                    f_types.append('f')
                    
        n_lines = len(lines)
        tfex_obj.data =  tabarray(np.zeros((n_lines,), dtype=dtypes_data))
        timetag = tabarray(np.zeros((n_lines,), dtype=dtypes_timetag))
        n_ttc = len(dtypes_timetag); #number of  time tag colums
        for i in range(len(lines)):
            data = parseFixedWithString(lines[i],widths,f_types);
            timetag[i] = data[0:n_ttc]
            tfex_obj.data[i] = data[n_ttc:]
        
        ## TODO -> warningns in case of loss of precision for floats
        
        
        ## TODO -> decide which timestamps are allowed in the format and manage them, for now just MJD and second of the day
        mjds = np.zeros((n_lines,), np.double);
        for i in range(len(dtypes_timetag)):
            if 'timetag_MJD' in dtypes_timetag[i][0]:
                mjds = mjds + timetag[:,i]
            elif 'timetag_SoD' in dtypes_timetag[i][0]:
                mjds = mjds + timetag[:,i].astype(np.float64)/86400
        
        tfex_obj.time_stamps = taiseconds.fromMJD(mjds)
        
        
        return tfex_obj
        
        
    def write(self,file_path):
        header_data = {
            "TFEXVER": self.version,
            "MJDSTART": self.mjd_start,
            "MJDSTOP": self.mjd_stop,
            "NDATA": self.n_data,
            "PREFIX": self.prefixes,
            "SAMPLING_INTERVAL_s": self.sampling_interval_s,
            "AVERAGING_WINDOW_s": self.averagion_window_s,
            "MISSING_EPOCHS": self.missing_epochs,
            "AUTHOR": self.author,
            "DATE": self.date,
            "REFPOINTS": self.refpoints,
            "COLUMNS": self.colums,
            "CONSTANT_DELAYS": self.constant_delays,
            "COMMENT": self.comments
            }
        
            
        return 0

