""" Implementation of the CGGTTS format 2e
https://www.bipm.org/documents/20126/52718503/G1-2015.pdf/f49995a3-970b-a6a5-9124-cc0568f85450
Frederic.Meynadier@bipm.org
"""
import re
import os
import logging
import argparse
import pandas as pd
import numpy as np

log = logging.getLogger(__name__)


def sttime2d(hhmmss: str) -> float:
    """ Converts a HHMMSS time string into fractional day

    Parameters
    ----------
    hhhmmss:
        Input string

    Returns
    -------
    float
        Fractional day
    """
    hh = int(hhmmss[:2])
    mm = int(hhmmss[2:4])
    ss = int(hhmmss[4:])
    return hh / 24 + mm / 1440 + ss / 86400


class Cggtts():
    def __init__(self, const=None, freq=None, ll=None, mo=None, mjd=None):
        """ Constructor for the Cggtts class.

        Comments are replaced by the possible extracols after CK col
        """
        # GPS, GLO, GAL, BDS, BDS, QZS:
        self.const = const
        # 2 or 3-char identifier:
        self.freq = freq
        # 2-letter identifier of the lab
        self.ll = ll
        # 2-char ID of the receiver
        self.mo = mo
        self.mjd = mjd
        # see sect. 3.1
        self.const_code = {'GPS': 'G',
                           'GLO': 'R',
                           'GAL': 'E',
                           'BDS': 'C',
                           'QZS': 'J'}
        # CGGTTS V2e only has 3 codes (S=single, M= multi, Z=dual)
        if self.freq in ['C1', 'C2', 'P1', 'P2', 'LE1',
                         'B1I', 'B1C']:
            self.freq_code = 'M'
        elif self.freq in ['L3P', 'L3E', '3B2', '3B3']:
            self.freq_code = 'Z'
        else:
            self.freq_code = None

        self.header = {
            "CGGTTS     GENERIC DATA FORMAT VERSION": "",
            "REV DATE": "",
            "RCVR": "",
            "CH": "",
            "IMS": "",
            "LAB": "",
            "X": "",
            "Y": "",
            "Z": "",
            "FRAME": "",
            "COMMENTS": "",
            "INT DLY": "",
            "CAB DLY": "",
            "REF DLY": "",
            "REF": "",
            "CKSUM": ""
        }

        self.line_header = ""
        self.unit_header = ""

        # as written in the spec.
        self.cols = [{'label': 'SAT',
                      'rng': [1, 3],
                      'dtype': str,
                      'repr': 's'},
                     {'label': 'CL',
                      'rng': [5, 6],
                      'dtype': str,
                      'repr': 's'},
                     {'label': 'MJD',
                      'rng': [8, 12],
                      'dtype': int,
                      'repr': 'd'},
                     {'label': 'STTIME',
                      'rng': [14, 19],
                      'dtype': str,
                      'repr': 's'},
                     {'label': 'TRKL',
                      'rng': [21, 24],
                      'dtype': int,
                      'repr': 'd'},
                     {'label': 'ELV',
                      'rng': [26, 28],
                      'dtype': int,
                      'repr': 'd'},
                     {'label': 'AZTH',
                      'rng': [30, 33],
                      'dtype': int,
                      'repr': 'd'},
                     {'label': 'REFSV',
                      'rng': [35, 45],
                      'dtype': int,
                      'repr': 'd'},
                     {'label': 'SRSV',
                      'rng': [47, 52],
                      'dtype': int,
                      'repr': 'd'},
                     {'label': 'REFSYS',
                      'rng': [54, 64],
                      'dtype': int,
                      'repr': 'd'},
                     {'label': 'SRSYS',
                      'rng': [66, 71],
                      'dtype': int,
                      'repr': 'd'},
                     {'label': 'DSG',
                      'rng': [73, 76],
                      'dtype': int,
                      'repr': 'd'},
                     {'label': 'IOE',
                      'rng': [78, 80],
                      'dtype': int,
                      'repr': 'd'},
                     {'label': 'MDTR',
                      'rng': [82, 85],
                      'dtype': int,
                      'repr': 'd'},
                     {'label': 'SMDT',
                      'rng': [87, 90],
                      'dtype': int,
                      'repr': 'd'},
                     {'label': 'MDIO',
                      'rng': [92, 95],
                      'dtype': int,
                      'repr': 'd'},
                     {'label': 'SMDI',
                      'rng': [97, 100],
                      'dtype': int,
                      'repr': 'd'},
                     ]

        # Spec provides two options for further columns :
        self.cols_noiono = [{'label': 'FR',
                             'rng': [102, 103],
                             'dtype': int,
                             'repr': 'd'},
                            {'label': 'HC',
                             'rng': [105, 106],
                             'dtype': int,
                             'repr': 'd'},
                            {'label': 'FRC',
                             'rng': [108, 110],
                             'dtype': str,
                             'repr': 's'},
                            {'label': 'CK',
                             'rng': [112, 113],
                             'dtype': int,
                             'repr': 's'},
                            ]

        self.cols_iono = [{'label': 'MSIO',
                           'rng': [102, 105],
                           'dtype': int,
                           'repr': 'd'},
                          {'label': 'SMSI',
                           'rng': [107, 110],
                           'dtype': int,
                           'repr': 'd'},
                          {'label': 'ISG',
                           'rng': [112, 114],
                           'dtype': int,
                           'repr': 'd'},
                          {'label': 'FR',
                           'rng': [116, 117],
                           'dtype': int,
                           'repr': 'd'},
                          {'label': 'HC',
                           'rng': [119, 120],
                           'dtype': int,
                           'repr': 'd'},
                          {'label': 'FRC',
                           'rng': [122, 124],
                           'dtype': str,
                           'repr': 's'},
                          {'label': 'CK',
                           'rng': [126, 127],
                           'dtype': str,
                           'repr': 's'},
                          ]
        self.extracols = []
        self.df = None
        self.colnum = {}
        self.iono_avail = None

    def is_empty(self):
        return self.df is None

    def extend(self, ext_type="REFUTC"):
        """ Add colums to read / write extended format(s)
        """
        if ext_type == "REFUTC":
            self.extracols.append({'label': 'REFUTC',
                                   'rng': [129, 135],
                                   'dtype': int,
                                   'repr': 'd', 'unit': '.1ns'})
            self.extracols.append({'label': 'DUTC',
                                   'rng': [137, 143],
                                   'dtype': int,
                                   'repr': 'd', 'unit': '.1ns'})
        elif ext_type == "TGD":
            self.extracols.append({'label': 'TGD',
                                   'rng': [129, 135],
                                   'dtype': int,
                                   'repr': 'd', 'unit': '.1ns'})
        self.cols += self.extracols
        for i, c in enumerate(self.cols):
            self.colnum[c['label']] = i
        self.update_line_unit_header()

    def update_cols(self):
        """ Complete the list of data columns according to presence of iono,
        and fill the self.colnum correspondance table
        """

        if self.iono_avail:
            self.cols += self.cols_iono
        else:
            self.cols += self.cols_noiono
        for i, c in enumerate(self.cols):
            self.colnum[c['label']] = i

    def update_line_unit_header(self):
        """ Initialize these lines according to section 3.3
        """

        if self.iono_avail:
            self.line_header = (
                "SAT CL  MJD  STTIME TRKL ELV AZTH   REFSV      SRSV     "
                "REFSYS    SRSYS  DSG IOE MDTR SMDT MDIO SMDI MSIO SMSI "
                "ISG FR HC FRC CK")
            self.unit_header = (
                "             hhmmss  s  .1dg .1dg    .1ns     .1ps/s     "
                ".1ns    .1ps/s .1ns     .1ns.1ps/s.1ns.1ps/s  ")
        else:
            self.line_header = (
                "SAT CL  MJD  STTIME TRKL ELV AZTH   REFSV      SRSV     "
                "REFSYS    SRSYS  DSG IOE MDTR SMDT MDIO SMDI FR HC FRC CK")
            self.unit_header = (
                "             hhmmss  s  .1dg .1dg    .1ns     .1ps/s"
                "     .1ns    .1ps/s .1ns     .1ns.1ps/s.1ns."
                "1ps/s            ")
        for col in self.extracols:
            width = col['rng'][1] - col['rng'][0] + 1  # noqa
            self.line_header += f'{col["label"]:>{width}}'
            self.unit_header += f'{col["unit"]:>{width}}'

    def parse_filename(self, filepath):
        """ Section 3.1
        """
        filename = os.path.basename(filepath)
        x = filename[0]
        # f = filename[1]
        self.ll = filename[2:4]
        self.mo = filename[4:6]
        self.mjd = 1000 * int(filename[6:8]) + int(filename[9:12])

        for const, letter in self.const_code.items():
            if x in [letter.upper(), letter.lower()]:
                self.const = const
                break
        else:
            log.error('Constellation char unknown: {}'.format(x))

    def gen_filename(self):
        """ Returns canonical filename according to current mjd, constellation and code
        Returns
        -------
        str: file name
        """
        x = self.const_code[self.const]
        f = self.freq_code
        mj_ddd = "{:02d}.{:03d}".format(self.mjd // 1000, self.mjd % 1000)
        return (x + f + self.ll + self.mo + mj_ddd).lower()

    def parse_header(self, line):
        """ Section 3.2, header
        """
        # Non-greedy match of the first "=" sign
        m = re.match(r"(?P<key>.*?)=(?P<value>.*)", line)
        if m is None:
            return
        key = m.group('key').strip()
        val = m.group('value').strip()
        try:
            self.header[key] = val
        except KeyError:
            log.error("Unknown header: {}".format(key))

    def checksum(self, ck_str):
        return '{:02x}'.format(sum(ck_str.encode('ascii')) % 256).upper()

    def parse_data(self, line):
        """ Section 3.5, "data line"
        """
        buf = []
        for c in self.cols:
            try:
                strval = line[c['rng'][0] - 1: c['rng'][1]].strip()
            except IndexError:
                buf.append('')
                continue
            try:
                if c['dtype'] is str:
                    buf.append(strval)
                elif c['dtype'] is int:
                    buf.append(int(strval))
            except ValueError:
                buf.append(np.nan)

        # checksum verification
        if self.iono_avail:
            ck_str = line[0:125]
        else:
            ck_str = line[0:111]
        if (buf[self.colnum['CK']] != "GG" and
                self.checksum(ck_str) != buf[self.colnum['CK']]):
            log.warning("Checksum error detected : {}".format(line))
        return buf

    def read_from_path(self, path):
        """ Automatically determine the filename from attributes, and
        look for file in path """

        full_path = os.path.join(path, self.gen_filename())
        if not os.path.exists(full_path):
            log.debug(
                "File not found for loading cggtts: {}".format(full_path))
            return
        self.read(full_path)

    def read(self, filename, parse_filename=True):
        """ Read a CGGTTS file and populate the object

        Parameters
        ----------
        filename: str
            complete path to a CGGTTS file
        parse_filename: bool
            If True, will attempt to deduce metadata from the filename
            If False, filling the metadata can be done at a later stage
        """
        if parse_filename:
            self.parse_filename(filename)
        with open(filename, errors='replace') as fp:
            in_header = True
            line_header_parsed = False
            unit_header_parsed = False
            raw_data = []
            for line in fp:
                if len(line.strip()) == 0:
                    # In theory number header should be defined by line number.
                    # But some cggtts have multiple "comments" line
                    # -> Trust the empty line
                    in_header = False
                    continue
                if in_header:
                    self.parse_header(line)
                    continue
                if not line_header_parsed:
                    self.line_header = line.replace('\n', '')
                    # This should be tested by header IMS = 99999
                    # instead, but to deal with malformed files :
                    if 'MSIO' in line:
                        self.iono_avail = True
                    else:
                        self.iono_avail = False
                    self.update_cols()
                    line_header_parsed = True
                    continue
                if not unit_header_parsed:
                    self.unit_header = line.replace('\n', '')
                    unit_header_parsed = True
                    continue
                raw_data.append(self.parse_data(line.strip()))
        self.update_line_unit_header()
        self.df = pd.DataFrame(raw_data)
        if len(self.df) == 0:
            log.debug("Empty file for {} {} {}".format(
                self.const, self.freq, self.mjd))
            return
        self.df.columns = [x['label'] for x in self.cols]
        # Add supplementary column : mjd float
        self.df['mjdfloat'] = (self.df['MJD'] +
                               self.df['STTIME'].apply(sttime2d))

        # Set freq from first row if not set yet
        if self.freq is None:
            self.freq = self.df['FRC'].iloc[0]

    def write(self, path, filename=None, force=False):
        """ Write a CGGTTS file on disk
        Parameters
        ----------
        path: str
            output path
        filename: str (opt)
            If not provided, the filename will be generated from metadata
        force: bool (opt, default=False)
            Overwrite if the file exists
        """

        if not os.path.exists(path):
            os.makedirs(path)
        if filename is None:
            filename = self.gen_filename()
        fullpath = os.path.join(path, filename)
        if os.path.exists(fullpath) and not force:
            log.error("File exists, exiting...")
            raise SystemExit
        with open(fullpath, 'w') as fp:
            fp.write(self.gen_header_output())
            fp.write(self.gen_data_output())

    def gen_header_output(self):
        """ Return a header string generated from the object
        """
        outs = ""
        for key, val in self.header.items():
            outs += "{} = {}\n".format(key, val)
        outs += "\n{}\n{}\n".format(self.line_header, self.unit_header)
        return outs

    def gen_data_output(self):
        """ Return a data string generated from the object
        """
        out = []

        for index, row in self.df.iterrows():
            data_str = ""
            for i, col in enumerate(self.cols):
                if col['label'] == 'CK':
                    # data_str += self.checksum(data_str[:-1]) + " "
                    # Checksum not working yet (fix '+' signs in some cols)
                    data_str += "GG "
                    continue
                try:
                    rng = col['rng']
                    w = rng[1] - rng[0] + 1
                    data_str += (
                        ("{:" + str(w) + col['repr'] + "} ").format(
                            col['dtype'](row[col['label']])))
                except ValueError:
                    data_str += ("{:" + str(w) + "} ").format(
                        '*')
            out.append(data_str)
        return "\n".join(out) + "\n"

    def refsys_median_per_epoch(self):
        """ Calculate the median of each epoch

        For each group of data related to the same epoch, calculate the median
        of the REFSYS values.

        Returns
        -------
        np.array
        """
        if self.df.empty:
            log.error('Trying to get median_per_epoch from empty file')
            return None
        refsys = self.df[['MJD', 'STTIME', 'mjdfloat', 'REFSYS']].copy()
        refsys['REFSYS'] = refsys['REFSYS'].div(10)
        return refsys.groupby(['MJD', 'STTIME']).median()

    def refsys_weighted_average_per_epoch(self):
        """ Return 1 REFSYS value per epoch, obtained by averaging
        all REFSYS data with weight = sin**2(elev)

        Returns
        -------
        np.array
        """
        output = []
        try:
            refsys = self.df[
                ['MJD', 'STTIME', 'mjdfloat', 'REFSYS', 'ELV']].copy()
        except KeyError:
            log.error('Trying to get weighted average from empty file')
            output.append([self.mjd, '000000', self.mjd, np.nan])
            output = pd.DataFrame(
                output,
                columns=['MJD', 'STTIME', 'mjdfloat', 'REFSYS'])
            return output
        refsys['REFSYS'] = refsys['REFSYS'].div(10)
        refsys['ELV'] = refsys['ELV'].div(10)
        refsys['sin2elv'] = refsys['ELV'].map(
            lambda x: np.sin(np.radians(x))**2)
        last_mjdfloat = None
        for name, group in refsys.groupby(['MJD', 'STTIME']):
            mjd, sttime = name
            mjdfloat = group.iloc[0]['mjdfloat']
            # If last point is too old (> 1d) : mark a "nan"
            if last_mjdfloat is not None and mjdfloat - last_mjdfloat > 1:
                output.append([int(np.ceil(last_mjdfloat)),
                               '000000',
                               np.ceil(last_mjdfloat),
                               np.nan])
            last_mjdfloat = mjdfloat
            # Exclude obviously wrong refsys values :
            # - off by 100 ns from median
            # - off by 1000 ns (abs)
            group = group[np.abs(group.REFSYS) < 1000]
            group_median = group['REFSYS'].median()
            group = group[np.abs(group.REFSYS - group_median) < 100]
            # Calculate value
            if group['sin2elv'].sum() != 0:
                value = (group['REFSYS'].multiply(group['sin2elv']).sum() /
                         group['sin2elv'].sum())
                output.append([mjd, sttime, mjdfloat, value])
        output = pd.DataFrame(
            output,
            columns=['MJD', 'STTIME', 'mjdfloat', 'REFSYS'])
        return output


def gen_from_marker_sig_mjd(marker, sig, mjd):
    """ Return a Cggtts object, metadata initialized but empty of data

    Parameters
    ----------
    marker: str
        The 4-letter identifier of the receiver
    sig: str
        a string containing the constellation/frequency combination, e.g.
        GPS_L3P
    mjd: int
        An integer corresponding to the date's MJD

    Returns
    -------
    pycggtts.Cggtts()
    """
    ll = marker[:2]
    mo = marker[-2:]
    const, freq = sig.split('_')
    return Cggtts(const=const, freq=freq, ll=ll, mo=mo, mjd=mjd)


def load_multiple_files(paths_cggtts, marker, sig,
                        ext_type=None):
    """ Load multiple cggtts files

    Parameters
    ----------
    path_cggtts: list of {'mdj': mjd, 'path': path} dict
        Allows to direct to different dirs depending on year
    marker: string
        receiver marker
    sig: string
        GNSS signal (e.g. GPS_L3P)

    Returns
    -------
    output: pycggts.Cggtts()
    """
    output = gen_from_marker_sig_mjd(marker, sig, paths_cggtts[0]['mjd'])
    if ext_type:
        output.extend(ext_type=ext_type)
    df_list = []
    for mjd_path in paths_cggtts:
        mjd = mjd_path['mjd']
        cggtts_path = mjd_path['path']
        cg = gen_from_marker_sig_mjd(marker, sig, mjd)
        if ext_type:
            cg.extend(ext_type=ext_type)
        cg.read_from_path(cggtts_path)
        if cg.is_empty():
            log.warning("No cggtts data for %s %s %s" %
                        (marker, sig, mjd))
            continue
        df_list.append(cg.df)
    try:
        output.df = pd.concat(df_list)
    except ValueError:
        log.warning("No data to concatenate !")
    return output


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "pattern",
        help="file pattern (use [MJ.DDD] for dotted mjd)")
    parser.add_argument(
        "--period", "-p",
        help="Period (MJDDD-MJDDD)")
    args = parser.parse_args()

    mjdstart, mjdstop = [int(x) for x in args.period.split('-')]
    output = []
    for mjd in range(mjdstart, mjdstop + 1):
        filename = args.pattern.replace(
            "[MJ.DDD]",
            "{:02d}.{:03d}".format(mjd // 1000, mjd % 1000))
        if not os.path.exists(filename):
            print("{}: no such file".format(filename))
            continue
        cg = Cggtts()
        cg.read(filename)
        # cg.write('./test', force=True)
        output.append(cg.refsys_median_per_epoch())

    all_refsys = pd.concat(output)
    pattern = os.path.basename(args.pattern).replace('[MJ.DDD]', '')
    all_refsys.to_csv("refsys_{}.csv".format(pattern), sep=" ")
