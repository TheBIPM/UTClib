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
