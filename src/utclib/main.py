import argparse
import os
import utclib.converters as conv
import logging

def get_parser():
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
    args = get_parser().parse_args()

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
