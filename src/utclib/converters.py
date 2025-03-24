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

def parse_ippp_tools_file(self):
    lab1 = ""
    lab2 = ""
    data = []
    sign_changed = False
    with open(self.input_file) as fp:
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
                mjd, hhmmss, val = line.split()
                if not sign_changed:
                    val = -float(val)
                data.append([int(mjd) + hhmmss2d(hhmmss),
                             float(val)])
            except IndexError:
                continue
    return {'data': np.array(data),
            'loc': lab2,
            'rem': lab1,
            'unit': 1e-9,
            'linktype': 'ippp'}

def parse_fibre_file(self):
    labs = self.input_file.split('_')[2]
    lab1, lab2 = labs.split('-')
    print("Parsing {}".format(self.input_file))
    with open(self.input_file) as fp:
        data = np.genfromtxt(fp)
    # Resample from to 30s data
    w = 30
    int_mjd = int(data[0, 0])
    samples = {}
    for d in data:
        slot = np.floor(((d[0] - int_mjd) * 86400) / w) * w
        if slot not in samples:
            samples[slot] = []
        if np.abs(d[1]) < 10000:
            samples[slot].append(d[1])
    output = []
    for s in samples.keys():
        output.append([int_mjd + s / 86400,
                       np.nanmean(samples[s])])

    return {'data': np.array(output),
            'loc': lab1,
            'rem': lab2,
            'unit': 1e-9,
            'linktype': 'fibre'}
