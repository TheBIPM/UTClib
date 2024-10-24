from utclib import tfex
from pathlib import Path

p = Path(__file__).resolve().parent

class TestHeader:

    def test_read(self):
        tf = tfex.tfex.from_file(p / 'test_data' / 'input.tfex')

