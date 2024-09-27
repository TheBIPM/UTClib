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
        self.CAL_TAI0 = [1958, 1, 1, 0, 0, 0]
        self.DATETIME64_TAI0 = np.datetime64('1958-01-01')
        self.UNIX_TAI0 = -378691200    
        # first colums in second elsapsed since TAI start epoch, second could is the number of non leap secons elapsed , third colum is TAI - UTC in seconds
        self.LEAP_SEC_TAB = np.array( [[ 441763200,  441763190, 10]   # 1972   1    1 UTC 
                                      ,[ 457488010,  457487999, 11]   # 1972   7    1 UTC 
                                      ,[ 473385611,  473385599, 12]   # 1973   1    1 UTC 
                                      ,[ 504921612,  504921599, 13]   # 1974   1    1 UTC 
                                      ,[ 536457613,  536457599, 14]   # 1975   1    1 UTC 
                                      ,[ 567993614,  567993599, 15]   # 1976   1    1 UTC 
                                      ,[ 599616015,  599615999, 16]   # 1977   1    1 UTC 
                                      ,[ 631152016,  631151999, 17]   # 1978   1    1 UTC 
                                      ,[ 662688017,  662687999, 18]   # 1979   1    1 UTC 
                                      ,[ 694224018,  694223999, 19]   # 1980   1    1 UTC 
                                      ,[ 741484819,  741484799, 20]   # 1981   7    1 UTC 
                                      ,[ 773020820,  773020799, 21]   # 1982   7    1 UTC 
                                      ,[ 804556821,  804556799, 22]   # 1983   7    1 UTC 
                                      ,[ 867715222,  867715199, 23]   # 1985   7    1 UTC 
                                      ,[ 946684823,  946684799, 24]   # 1988   1    1 UTC 
                                      ,[1009843224, 1009843199, 25]   # 1990   1    1 UTC 
                                      ,[1041379225, 1041379199, 26]   # 1991   1    1 UTC 
                                      ,[1088640026, 1088639999, 27]   # 1992   7    1 UTC 
                                      ,[1120176027, 1120175999, 28]   # 1993   7    1 UTC 
                                      ,[1151712028, 1151711999, 29]   # 1994   7    1 UTC 
                                      ,[1199145629, 1199145599, 30]   # 1996   1    1 UTC 
                                      ,[1246406430, 1246406399, 31]   # 1997   7    1 UTC 
                                      ,[1293840031, 1293839999, 32]   # 1999   1    1 UTC 
                                      ,[1514764832, 1514764799, 33]   # 2006   1    1 UTC 
                                      ,[1609459233, 1609459199, 34]   # 2009   1    1 UTC 
                                      ,[1719792034, 1719791999, 35]   # 2012   7    1 UTC 
                                      ,[1814400035, 1814399999, 36]   # 2015   7    1 UTC 
                                      ,[1861920036, 1861919999, 37]]) # 2017   1    1 UTC                                    
     
    @classmethod                                              
    def fromMJD(self,mjd):
        """ createthe object from a numpy array of MJDs
        Parameters
        ----------
        mjd : numpy array (nx1)  MJDS
            
        """
        obj = self()
        obj.tai_seconds = np.zeros((len(mjd),2),np.int64)
        obj.tai_seconds[:,0] = np.floor((mjd - obj.MJD_TAI0)*86400)
        obj.tai_seconds[:,1] = np.round(np.remainder((mjd - obj.MJD_TAI0)*86400,1)*1e16)

        obj.applyLeapSecond()
        return obj

    @classmethod
    def fromUnixTime(self,unixsecond):
        """ createthe object from a numpy array of unix time 
        Parameters
        ----------
        unixsecond : numpy array (nx1) non leap second elapsed since 1 1 1970
            
        """
        obj = self()
        obj.tai_seconds = np.zeros((len(unixsecond),2),np.int64)
        obj.tai_seconds[:,0] = np.floor(unixsecond - obj.UNIX_TAI0)
        obj.tai_seconds[:,1] = np.round(np.remainder(unixsecond)*1e16)

        obj.applyLeapSecond()
        return obj


    @classmethod                                              
    def fromUTCCalendar(self,years,months,days,hours,minutes,seconds):
        """ createthe object from a numpy array of MJDs
        Parameters
        ----------
        calendar : numpy array (nx)
            
        """
        if years.shape[0] != months.shape[0] or years.shape[0] != days.shape[0] or years.shape[0] != hours.shape[0] or years.shape[0] != minutes.shape[0] or years.shape[0] != seconds.shape[0]:
            print("ERROR: imput array do not have the same shape ")
            return

        obj = self()

        idx_leap = seconds >= 60
        idx_not_leap = np.logical_not(idx_leap)
        seconds[idx_leap] -= 1

        frac_seconds = np.remainder(seconds)
        seconds = np.floor(seconds)

        # convert ot numpy datatime64
        milliseconds=None
        microseconds=None
        nanoseconds=None
        years = np.asarray(years) - 1970
        months = np.asarray(months) - 1
        days = np.asarray(days) - 1
        types = ('<M8[Y]', '<m8[M]', '<m8[D]', '<m8[W]', '<m8[h]','<m8[m]', '<m8[s]', '<m8[ms]', '<m8[us]', '<m8[ns]')
        vals = (years, months, days, weeks, hours, minutes, seconds, milliseconds, microseconds, nanoseconds)
        npdate = sum(np.asarray(v, dtype=t) for t, v in zip(types, vals) if v is not None)



        obj.tai_seconds = np.zeros((len(years),2),np.int64)
        timedelta = npdate - self.DATETIME64_TAI0
        obj.tai_seconds[:,0] = timedelta.astype('timedelta64[s]').astype(np.int64)
        obj.tai_seconds[:,1] = np.round(frac_seconds*1e16)



        obj.applyLeapSecond()

        obj.tai_seconds[idx_leap,0] += 1
        return obj

    def applyLeapSecond(self):
        """
        this function is used in the construction method after the input data are trated naively as if not leap second exist

        """
        min_taisec = np.min(self.tai_seconds[:,0])
        max_taisec = np.max(self.tai_seconds[:,0])

        if max_taisec < self.LEAP_SEC_TAB[0,1]:
            min_found = False
            for i in range(self.LEAP_SEC_TAB.shape[0]-1,-1,-1):
                if self.LEAP_SEC_TAB[i,1] < min_taisec:
                    if not(min_found):
                        min_found = True
                    else:
                        break
                if i == (self.LEAP_SEC_TAB.shape[0]-1):
                    self.tai_seconds[self.tai_seconds[:,0] > self.LEAP_SEC_TAB[i,1],0] += self.LEAP_SEC_TAB[i,2]
                else:
                    idx = np.logical_and(self.tai_seconds[:,0] > self.LEAP_SEC_TAB[i,1],self.tai_seconds[:,0] < self.LEAP_SEC_TAB[i+1,1])
                    self.tai_seconds[idx,0] += self.LEAP_SEC_TAB[i,2]
        else:
            if max_taisec > 0:
                print("WARNING: UTC TAI difference between 1 1 1958 and 1 1 1972 still nto supported")   
    
    def removeLeapSecond(self):
        """
        this function is used in the output method it is the "inverse" of the applyLeapSecond function.  it does not modify the object property since this a lossy operation (it can create two epochs with the same second count)
        """


        tai_sec = self.tai_seconds[:,0]
        min_taisec = np.min(tai_sec)
        max_taisec = np.max(tai_sec)

        count = 0

        for i in range(self.LEAP_SEC_TAB.shape[0]):
            if self.LEAP_SEC_TAB[i,0] > max_taisec:
                    break
            if i == (self.LEAP_SEC_TAB.shape[0]-1):
                tai_sec[tai_sec >= self.LEAP_SEC_TAB[i,0],0] -= self.LEAP_SEC_TAB[i,2]
                count += 1
            else:
                idx = np.logical_and(self.tai_seconds[:,0] >= self.LEAP_SEC_TAB[i,0],self.tai_seconds[:,0] < self.LEAP_SEC_TAB[i+1,0])
                self.tai_seconds[idx,0] -= self.LEAP_SEC_TAB[i,2]
                count += 1


        return tai_sec, count > 1

    
    def getMJD(self):
        """ get the MJD
        Parameters
        ----------

        Output
        ----------
        mjd : numpy array (nx1) float64 MJDS        
        
        """
        tai_sec, cross_leap = self.removeLeapSecond()
        if cross_leap:
            print('WARNING: leap second crossed, causality could be compromised')
        return float(tai_sec)/86400+float(self.tai_seconds[:,1])/1e16 + self.MJD_TAI0 

    def getIntMJDSOD(self):
        """ get the MJD
        Parameters
        ----------

        Output
        ----------
        mjd_sod : (numpy array, numpyarray) int64 MJDS and second of the day

        """
        tai_sec, cross_leap= self.removeLeapSecond()
        if cross_leap:
            print('WARNING: leap second crossed, causality could be compromised')
        sod = np.int64(np.remainder(tai_sec,86400)) + np.int64(np.round(self.tai_seconds[:,1]/1e16))
        mjd = np.int64(np.floor(tai_sec/86400)) +  self.MJD_TAI0 
        mjd[sod == 86400] += 1
        sod[sod == 86400] = 0
        return (mjd, sod)

    def getUnixTimeInt(self, disable_warn=False):
        """ get the MJD
        Parameters
        ----------

        Output
        ----------
        unixsec : numpy array (nx1) int64 unixseconds
        """
        tai_sec, cross_leap = self.removeLeapSecond()
        if cross_leap and not(disable_warn):
            print('WARNING: leap second crossed, causality could be compromised')
        return tai_sec + obj.UNIX_TAI0

    def isLeapSec(self):
        " get leaps second index"

        idx = np.full((self.tai_seconds.shape[0],1),False)
        for i in range(1,self.LEAP_SEC_TAB.shape[0]):
            idx = np.logical_or(idx,self.tai_seconds[:,0] == (self.LEAP_SEC_TAB[i,0]-1))
        return idx

    def getCalenadarDate(self):
        """ get the calendar date
        Parameters
        ----------

        Output
        ----------
        years     : numpy array (nx1) int64 
        months    : numpy array (nx1) int64 
        days      : numpy array (nx1) int64 
        hours     : numpy array (nx1) int64 
        minutes   : numpy array (nx1) int64 
        seconds   : numpy array (nx1) float64 
        """
        is_leap = self.isLeapSec()
        unixsec = self.getUnixTimeInt(True)
        dt = np.array(unixsec, dtype='datetime64[s]')
        years, months, days, hours, minutes, seconds = [dt.astype(f"M8[{x}]") for x in "YMDhms"]
        seconds = seconds + self.tai_seconds[:,1]/1e16

        seconds[is_leap] += 1

        return years, months, days, hours, minutes, seconds 
        