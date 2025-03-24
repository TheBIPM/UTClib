""" Utilities to convert to / from tfex
"""

import utclib.tfex as tfex
import numpy as np
import re


def hhmmss2d(hhmmss):
    hh = int(hhmmss[:2])
    mm = int(hhmmss[2:4])
    ss = int(hhmmss[4:])
    return hh / 24 + mm / 1440 + ss / 86400

def hhmmss2s(hhmmss_as_int):
    hh = hhmmss_as_int // 10000
    mm = (hhmmss_as_int - hh*10000) // 100
    ss = hhmmss_as_int % 100
    return hh * 3600 + mm * 60 + ss

def parse_tsoft_file(filename):
    first_line = True
    rem = "____"
    loc = "____"
    tech = "Unknown" # Can be : GPSP3, GPSPPP, TWSTFT, etc...
    tau0 = None
    mjd = []
    sod = []
    val = []
    smo = []
    dlt = []

    # Tech codes (from https://webtai.bipm.org/ftp/pub/tai/timelinks/lkc/ReadMe_LinkComparison_ftp_v12.pdf)
    techs = {"333A_": "GPSPPP",
             "PPPA_": "GPSP3",
             "MMMA_": "GPSMC",
             "EEEA_": "GALP3",
             "CCCA_": "BDSP3",
             "RRRC_": "GLNMC",
             "TTTT_": "TWSTFT",
             "TTTTs": "TWSDRR",
             "TTTTr": "TWSRS",
             "TTTTi": "GPS IPPP",
             "T3B3_": "TWGPPP",
             "GRB1_": "GPSGLN"
            }

    for code, tc in techs.items():
        if filename.split('.')[1] == code:
            tech = tc

    pattern_tau0 = r"Tau0=\s*(?P<tau0>\d+)s"
    with open(filename) as fp:
        for line in fp:
            ls = line.split()
            if first_line:
                # Find samplin interval
                m = re.findall(pattern_tau0, line)
                if m:
                    tau0 = float(m[0])
                header = line.split()
                # find local and remote
                try:
                    rem = header[0].split('/')[1].split('-')[1]
                    loc = header[0].split('/')[1].split('-')[0].split('__')[1]
                except IndexError:
                    pass

                first_line = False
                continue
            if len(ls) != 4:
                continue
            try:
                if len(mjd) != 0 and float(ls[0]) < mjd[-1]:
                    break
                mjd.append(int(np.floor(float(ls[0]))))
                sod.append(int(np.floor((float(ls[0])%1 * 86400))))
                val.append(float(ls[1]))
                try:
                    smo.append(float(ls[2]))
                except ValueError:
                    smo.append(np.nan)
                try:
                    dlt.append(float(ls[3]))
                except ValueError:
                    dlt.append(np.nan)

            except ValueError:
                continue

    tf = tfex.tfex.from_arrays([
        (mjd,
         {'timetag': True,
          'label': 'MJD',
          'scale': 'utc',
          'unit': 'si:day',
          'format': '5d'}),
        (sod,
         {'timetag': True,
          'label': 'SoD',
          'scale': 'utc',
          'unit': 'si:second',
          'format': '5d'}),
        (val,
         {'label': 'delta_t',
          'trip': ['AB'],
          'unit': 'si:nanosecond',
          'format': '8.3f'}),
        (smo,
         {'label': 'smoothed Vondrak',
          'unit': 'si:nanosecond',
          'format': '8.3f'}),
        (dlt,
         {'label': 'data - smoothed',
          'unit': 'si:nanosecond',
          'format': '8.3f'}),
    ])
    tf.hdr.TFEXVER = "0.2"
    tf.hdr.PREFIX = {'si': 'https://si-digital-framework.org/SI/units/'}
    tf.hdr.AUTHOR = "BIPM"
    tf.hdr.SAMPLING_INTERVAL_s = tau0
    tf.hdr.add_refpoint(rp_id="A", rp_ts="Unknown", rp_dev=loc, rp_type=tech)
    tf.hdr.add_refpoint(rp_id="B", rp_ts="Unknown", rp_dev=rem, rp_type=tech)
    tf.hdr.COMMENT = ""
    return tf


