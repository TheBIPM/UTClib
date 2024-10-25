from utclib import tfex
from pathlib import Path

p = Path(__file__).resolve().parent

class TestHeader:

    def test_read(self):
        tf = tfex.tfex.from_file(p / 'test_data' / 'input.tfex')
        assert(tf.timestamps.tai_seconds[0][0] == 2077574437)

    def test_write(self):
        tf = tfex.tfex.from_file(p / 'test_data' / 'input.tfex')
        tf.write_to_file('output.tfex')


