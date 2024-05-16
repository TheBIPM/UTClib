""" Utilities to convert to / from tfex
"""

import UTClib.tfexio as tfexio
import mjdutils.datetimemjd as mjdutils
import argparse
import numpy as np
import glob
import logging
import os


def hhmmss2d(hhmmss):
    hh = int(hhmmss[:2])
    mm = int(hhmmss[2:4])
    ss = int(hhmmss[4:])
    return hh / 24 + mm / 1440 + ss / 86400


class converter():
    def __init__(self, input_file, file_type):
        self.input_file = input_file
        self.file_type = file_type

    def get_tlink(self):
        outlnk = tfexio.Tfex()
        if self.file_type in ["ppp", "p3"]:
            parsed_content = self.parse_tsoft_file()
        elif self.file_type in ["ippp"]:
            parsed_content = self.parse_ippp_tools_file()
        elif self.file_type == 'fibre':
            parsed_content = self.parse_fibre_file()

        outlnk.from_array(parsed_content['data'])
        return outlnk

    def parse_tsoft_file(self):
        filename = self.input_file
        first_line = True
        rem = "____"
        data = []
        if "PPP" in os.path.basename(filename):
            linktype = "p3"
        elif "333" in os.path.basename(filename):
            linktype = "ppp"
        else:
            linktype = "unknown"
        with open(filename) as fp:
            for line in fp:
                ls = line.split()
                if first_line:
                    header = line.split()
                    first_line = False
                    continue
                if len(ls) != 4:
                    continue
                try:
                    mjd = float(ls[0])
                    val = float(ls[1])
                    # smooth = float(ls[2])
                    # diff = float(ls[3])
                    if (len(data) == 0 or mjd > data[-1][0]):
                        data.append([mjd, val])
                except ValueError:
                    continue
            try:
                rem = header[0].split('/')[1].split('-')[1]
                loc = header[0].split('/')[1].split('-')[0].split('__')[1]
            except IndexError:
                pass

        data = np.array(data)
        return {'data': data,
                'rem': rem,
                'loc': loc,
                'unit': 1e-9,
                'linktype': linktype}

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


def get_filename(args, mjd):
    """ Determine full path to source file, based on MJD and patterns
    """
    if args.source == "utc":
        root_path = "/mnt/PCtsoft/TAN/%y%m/"
    elif args.source == "utcr":
        root_path = "/mnt/utcr_home_utcr/prod/run/%y%V_cirt/"

    if args.type == "ppp":
        pattern = root_path + "LkG/{}*.333A_.dat".format(args.marker)
    elif args.type == "p3":
        pattern = root_path + "LkG/{}*.PPPA_.dat".format(args.marker)

    if args.pattern:
        pattern = args.pattern

    dt = mjdutils.date.frommjd(mjd)
    matches = glob.glob(dt.strftime(pattern))
    if matches:
        return matches[0]
    else:
        logging.warning("No file corresponding to {} (mjd {}, {})".format(
            dt.strftime(pattern), mjd, args.marker))
        return None


def main():
    parser = argparse.ArgumentParser(
        description="Generate links from various sources")
    parser.add_argument(
        'marker',
        help="local station marker")
    parser.add_argument(
        '-c', '--correct',
        action='append',
        default=[],
        help="Correction tuples mjdstart,mjdstop,offset")
    parser.add_argument(
        '--outputpath', '-o',
        type=str,
        default=".",
        help="Output directory")
    parser.add_argument(
        '-p', '--pattern',
        help="Full pattern for local data, use opt 'source' for shortcuts")
    parser.add_argument(
        '-r', '--range',
        required=True,
        help="MJD range (MJDDD-MJDDD or MJDDD or MJDDD_N)")
    parser.add_argument(
        '-s', '--source',
        type=str,
        default="utcr",
        help="[utc|utcr (default)]")
    parser.add_argument(
        '-t', '--type',
        required=True,
        help="Link type (p3, ppp, ippp, fibre)")
    args = parser.parse_args()

    if '-' in args.range:
        mjdstart, mjdstop = [int(x) for x in args.range.split('-')]
        mjds = range(mjdstart, mjdstop + 1)
    elif '_' in args.range:
        mjdstart, n = [int(x) for x in args.range.split('_')]
        mjds = range(mjdstart, mjdstart + n)
    else:
        mjds = [int(args.range)]
    file_list = []
    for mjd in mjds:
        filename = get_filename(args, mjd)
        if filename and filename not in file_list:
            file_list.append(filename)
    tlinks = []
    for input_file in file_list:
        tlinks.append(converter(input_file, args.type).get_tlink())

    concatenated_lnk = tfexio.concatenate(tlinks)

    if len(args.correct) > 0:
        for cor in args.correct:
            mjd1, mjd2, offset = [float(x) for x in cor.split(',')]
            concatenated_lnk.apply_offset(offset, mjd1, mjd2)

    if not os.path.exists(args.outputpath):
        os.makedirs(args.outputpath)
    concatenated_lnk.to_file(path=args.outputpath)


if __name__ == "__main__":
    main()
