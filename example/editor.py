#!/usr/bin/env python3

"""
Executable wrapper around spawneditor.py.  Runs the default editor on a
specified file at a specified line number.
"""

import argparse
import os
import sys
import typing

import spawneditor


def main(argv: typing.List[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__.strip(), add_help=False)
    ap.add_argument("-h", "--help", action="help",
                    help="Show this help message and exit.")
    ap.add_argument("--line", metavar="LINE", type=int)
    ap.add_argument("file", metavar="FILE", nargs="?")

    args = ap.parse_args(argv[1:])

    spawneditor.edit_file(args.file, line_number=args.line)

    return 0


if __name__ == "__main__":
    __name__ = os.path.basename(__file__)  # pylint: disable=redefined-builtin

    try:
        sys.exit(main(sys.argv))
    except KeyboardInterrupt:
        sys.exit(1)
