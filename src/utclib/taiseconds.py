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


# first colums in second elsapsed since TAI sart epoch, second colum is TAI - UTC in seconds
LEAP_SEC_TAB =  [[ 441763200, 10]  # 1972   1    1 UTC 
                ,[ 457488010, 11]  # 1972   7    1 UTC 
                ,[ 473385611, 12]  # 1973   1    1 UTC 
                ,[ 504921612, 13]  # 1974   1    1 UTC 
                ,[ 536457613, 14]  # 1975   1    1 UTC 
                ,[ 567993614, 15]  # 1976   1    1 UTC 
                ,[ 599616015, 16]  # 1977   1    1 UTC 
                ,[ 631152016, 17]  # 1978   1    1 UTC 
                ,[ 662688017, 18]  # 1979   1    1 UTC 
                ,[ 694224018, 19]  # 1980   1    1 UTC 
                ,[ 741484819, 20]  # 1981   7    1 UTC 
                ,[ 773020820, 21]  # 1982   7    1 UTC 
                ,[ 804556821, 22]  # 1983   7    1 UTC 
                ,[ 867715222, 23]  # 1985   7    1 UTC 
                ,[ 946684823, 24]  # 1988   1    1 UTC 
                ,[1009843224, 25]  # 1990   1    1 UTC 
                ,[1041379225, 26]  # 1991   1    1 UTC 
                ,[1088640026, 27]  # 1992   7    1 UTC 
                ,[1120176027, 28]  # 1993   7    1 UTC 
                ,[1151712028, 29]  # 1994   7    1 UTC 
                ,[1199145629, 30]  # 1996   1    1 UTC 
                ,[1246406430, 31]  # 1997   7    1 UTC 
                ,[1293840031, 32]  # 1999   1    1 UTC 
                ,[1514764832, 33]  # 2006   1    1 UTC 
                ,[1609459233, 34]  # 2009   1    1 UTC 
                ,[1719792034, 35]  # 2012   7    1 UTC 
                ,[1814400035, 36]  # 2015   7    1 UTC 
                ,[1861920036, 37]] # 2017   1    1 UTC 
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
        self.CAL_TAI0 = [1958, 1, 1, 0, 0, 0]                                         
     
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
    
    def getMJD(self):
        """ get the MJD
        Parameters
        ----------

        Output
        ----------
        mjd : numpy array (nx1) float64 MJDS
            
            
        WARNING : leap seconds not still implemented -> it is just for testing and will produce incorrect results!!!!!
        
        
        """
        return float(self.tai_seconds[:,0])/86400+float(self.tai_seconds[:,1])/1e16 + self.MJD_TAI0 
    def getIntMJDSOD(self):
        """ get the MJD
        Parameters
        ----------

        Output
        ----------
        mjd_sod : (numpy array, numpyarray) int64 MJDS and second of the day
            
            
        WARNING : leap seconds not still implemented -> it is just for testing and will produce incorrect results!!!!!
        
        
        """
        sod = np.int64(np.remainder(self.tai_seconds[:,0],86400)) + np.int64(np.round(self.tai_seconds[:,1]/1e16))
        mjd = np.int64(np.floor(self.tai_seconds[:,0]/86400)) +  self.MJD_TAI0 
        mjd[sod == 86400] += 1
        sod[sod == 86400] = 0
        return (mjd, sod)