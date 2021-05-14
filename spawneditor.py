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
import typing


class UnsupportedPlatformError(Exception):
    """An exception class raised for unsupported platforms."""


def spawn_editor(file_path: str, *,
                 line_number: typing.Optional[int] = None,
                 editor: typing.Optional[str] = None,
                 stdin: typing.TextIO) -> None:
    """
    Opens the specified file in an editor.  If a line is specified, tries to
    open the editor at that line number, if possible.

    The launched editor will be chosen from, in order:

    1. The explicitly specified editor.
    2. The `VISUAL` environment variable.
    3. The `EDITOR` environment variable.
    4. Hard-coded paths to common editors.

    Raises an `UnsupportedPlatformError` if an editor cannot be determined.
    """
    options: typing.List[str] = []
    use_posix_style = True

    editor = editor or os.environ.get("VISUAL") or os.environ.get("EDITOR")

    if editor:
        (editor, *options) = shlex.split(editor, posix=(os.name == "posix"))

    if not editor:
        if os.name == "posix":
            editor = str(pathlib.Path("/usr/bin/editor").resolve()) or "vi"
        elif os.name == "nt":
            editor = "notepad.exe"
            line_number = None
            use_posix_style = False
        else:
            raise UnsupportedPlatformError(
                "Unable to determine what text editor to use.  "
                "Set the EDITOR environment variable.")

    if line_number:
        editor_name = pathlib.Path(os.path.basename(editor)).stem
        if editor_name in ("sublime_text", "subl", "code", "atom"):
            if editor_name == "code":
                options.append("--goto")
            file_path = f"{file_path}:{line_number}"
        elif editor_name in ("vi", "vim", "emacs", "xemacs", "nano", "pico",
                             "gedit"):
            options.append(f"+{line_number}")
        elif editor_name in ("notepad++",):
            options.append(f"-n{line_number}")
    if use_posix_style and file_path.startswith("-") and "--" not in options:
        options.append("--")

    subprocess.run((editor, *options, file_path), stdin=stdin, check=True)
