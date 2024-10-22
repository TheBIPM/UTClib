from utclib import tfex
from pathlib import Path

p = Path(__file__).resolve().parent
tf = tfex.tfex()

class TestHeader:

    def test_read(self):
        tf.from_file(p / 'test_data' / 'input.tfex')