def parse_ippp_tools_file(filename):
    """ Converts from the custom "IPPP tools" format
    """
    lab1 = ""
    lab2 = ""
    sign_changed = False
    mjd = []
    sod = []
    val = []
    with open(filename) as fp:
        for line in fp:
            if "LAB1 =" in line:
                lab1 = line.split()[2]
                continue
            if "LAB2 =" in line:
                lab2 = line.split()[2]
                continue
            if line[0] == "!":
                if 'sign changed' in line:
                    sign_changed = True
                continue
            if "@END Header" in line:
                continue
            try:
                mjd_i, hhmmss_i, val_i = line.split()
                if not sign_changed:
                    val_i = -float(val_i)
                mjd.append(int(mjd_i))
                sod.append(int(hhmmss2s(hhmmss_i)))
                val.append(float(val_i))
            except ValueError:
                continue
    tf = tfex.tfex.from_arrays([
        (mjd,
         {'timetag': True,
          'label': 'MJD',
          'scale': 'utc',
          'unit': 'si:day',
          'format': '5d'}),
        (sod,
         {'timetag': True,
          'label': 'SoD',
          'scale': 'utc',
          'unit': 'si:second',
          'format': '5d'}),
        (val,
         {'label': 'delta_t',
          'trip': ['AB'],
          'unit': 'si:nanosecond',
          'format': '8.3f'}),
    ])
    tf.hdr.TFEXVER = "0.2"
    tf.hdr.PREFIX = {'si': 'https://si-digital-framework.org/SI/units/'}
    tf.hdr.AUTHOR = "BIPM"
    tech="IPPP"
    tf.hdr.add_refpoint(rp_id="A", rp_ts="Unknown", rp_dev=lab1, rp_type=tech)
    tf.hdr.add_refpoint(rp_id="B", rp_ts="Unknown", rp_dev=lab2, rp_type=tech)
    tf.hdr.COMMENT = ""
    return tf


def parse_cggtts_file(filename):
    """ Convert the REFSYS values from a CGGTTS file into a TFEX object
    """
    import utclib.pycggtts as pc
    cg = pc.Cggtts()
    cg.read(filename)
    refsys_median = cg.refsys_weighted_average_per_epoch()
    mjd = refsys_median['MJD'].astype(int).values
    sod = hhmmss2s(refsys_median['STTIME'].astype(int).values)
    val = refsys_median['REFSYS'].astype(int).values/10
    tf = tfex.tfex.from_arrays([
        (mjd,
         {'timetag': True,
          'label': 'MJD',
          'scale': 'utc',
          'unit': 'si:day',
          'format': '5d'}),
        (sod,
         {'timetag': True,
          'label': 'SoD',
          'scale': 'utc',
          'unit': 'si:second',
          'format': '5d'}),
        (val,
         {'label': 'delta_t',
          'trip': ['AB'],
          'unit': 'si:nanosecond',
          'format': '8.1f'}),
    ])
    tf.hdr.TFEXVER = "0.2"
    tf.hdr.PREFIX = {'si': 'https://si-digital-framework.org/SI/units/'}
    tf.hdr.AUTHOR = "BIPM"
    tf.hdr.MJDSTART = mjd[0]
    tf.hdr.MJDSTOP = mjd[-1]
    tech = cg.const + "_" + cg.freq
    tf.hdr.add_refpoint(
        rp_id="A", rp_ts=cg.header['REF'], rp_dev=cg.header['RCVR'], rp_type=tech)
    tf.hdr.add_refpoint(
        rp_id="B", rp_ts=cg.const, rp_dev='REFSYS', rp_type=tech)
    tf.hdr.COMMENT = ""
    return tf




