from utclib import tfexhdr
from pathlib import Path

class TestHeader:
    def test_read(self):
        p = Path(__file__).resolve().parent
        hdr = tfexhdr.tfexhdr()
        hdr.read(p / 'test_data' / 'input.tfex')
        assert(hdr.TFEXVER == "0.2")
