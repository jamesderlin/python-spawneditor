# spawneditor.py
#
# Copyright (C) 2020-2021 James D. Lin <jameslin@cal.berkeley.edu>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

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
