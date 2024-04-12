import argparse
import utclib.tfexio as tfex

def get_parser():
    """ Dedicated function to collect command line parameters, so it can
    autogenerate doc too
    """
    parser = argparse.ArgumentParser(
        description="Command-line utility for time and frequency links")
    parser.add_argument(
        '--to_tfex',
        type=str,
        help="Convert this file to tfex format")
    return parser


def tfexconv():
    args = get_parser().parse_args()
    if args.to_tfex:
       lnk = tfex.Tfex()
       lnk.load(args.to_tfex)
       lnk.to_stdout()
