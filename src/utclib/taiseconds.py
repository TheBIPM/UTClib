"""
taiseconds  - A python class to store TAI timestamps unambigously and with high precision
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
import numpy as np


class taiseconds:
    """
    A class to store TAI timestamps unambigously and with high precision

    """
    def __init__(self):

        # HEADER
        self.tai_seconds = None                    #  nx 2 numpy int64 array:
                                                   #  first colums seconds sinc TAI origin 
                                                   #  fractional part of the second in attoseconds 1e-18s
        self.MJD_TAI0 = 36204                      # MJD of 1st Jan 1958 00h 00m 00s                                            
     
    @classmethod                                              
    def fromMJD(self,mjd):
        """ createthe object from a numpy array of MJDs
        Parameters
        ----------
        mjd : numpy array (nx1)
            MJDS
            
        WARNING : leap seconds not still implemented -> it is just for testing and will produce incorrect results!!!!!
        """
        obj = self()
        obj.tai_seconds = np.zeros((len(mjd),2),np.int64)
        obj.tai_seconds[:,0] = np.floor((mjd - obj.MJD_TAI0)*86400)
        obj.tai_seconds[:,1] = np.round(np.remainder((mjd - obj.MJD_TAI0)*86400,1)*1e16)
        
        return obj
        
        