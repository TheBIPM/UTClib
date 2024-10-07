"""
A module that handles tfex header

tfex header is supposed to be following TOML syntax

A fixed set of parameters is allowed
"""

import toml

class TfexHdrError(Exception):
    pass

class tfexhdr:
    def __init__(self):
        self.valid_keywords_and_types={
            'TFEXVER': str,
            'MJDSTART': float,
            'MJDSTOP': float,
            'NDATA': int,
            'PREFIX': str,
            'SAMPLING_INTERVAL_s': float,
            'AVERAGING_WINDOW_s': float,
            'MISSING_EPOCHS': bool,
            'AUTHOR': str,
            'DATE':str,
            'REFPOINTS': list,
            'COLUMNS': dict,
            'CONSTANT_DELAYS': list,
            'COMMENT': str}
        # This turns each keyword into an attribute of the class
        for kw in self.valid_keywords_and_types.keys():
            setattr(self, kw, None)

    def load(self, toml_string: str):
        """ Loads values from an input string that is valid TOML
        """
        parsed_toml = toml.loads(toml_string)
        for kw, value in parsed_toml.items():
            if kw not in self.valid_keywords_and_types:
                raise TfexHdrError("Unauthorized keyword: %s" % kw)
            try:
                # Update attribute while casting to proper type
                setattr(self, kw,
                        self.valid_keywords_and_types[kw](value))
            except (TypeError, ValueError):
                raise TfexHdrError("Wrong type for %s" % kw)



if __name__ == "__main__":
    hdr = tfexhdr()
    hdr.TFEXVER = 1.0
    print(hdr.TFEXVER)
    hdr.load("TFEXVER = 2.0\n")
    print(hdr.TFEXVER)

