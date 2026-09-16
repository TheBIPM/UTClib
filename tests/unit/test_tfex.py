from utclib import tfex
from pathlib import Path
import pytest
import numpy as np

p = Path(__file__).resolve().parent

class TestHeader:

    def test_read(self):
        tf = tfex.tfex.from_file(p / 'test_data' / 'input.tfex')
        assert(tf.timestamps.tai_seconds[0][0] == 2077574437)

    def test_write(self):
        tf = tfex.tfex.from_file(p / 'test_data' / 'input.tfex')
        tf.write_to_file('output.tfex')

class TestAccess:

    def test_correct_column(self):
        tf = tfex.tfex.from_file(p / 'test_data' / 'input.tfex')
        assert(tf.datacol('delta_t').shape==(4,))

    def test_wrong_column(self):
        tf = tfex.tfex.from_file(p / 'test_data' / 'input.tfex')
        with pytest.raises(ValueError):
            tf.datacol('delta_t_blue')

class TestOthers:

    def test_regularize(self):
        tf = tfex.tfex.from_file(p / 'test_data' / 'input_withgaps.tfex')
        tf.regularize()
        tf_mjdsod = tf.timestamps.getIntMJDSOD()
        expected_mjd = np.repeat(60250,12)
        expected_sod = np.linspace(0,55,12)
        assert(
            np.all(tf_mjdsod[0]==expected_mjd)
            and
            np.all(tf_mjdsod[1]==expected_sod)
        )
