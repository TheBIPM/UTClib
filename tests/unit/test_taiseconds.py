from utclib import taiseconds
import numpy as np


class TestTaiSeconds:
    def test_creation(self):
        t = taiseconds.taiseconds()
        t.fromMJD(np.array([65000]))

