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
    FRAC_MULTIPLIER = 1e16
    MJD_TAI0 = 36204                      # MJD of 1st Jan 1958 00h 00m 00s
    CAL_TAI0 = [1958, 1, 1, 0, 0, 0]
    DATETIME64_TAI0 = np.datetime64('1958-01-01')
    UNIX_TAI0 = -378691200
    TAISEC_GPS0 = 694656019
    TAISEC_BDS0 = 1514764833
    TAISEC_GAL0 = 1313971219
    # first colums in second elsapsed since TAI start epoch, second could is the number of non leap secons elapsed , third colum is TAI - UTC in seconds after that date
    LEAP_SEC_TAB = np.array( [[ 441763210, 10]   # 1972   1    1 UTC
                             ,[ 457488011, 11]   # 1972   7    1 UTC
                             ,[ 473385612, 12]   # 1973   1    1 UTC
                             ,[ 504921613, 13]   # 1974   1    1 UTC
                             ,[ 536457614, 14]   # 1975   1    1 UTC
                             ,[ 567993615, 15]   # 1976   1    1 UTC
                             ,[ 599616016, 16]   # 1977   1    1 UTC
                             ,[ 631152017, 17]   # 1978   1    1 UTC
                             ,[ 662688018, 18]   # 1979   1    1 UTC
                             ,[ 694224019, 19]   # 1980   1    1 UTC
                             ,[ 741484820, 20]   # 1981   7    1 UTC
                             ,[ 773020821, 21]   # 1982   7    1 UTC
                             ,[ 804556822, 22]   # 1983   7    1 UTC
                             ,[ 867715223, 23]   # 1985   7    1 UTC
                             ,[ 946684824, 24]   # 1988   1    1 UTC
                             ,[1009843225, 25]   # 1990   1    1 UTC
                             ,[1041379226, 26]   # 1991   1    1 UTC
                             ,[1088640027, 27]   # 1992   7    1 UTC
                             ,[1120176028, 28]   # 1993   7    1 UTC
                             ,[1151712029, 29]   # 1994   7    1 UTC
                             ,[1199145630, 30]   # 1996   1    1 UTC
                             ,[1246406431, 31]   # 1997   7    1 UTC
                             ,[1293840032, 32]   # 1999   1    1 UTC
                             ,[1514764833, 33]   # 2006   1    1 UTC
                             ,[1609459234, 34]   # 2009   1    1 UTC
                             ,[1719792035, 35]   # 2012   7    1 UTC
                             ,[1814400036, 36]   # 2015   7    1 UTC
                             ,[1861920037, 37]]) # 2017   1    1 UTC
    def __init__(self):

        # HEADER
        self.tai_seconds = None                    #  nx 2 numpy int64 array:
                                                   #  first colums seconds sinc TAI origin
                                                   #  fractional part of the second in attoseconds 1e-18s


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
        obj.tai_seconds[:,1] = np.round(np.remainder((mjd - obj.MJD_TAI0)*86400,1)*self.FRAC_MULTIPLIER)

        obj.applyLeapSecond()
        return obj
    
    @classmethod
    def fromBesselianDate(self,bess_date):
        """ createthe object from a numpy array of besselian date
        
        see: https://maia.usno.navy.mil/information/eo-values
        Parameters
        ----------
        bess_date : numpy array (nx1)  besselian dates

        """
        obj = self()
        mjd = (bess_date - 2000)*365.2422 + 51544.03
        obj.tai_seconds = np.zeros((len(mjd),2),np.int64)
        obj.tai_seconds[:,0] = np.floor((mjd - obj.MJD_TAI0)*86400)
        obj.tai_seconds[:,1] = np.round(np.remainder((mjd - obj.MJD_TAI0)*86400,1)*self.FRAC_MULTIPLIER)

        obj.applyLeapSecond()
        return obj
    @classmethod
    def fromMJDSoD(self, mjd, sod):
        """ create the object from a numpy array of MJDs + numpy array of Sod
        Parameters
        ----------
        mjd : numpy array (nx1)  MJDS
        sod : numpy array (nx1)  Second of days

        """
        obj = self()
        obj.tai_seconds = np.zeros((len(mjd),2),np.int64)
        obj.tai_seconds[:,0] = (np.floor((mjd - obj.MJD_TAI0)*86400) +
                                np.floor(sod))
        obj.tai_seconds[:,1] = np.round((sod%1)*self.FRAC_MULTIPLIER)

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
        obj.tai_seconds[:,1] = np.round(np.remainder(unixsecond,1)*self.FRAC_MULTIPLIER)

        obj.applyLeapSecond()
        return obj


    @classmethod
    def fromUTCCalendar(self,years,months,days,hours,minutes,seconds):
        """ createthe object from a numpy array of MJDs
        Parameters
        ----------
        years   : numpy array (nx)
        months  : numpy array (nx)
        days    : numpy array (nx)
        hours   : numpy array (nx)
        minutes : numpy array (nx)
        seconds : numpy array (nx)

        """
        if isinstance(years, np.ndarray) and isinstance(months, np.ndarray) and isinstance(days, np.ndarray) and isinstance(hours, np.ndarray) and isinstance(minutes, np.ndarray) and isinstance(seconds, np.ndarray):
            if years.shape[0] != months.shape[0] or years.shape[0] != days.shape[0] or years.shape[0] != hours.shape[0] or years.shape[0] != minutes.shape[0] or years.shape[0] != seconds.shape[0]:
                print("ERROR: imput array do not have the same shape ")
                return
        #else:
        #    if type(years) != type(months) or type(years) != type(days) or type(years) != type(hours) or type(years) != type(minutes) or type(years) != type(seconds):
        #        print("ERROR: imput array do not have the same type ")
        #       return


        obj = self()
        seconds = np.asarray(seconds)

        idx_leap = seconds >= 60
        idx_not_leap = np.logical_not(idx_leap)
        seconds[idx_leap] -= 1

        frac_seconds = np.remainder(seconds,1)
        seconds = np.floor(seconds)

        # convert ot numpy datatime64
        milliseconds=None
        microseconds=None
        nanoseconds=None
        years = np.asarray(years) - 1970
        months = np.asarray(months) - 1
        days = np.asarray(days) - 1
        types = ('<M8[Y]', '<m8[M]', '<m8[D]', '<m8[h]','<m8[m]', '<m8[s]', '<m8[ms]', '<m8[us]', '<m8[ns]')
        vals = (years, months, days, hours, minutes, seconds, milliseconds, microseconds, nanoseconds)
        npdate = sum(np.asarray(v, dtype=t) for t, v in zip(types, vals) if v is not None)



        obj.tai_seconds = np.zeros((years.size,2),np.int64)
        timedelta = npdate - obj.DATETIME64_TAI0
        obj.tai_seconds[:,0] = timedelta.astype('timedelta64[s]').astype(np.int64)
        obj.tai_seconds[:,1] = np.round(frac_seconds*self.FRAC_MULTIPLIER)



        obj.applyLeapSecond()

        obj.tai_seconds[idx_leap,0] += 1
        return obj

    @classmethod
    def fromGPSWeekSow(self,week,sow):
        """ createthe object from a numpy array of MJDs
        Parameters
        ----------
        week   : numpy array (nx)
        sow  : numpy array (nx) second of the week

        """
        obj = self()
        week = np.asarray(week)
        sow = np.asarray(sow)
        nep = week.size

        obj.tai_seconds = np.zeros((nep,2),np.int64)
        obj.tai_seconds[:,0] = self.TAISEC_GPS0 + week.astype(np.int64)*86400*7 + np.floor(sow).astype(np.int64)
        obj.tai_seconds[:,1] = (np.remainder(sow,1)*self.FRAC_MULTIPLIER).astype(np.int64)

        return obj

    @classmethod
    def fromGALWeekSow(self,week,sow):
        """ createthe object from a numpy array of MJDs
        Parameters
        ----------
        week   : numpy array (nx)
        sow  : numpy array (nx) second of the week

        """
        obj = self()
        week = np.asarray(week)
        sow = np.asarray(sow)
        nep = week.size

        obj.tai_seconds = np.zeros((nep,2),np.int64)
        obj.tai_seconds[:,0] = self.TAISEC_GAL0 + week.astype(np.int64)*86400*7 + np.floor(sow).astype(np.int64)
        obj.tai_seconds[:,1] = (np.remainder(sow,1)*self.FRAC_MULTIPLIER).astype(np.int64)

        return obj

    @classmethod
    def fromBDSWeekSow(self,week,sow):
        """ createthe object from a numpy array of MJDs
        Parameters
        ----------
        week   : numpy array (nx)
        sow  : numpy array (nx) second of the week

        """
        obj = self()
        week = np.asarray(week)
        sow = np.asarray(sow)
        nep = week.size

        obj.tai_seconds = np.zeros((nep,2),np.int64)
        obj.tai_seconds[:,0] = self.TAISEC_BDS0 + week.astype(np.int64)*86400*7 + np.floor(sow).astype(np.int64)
        obj.tai_seconds[:,1] = (np.remainder(sow,1)*self.FRAC_MULTIPLIER).astype(np.int64)

        return obj




    def __getitem__(self, key):
        """
        this function allows the class to be index as an array. E.g. extraction 4 and 5 element of a taiseconds object (lest call it taisec) becomes taisec[[3,4]]
        """
        obj = taiseconds()
        obj.tai_seconds = self.tai_seconds[key,:]
        return obj


    def __setitem__(self, key, value):
        """
        this function allows the class to be index as an array. E.g. substituing epoch 4 and 5 of of a taiseconds object (lest call it taisec) with an other taisecond object (lets call it taisec2) becomes taisec[[3,4]] = taisec
        """
        self.tai_seconds[key,:] = value.tai_seconds



    def applyLeapSecond(self):
        """
        this function is used in the construction method after the input data are trated naively as if not leap second exist

        """
        min_taisec = np.min(self.tai_seconds[:,0])
        max_taisec = np.max(self.tai_seconds[:,0])

        leap_epoch_nls = self.LEAP_SEC_TAB[:,0] - self.LEAP_SEC_TAB[:,1] # leap second epoch in non leap second count
        if max_taisec > leap_epoch_nls[0]:
            min_found = False
            for i in range(self.LEAP_SEC_TAB.shape[0]-1,-1,-1):
                if leap_epoch_nls[i] < min_taisec:
                    if not(min_found):
                        min_found = True
                    else:
                        break
                if i == (self.LEAP_SEC_TAB.shape[0]-1):
                    self.tai_seconds[self.tai_seconds[:,0] >= leap_epoch_nls[i],0] += self.LEAP_SEC_TAB[i,1]
                else:
                    idx = np.logical_and(self.tai_seconds[:,0] >= leap_epoch_nls[i],self.tai_seconds[:,0] < leap_epoch_nls[i+1])
                    self.tai_seconds[idx,0] += self.LEAP_SEC_TAB[i,1]
        else:
            if max_taisec > 0:
                print("WARNING: UTC TAI difference between 1 1 1958 and 1 1 1972 still nto supported")

    def removeLeapSecond(self):
        """
        this function is used in the output method it is the "inverse" of the applyLeapSecond function.  it does not modify the object property since this a lossy operation (it can create two epochs with the same second count)
        """


        tai_sec = np.copy(self.tai_seconds[:,0])
        min_taisec = np.min(tai_sec)
        max_taisec = np.max(tai_sec)

        count = 0

        for i in range(self.LEAP_SEC_TAB.shape[0]):
            if self.LEAP_SEC_TAB[i,0] > max_taisec:
                    break
            if i == (self.LEAP_SEC_TAB.shape[0]-1):
                tai_sec[tai_sec >= self.LEAP_SEC_TAB[i,0]] -= self.LEAP_SEC_TAB[i,1]
                count += 1
            else:
                idx = np.logical_and(self.tai_seconds[:,0] >= self.LEAP_SEC_TAB[i,0],self.tai_seconds[:,0] < self.LEAP_SEC_TAB[i+1,0])
                tai_sec[idx] -= self.LEAP_SEC_TAB[i,1]
                count += 1
        # leap second can not be represented in a non lap second scale
        # IMPORTANT 1 : this is critical for converting back to calendar time
        # IMPORTANT 2 : this means that in unix time and MJD all leap second epochs are borught back to the previous second
        is_leap = self.isLeapSec()
        tai_sec[is_leap] -= 1



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
        return tai_sec.astype(np.float64)/86400+(self.tai_seconds[:,1]/self.FRAC_MULTIPLIER).astype(np.float64)/86400 + self.MJD_TAI0

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
        sod = np.int64(np.remainder(tai_sec,86400)) + np.int64(np.round(self.tai_seconds[:,1]/self.FRAC_MULTIPLIER))
        mjd = np.int64(np.floor(tai_sec/86400)) +  self.MJD_TAI0
        mjd[sod == 86400] += 1
        sod[sod == 86400] = 0
        return (mjd, sod)
    
    def getBesseliandate(self):
        """ get the Beseelian date
        Parameters
        ----------

        Output
        ----------
        mjd : numpy array (nx1) float64 besselian date

        """
        return  2000.000 + (self.getMJD() - 51544.03) / 365.2422

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
        return tai_sec + self.UNIX_TAI0

    def isLeapSec(self):
        " get leaps second index"

        idx = np.full((self.tai_seconds.shape[0],),False)
        for i in range(1,self.LEAP_SEC_TAB.shape[0]):
            idx = np.logical_or(idx,self.tai_seconds[:,0] == (self.LEAP_SEC_TAB[i,0]-1))
        return idx

    def getCalendarDate(self):
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
        # see https://stackoverflow.com/questions/13648774/get-year-month-or-day-from-numpy-datetime64
        Y, M, D, h, m, s = [dt.astype(f"M8[{x}]") for x in "YMDhms"]
        years = Y.astype(np.int64) + 1970
        months = (M - Y).astype(np.int64) + 1 # month
        days = (D - M).astype(np.int64) + 1 # day
        hours = (dt - D).astype("m8[h]").astype(np.int64) # hour
        minutes = (dt - h).astype("m8[m]").astype(np.int64) # minute
        seconds = (dt - m).astype("m8[s]").astype(np.int64) # second

        seconds = seconds + self.tai_seconds[:,1]/self.FRAC_MULTIPLIER

        seconds[is_leap] += 1

        return years, months, days, hours, minutes, seconds

    def getNPDateTime(self):
        """ get the calendar date
        Parameters
        ----------

        Output
        ----------
        dates     : numpy array (nx1) datetime64
        
        """
        years, months, days, hours, minutes, seconds = self.getCalendarDate()
        years = np.asarray(years) - 1970
        months = np.asarray(months) - 1
        days = np.asarray(days) - 1
        nanoseconds = np.round(np.remainder(seconds*1e6,1)*1e3)
        microseconds = np.floor(np.remainder(seconds*1e3,1)*1e3)
        milliseconds = np.floor(np.remainder(seconds,1)*1e3)
        seconds = np.floor(seconds)
        types = ('<M8[Y]', '<m8[M]', '<m8[D]', '<m8[h]','<m8[m]', '<m8[s]','<m8[ms]', '<m8[us]')#   '<m8[ns]')
        vals = (years, months, days, hours,minutes, seconds,milliseconds, microseconds)# nanoseconds)
        return sum(np.asarray(v, dtype=t) for t, v in zip(types, vals) if v is not None)


    def getGPSWeekSow(self):
        """ create the object from a numpy array of MJDs
        Returns
        ----------
        week   : numpy array (nx)
        sow  : numpy array (nx) second of the week

        """
        gpsec = self.tai_seconds[:,0] - self.TAISEC_GPS0

        week = np.floor(gpsec/(7*86400))
        sow  = np.remainder(gpsec,(7*86400)) + self.tai_seconds[:,1]/self.FRAC_MULTIPLIER

        return week,sow

    def getBDSWeekSow(self):
        """ create the object from a numpy array of MJDs
        Returns
        ----------
        week   : numpy array (nx)
        sow  : numpy array (nx) second of the week

        """
        bdsec = self.tai_seconds[:,0] - self.TAISEC_BDS0

        week = np.floor(bdsec/(7*86400))
        sow  = np.remainder(bdsec,(7*86400)) + self.tai_seconds[:,1]/self.FRAC_MULTIPLIER

        return week,sow

    def getGALWeekSow(self):
        """ create the object from a numpy array of MJDs
        Returns
        ----------
        week   : numpy array (nx)
        sow  : numpy array (nx) second of the week

        """
        gasec = self.tai_seconds[:,0] - self.TAISEC_GAL0

        week = np.floor(gasec/(7*86400))
        sow  = np.remainder(gasec,(7*86400)) + self.tai_seconds[:,1]/self.FRAC_MULTIPLIER

        return week,sow

    def getFromMinEpoch(self):
        """
        get difference from min epoch

        Returns
        -------
        diff : numpy array of float with difference from the first epoch

        """

        min_sec = np.min(self.tai_seconds[:,0])
        return (self.tai_seconds[:,0]-min_sec) + self.tai_seconds[:,1]/self.FRAC_MULTIPLIER, min_sec

    def intersect(self,taisec2,rate=None):
        """
        intersect two taiseconds object returning one with just the common epoch at the desired rate
        WARNING: this works only for object with reasonably regularly spaced epochs and rate which are integer multiplier or fraction of a second


        Parameters
        ----------
        taisec2 : taiseconds object

        Returns
        -------
        taisec : a taisecond object with just the common epoch
        i1 : index of the first array of epochs
        i2 : index of the second array of epochs

        """

        floatep1,min_sec1 = self.getFromMinEpoch()
        floatep2,min_sec2 = taisec2.getFromMinEpoch()
        if floatep1.size == 1 :
            rate1 = 1
            si1 = 1
        else:
            si1 = np.argsort(floatep1)
            rate1 = np.median(np.diff(floatep1))
        if floatep2.size == 1 :
            rate2 = 1
            si2 = 1
        else:
            si2 = np.argsort(floatep2)
            rate2 = np.median(np.diff(floatep2))
        if rate is None:
            rate = np.min([rate1,rate2])/3

        else:
            rate = rate/3
        if np.spacing(floatep1[-1]) > rate or  np.spacing(floatep2[-1]) > rate:
            print('WARNING: double precision not enough for the datset, possible incorrect result')
        if min_sec1 < min_sec2:
            floatep2 = floatep2 + (min_sec2 - min_sec1)
            min_sec = min_sec1
        else:
            floatep1 = floatep1 + (min_sec1 - min_sec2)
            min_sec = min_sec2
        intep1 = np.round(floatep1/rate).astype(np.int64)
        intep2 = np.round(floatep2/rate).astype(np.int64)

        intset, i1, i2 = np.intersect1d(intep1, intep2, return_indices=True)

        obj = taiseconds()
        intset = intset*rate
        intsec = np.floor(intset).astype(np.int64)
        fracsec = np.round(np.remainder(intsec,1)*self.FRAC_MULTIPLIER).astype(np.int64)
        obj.tai_seconds = np.zeros((fracsec.size,2),np.int64)
        obj.tai_seconds[:,0] = intsec + min_sec
        obj.tai_seconds[:,1] = fracsec
        return obj,si1[i1],si2[i2]


    def union(self,taisec2,rate=None):
        """
        intersect two taiseconds object retuning one with just the merged epoch
        WARNING: this works only for object with reasonably regualrly spaced epochs and rate which are integer multiplier or fraction of a second

        Parameters
        ----------
        taisec2 : taiseconds object

        Returns
        -------
        taisec : a taisecond object with just the common epoch

        """
        floatep1,min_sec1 = self.getFromMinEpoch()
        floatep2,min_sec2 = taisec2.getFromMinEpoch()
        if floatep1.size == 1 :
            rate1 = 1
            si1 = 1
        else:
            si1 = np.argsort(floatep1)
            rate1 = np.median(np.diff(floatep1))
        if floatep2.size == 1 :
            rate2 = 1
            si2 = 1
        else:
            si2 = np.argsort(floatep2)
            rate2 = np.median(np.diff(floatep2))
        if rate is None:
            rate = np.min([rate1,rate2])/3
        else:
            rate = rate/3
        if np.spacing(floatep1[-1]) > rate or  np.spacing(floatep2[-1]) > rate:
            print('WARNING: double precision not enough for the datset, possible incorrect result')
        if min_sec1 < min_sec2:
            floatep2 = floatep2 + (min_sec2 - min_sec1)
        else:
            floatep1 = floatep1 + (min_sec1 - min_sec2)
        intep1 = np.round(floatep1/rate).astype(np.int64)
        intep2 = np.round(floatep2/rate).astype(np.int64)

        unionset = np.union1d(intep1, intep2)
        i1 = np.searchsorted(unionset,intep1)
        i2 = np.searchsorted(unionset,intep2)

        obj = taiseconds()
        unionset = unionset*rate
        intsec = np.floor(unionset).astype(np.int64)
        fracsec = np.round(np.remainder(unionset,1)*self.FRAC_MULTIPLIER).astype(np.int64)
        obj.tai_seconds = np.zeros((fracsec.size,2),np.int64)
        obj.tai_seconds[:,0] = intsec
        obj.tai_seconds[:,1] = fracsec
        return obj,i1[si1],i2[si2]
    
    def append(self,to_append_obj):
        """
        append epochs froma nother teiseconds object

        Parameters
        ----------
        to_append_obj : taiseconds object

        Returns
        -------
        

        """
        if self.tai_seconds is None:
            self.tai_seconds = to_append_obj.tai_seconds
        else:
            self.tai_seconds = np.vstack([self.tai_seconds, to_append_obj.tai_seconds])
            
    def __gt__(self, taisec_comp):
        """
        > operator
        chek if taiseconds epochs are greater than taiseocnd single class

        Parameters
        ----------
        taisec_comp : taiseconds dtae to be compared

        Returns
        -------
        idx = index of greater dates
        

        """
        return (self.tai_seconds[:,0] > (taisec_comp.tai_seconds[0,0]-1)) | ((self.tai_seconds[:,0] == taisec_comp.tai_seconds[0,0]) & (self.tai_seconds[:,1] > taisec_comp.tai_seconds[0,1]))

    def __eq__(self, taisec_comp):
        """
        == operator
        chek if taiseconds epochs are equal than taiseocnd single class

        Parameters
        ----------
        taisec_comp : taiseconds dtae to be compared

        Returns
        -------
        idx = index of equal dates
        

        """
        return ((self.tai_seconds[:,0] == taisec_comp.tai_seconds[0,0]) & (self.tai_seconds[:,1] == taisec_comp.tai_seconds[0,1]))

    def __ne__(self, taisec_comp):
        """
        != operator
        chek if taiseconds epochs are not equal than taiseocnd single class

        Parameters
        ----------
        taisec_comp : taiseconds dtae to be compared

        Returns
        -------
        idx = index of not equal dates
        

        """
        return ((self.tai_seconds[:,0] != taisec_comp.tai_seconds[0,0]) | (self.tai_seconds[:,1] != taisec_comp.tai_seconds[0,1]))

    def __lt__(self, taisec_comp):
        """
        < operator
        chek if taiseconds epochs are smaller than taiseocnd single class

        Parameters
        ----------
        taisec_comp : taiseconds dtae to be compared

        Returns
        -------
        idx = index of less than dates
        

        """
        return (self.tai_seconds[:,0] < (taisec_comp.tai_seconds[0,0]+1)) | ((self.tai_seconds[:,0] == taisec_comp.tai_seconds[0,0]) & (self.tai_seconds[:,1] < taisec_comp.tai_seconds[0,1]))
    
    def __le__(self, taisec_comp):
        """
        <= operator
        chek if taiseconds epochs are less than or equal  than taiseocnd single class

        Parameters
        ----------
        taisec_comp : taiseconds dtae to be compared

        Returns
        -------
        idx = index of less than or equal  dates
        

        """
        return (self.tai_seconds[:,0] < (taisec_comp.tai_seconds[0,0]+1)) | ((self.tai_seconds[:,0] == taisec_comp.tai_seconds[0,0]) & (self.tai_seconds[:,1] <= taisec_comp.tai_seconds[0,1]))
    
    def __ge__(self, taisec_comp):
        """
        >= operator
        chek if taiseconds epochs are greater or equal than taiseocnd single class

        Parameters
        ----------
        taisec_comp : taiseconds dtae to be compared

        Returns
        -------
        idx = index of greater or equal dates
        

        """
        return (self.tai_seconds[:,0] > (taisec_comp.tai_seconds[0,0]-1)) | ((self.tai_seconds[:,0] == taisec_comp.tai_seconds[0,0]) & (self.tai_seconds[:,1] >= taisec_comp.tai_seconds[0,1]))
    