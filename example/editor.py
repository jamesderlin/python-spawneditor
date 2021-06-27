#!/usr/bin/env python3

"""
Executable wrapper around spawneditor.py.  Runs the default editor on a
specified file at a specified line number.
"""

import getopt
import os
import sys
import typing

import spawneditor

_usage_text = """
Options:
    --line=LINE
"""


def usage(*, full: bool = False, file: typing.TextIO = sys.stdout) -> None:
    """Prints usage information."""
    print(f"Usage: {__name__} [OPTIONS] FILE\n"
          f"       {__name__} --help\n",
          file=file,
          end="")
    if full:
        print(f"\n"
              f"{__doc__.strip()}\n"
              f"\n"
              f"{_usage_text.strip()}\n",
              file=file,
              end="")


def main(argv: typing.List[str]) -> int:
    try:
        (opts, args) = getopt.getopt(argv[1:], "h", ["help", "line="])
    except getopt.GetoptError as e:
        print(str(e), file=sys.stderr)
        usage(file=sys.stderr)
        return 1

    line_number: typing.Optional[int] = None
    for (o, a) in opts:
        if o in ("-h", "--help"):
            usage(full=True)
            return 0
        elif o == "--line":
            line_number = int(a)

    spawneditor.edit_file(args[0] if args else None, line_number=line_number)

    return 0


if __name__ == "__main__":
    __name__ = os.path.basename(__file__)  # pylint: disable=redefined-builtin

    try:
        sys.exit(main(sys.argv))
    except KeyboardInterrupt:
        sys.exit(1)
