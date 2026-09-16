from utclib import taiseconds
import numpy as np
import timeit


class TestTaiSeconds:
    
    def test_creation(self):
        t = taiseconds.taiseconds()
        t.fromMJD(np.array([65000]))

    def test_speed(self):
        # Use "pytest -s" to see stdout
        t1 = timeit.timeit(
            'orig_dt.date(2022, 1, 1)',
            setup='import datetime as orig_dt',
            number=1000)
        t2 = timeit.timeit(
            'ts.fromUTCCalendar([2022], [1], [1], [0], [0], [0])',
            setup="from utclib import taiseconds; ts = taiseconds.taiseconds()",
            number=1000)
        t3 = timeit.timeit(
            'ts.fromUTCCalendar(year, month, day, zeros, zeros, zeros)',
            setup=("from utclib import taiseconds;"
                   "import numpy as np;"
                   "ts = taiseconds.taiseconds();"
                   "year = np.zeros(1000);"
                   "month = np.zeros(1000);"
                   "day = np.zeros(1000);"
                   "zeros = np.zeros(1000);"
                   "year += 2022;"
                   "month += 1;"
                   "day += 1"),
            number=1)
        t4 = timeit.timeit(
            'np.array(dates, dtype="datetime64")',
            setup=("import numpy as np;"
                   "dates = ['2022-01-01' for i in range(1000)];"
                   ),
            number=1)
        print("\n")
        print("1000 datetime creation time    : {:.3f} ms".format(t1 * 1000))
        print("1000 x 1 taiseconds creation time : {:.3f} ms".format(t2 * 1000))
        print("1 x 1000 taiseconds creation time : {:.3f} ms".format(t3 * 1000))
        print("1 x 1000 datetime64 creation time : {:.3f} ms".format(t4 * 1000))

    def test_regularize(self):
        """test with integer number of seconds as sampling rate, reference array created from MJD/SoD, test array created by deleting a random number of elements in the middle"""
        N_points = 10
        rate = 300 # seconds
        # Generate N_points timetags
        mjd_sod = np.array([[60000]*N_points,np.arange(0,N_points*rate,rate)]).T
        ts = taiseconds.taiseconds().fromMJDSoD(mjd_sod[:,0], mjd_sod[:,1])
        # randomly delete some points in middle
        import random
        N_random = 2
        idx_random = random.sample(range(1,N_points-1), 2)
        mjd_sod_withgaps = np.delete(mjd_sod, idx_random, 0)
        ts_new = taiseconds.taiseconds().fromMJDSoD(mjd_sod_withgaps[:,0], mjd_sod_withgaps[:,1])
        idx_old = ts_new.regularizeSampling(rate)
        assert(len(ts)==len(ts_new) and np.all(ts.tai_seconds[:,0]==ts_new.tai_seconds[:,0]) and np.all(ts.tai_seconds[:,1]==ts_new.tai_seconds[:,1]))
