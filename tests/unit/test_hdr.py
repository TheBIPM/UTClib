from utclib import tfexhdr
from pathlib import Path

p = Path(__file__).resolve().parent
hdr = tfexhdr.tfexhdr()

class TestHeader:

    def test_read(self):
        hdr.read(p / 'test_data' / 'input.tfex')
        assert(hdr.TFEXVER == "0.2")

    def test_write(self):
        print(hdr.write())
