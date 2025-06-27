import argparse
import os
import logging
import utclib.tfex as tfex
import utclib.plot as tfp

# Convert

def get_parser_conv():
    """ Dedicated function to collect command line parameters, so it can
    autogenerate doc too
    """
    parser = argparse.ArgumentParser(
        description="Command-line utility for time and frequency links")
    parser.add_argument(
        'input',
        type=str,
        help="Convert this file to tfex format")
    parser.add_argument(
        '-o', '--output',
        type=str,
        help="output file (default : same with .tfex extension)"
    )
    parser.add_argument(
        '-t', '--type',
        default="tsoft",
        help="Link type (tsoft, ippp, cggtts)")
    return parser


def tfexconv():
    import utclib.converters as conv
    args = get_parser_conv().parse_args()

    if not args.output:
        args.output = os.path.join(".",
                                   os.path.splitext(args.input)[0] + ".tfex")
    if args.type == "tsoft":
        tf = conv.parse_tsoft_file(args.input)
    elif args.type == "ippp":
        tf = conv.parse_ippp_tools_file(args.input)
    elif args.type == "cggtts":
        tf = conv.parse_cggtts_file(args.input)
        args.output = os.path.join(
            ".",
            os.path.splitext(args.input)[0] +
            "_{:05d}.tfex".format(tf.hdr.MJDSTART))
    else:
        logging.error("Unknown or unimplemented input type: %s" % args.type )
        raise SystemExit
    tf.write_to_file(args.output)

# diff

def get_parser_diff():
    """ Dedicated function to collect command line parameters, so it can
    autogenerate doc too
    """
    parser = argparse.ArgumentParser(
        description="Command-line utility for time and frequency links")
    parser.add_argument(
        'input1',
        type=str,
        help="first tfex file")
    parser.add_argument(
        'input2',
        type=str,
        help="second tfex file")
    parser.add_argument(
        '-o', '--output',
        type=str,
        help="output file (default : ./input1-input2.tfex)"
    )
    return parser


def tfexdiff():
    args = get_parser_diff().parse_args()

    if not args.output:
        args.output = os.path.join(
            ".",
            os.path.splitext(args.input1)[0] + "-" +
            os.path.splitext(args.input2)[0] + ".tfex")
    tf1 = tfex.tfex.from_file(args.input1)
    tf2 = tfex.tfex.from_file(args.input2)
    interp = tf2.interpolate(tf1.timestamps)
    diff.write_to_file(args.output)


# Basic plot of one or more time link(s)
def get_parser_plot():
    parser = argparse.ArgumentParser("Render simple plots of TFEX data files")
    parser.add_argument("tfex_files",
                        type=str,
                        help=("Coma-separated list of TFEX files to include in "
                              " plot"))
    parser.add_argument('-o', '--offsets',
                        help="Comma-separated list of offsets")
    parser.add_argument('--median',
                        action='store_true',
                        help="Display a median-filtered curve")
    parser.add_argument('--rebin',
                        action='store_true',
                        help="Display rebinned values")
    parser.add_argument('--window_width',
                        type=float,
                        default=86400,
                        help="Window width for filter (s)")
    parser.add_argument('--show_average',
                        action='append',
                        type=str,
                        help=("Calculate and draw a line showing average value"
                              " over the indicate MJDDD.DDD:MJDDD.DDD range")
                        )
    parser.add_argument('--jump',
                        action='append',
                        type=str,
                        help=("Signal a jump")
                        )
    return parser

def tfexplot():
    args = get_parser_plot().parse_args()
    tfplot = tfp.Plot(stats=None)
    if args.offsets:
        offsets = [float(x) for x in args.offsets.split(',')]
    for i, tfex_file in enumerate(args.tfex_files.split(',')):
        tf = tfex.tfex.from_file(tfex_file)
        if args.offsets:
            offset_s = offsets[i]
        else:
            offset_s = 0
        tfplot.add_link(tf, offset_s=offset_s, median=args.median,
                        rebin=args.rebin,
                        window_width=args.window_width,
                        show_average=args.show_average,
                        jumps=args.jump)
    tfplot.post_draw()
    tfplot.savefig()
