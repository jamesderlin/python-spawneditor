# spawneditor.py
#
# Copyright (C) 2020-2021 James D. Lin <jamesdlin@berkeley.edu>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""
A Python module that attempts to provide a common interface for opening an
editor at a specified line in a file.
"""

import os
import pathlib
import shlex
import subprocess
import tempfile
import typing

posix_style = "+{line_number} \"{file_path}\""
sublime_text_style = "\"{file_path}:{line_number}\""

# yapf: disable  # See <https://github.com/google/yapf/issues/928>
editor_syntax_table = {
    # Visual Studio Code
    "code": "--goto \"{file_path}:{line_number}\"",

    # Sublime Text
    "subl": sublime_text_style,
    "sublime_text": sublime_text_style,

    # Atom
    "atom": sublime_text_style,

    # TextMate
    "mate": "--line {line_number} \"{file_path}\"",

    # Notepad++
    "notepad++": "-n{line_number} \"{file_path}\"",

    # POSIX
    "vi": posix_style,
    "vim": posix_style,
    "emacs": posix_style,
    "xemacs": posix_style,
    "nano": posix_style,
    "pico": posix_style,
    "gedit": posix_style,
}
# yapf: enable


class UnsupportedPlatformError(Exception):
    """An exception class raised for unsupported platforms."""


def edit_file(file_path: str,
              *,
              line_number: typing.Optional[int] = None,
              editor: typing.Optional[str] = None,
              stdin: typing.Optional[typing.TextIO] = None) -> None:
    """
    Opens the specified file in an editor.  If a line is specified, tries to
    open the editor at that line number, if possible.

    The launched editor will be chosen from, in order:

    1. The explicitly specified editor.
    2. The `VISUAL` environment variable, if `DISPLAY` is available.
    3. The `EDITOR` environment variable.
    4. Hard-coded paths to common editors.

    `stdin` may be specified to override a redirected standard input stre
    with a TTY.

    Raises an `UnsupportedPlatformError` if an editor cannot be determined.

    Raises `subprocess.CalledProcessError` if opening the editor failed.
    """
    options: typing.List[str] = []

    editor = (editor
              or (os.environ.get("DISPLAY") and os.environ.get("VISUAL"))
              or os.environ.get("EDITOR"))

    if not editor:
        if os.name == "posix":
            default_editor = pathlib.Path("/usr/bin/editor")
            editor = (str(default_editor.resolve())
                      if default_editor.exists() else "vi")
        elif os.name == "nt":
            editor = "notepad.exe"
            line_number = None
        else:
            raise UnsupportedPlatformError(
                "Unable to determine what text editor to use.  "
                "Set the EDITOR environment variable.")

    assert editor
    (editor, *options) = shlex.split(editor, posix=(os.name == "posix"))

    if file_path.startswith("-"):
        # Ensure that files that start with a hyphen aren't treated as options.
        # The invoked editor might not follow the POSIX practice of using a
        # special `--` option, so tweaking the file path is more universal.
        #
        # pathlib.Path automatically normalizes, which we do NOT want in this
        # case.
        file_path = os.path.join(".", file_path)

    additional_arguments = [file_path]
    if line_number:
        editor_name = pathlib.Path(editor).stem
        syntax_format = editor_syntax_table.get(editor_name)
        if syntax_format:
            additional_arguments \
                = shlex.split(syntax_format.format(file_path=file_path,
                                                   line_number=line_number))

    subprocess.run((editor,
                    *options,
                    *additional_arguments),
                   stdin=stdin,
                   check=True)


def edit_temporary(
        content_lines: typing.Optional[typing.Iterable[str]] = None,
        *,
        temporary_prefix: typing.Optional[str] = None,
        line_number: typing.Optional[int] = None,
        editor: typing.Optional[str] = None,
        stdin: typing.Optional[typing.TextIO] = None) -> typing.List[str]:
    """
    Calls `edit_file` on a temporary file with the specified contents.

    `content_lines` specifies the initial contents of the temporary file.  Each
    element will be written to a separate line, so elements should not include
    trailing newlines (unless extra blank lines are desired).

    On success, returns a list of the lines of the temporary file (including
    any initial content).  For compatibility with file-like objects, the lines
    will include trailing newlines.

    `temporary_prefix` specifies the desired filename prefix for the temporary
    file.

    For all other parameters, see `edit_file`.
    """
    try:
        with tempfile.NamedTemporaryFile(mode="w",
                                         prefix=temporary_prefix,
                                         delete=False,
                                         encoding="utf8") as file:
            for line in content_lines or []:
                print(line, file=file)

        edit_file(file.name,
                  line_number=line_number,
                  editor=editor,
                  stdin=stdin)

        with open(file.name, "r", encoding="utf8") as f:
            return list(f)
    finally:
        os.remove(file.name)
