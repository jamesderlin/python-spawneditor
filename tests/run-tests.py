#!/usr/bin/env python3

"""Unit tests for spawneditor."""

import os
import pathlib
import typing
import unittest
import unittest.mock

import spawneditor


class FakePosixPath(pathlib.PurePosixPath):
    """
    Fake version of `pathlib.PosixPath` that can run on non-POSIX systems.
    """
    def exists(self):
        """
        Implementation of `pathlib.PosixPath.exists` that ignores the existence
        of `/usr/bin/editor`.
        """
        return os.path.abspath(self) != "/usr/bin/editor"


def expect_spawn_editor(file_path: str,
                        line_number: typing.Optional[int],
                        fake_environment: typing.Dict[str, str],
                        expected_command: typing.Iterable[str],
                        editor: typing.Optional[str] = None,
                        os_name="posix") -> None:
    """
    Verifies the behavior of `spawneditor.spawn_editor`, setting up necesary
    mocks.
    """
    with unittest.mock.patch("os.environ", fake_environment), \
         unittest.mock.patch("os.name", os_name), \
         unittest.mock.patch("pathlib.Path", FakePosixPath), \
         unittest.mock.patch("subprocess.run") as mock_run:
        spawneditor.spawn_editor(file_path, line_number=line_number,
                                 editor=editor)
        mock_run.assert_called_once_with(expected_command,
                                         stdin=None, check=True)


# pylint: disable=no-self-use
class TestSpawnEditor(unittest.TestCase):
    """Tests `spawneditor.spawn_editor`."""
    def test_basic_without_line(self) -> None:
        """Tests basic usage without a line number."""
        editor = "vi"
        file_path = "some_file.txt"
        expect_spawn_editor(file_path,
                            None,
                            {"EDITOR": editor},
                            (editor, file_path))

    def test_basic_with_line(self) -> None:
        """Tests basic usage with a line number."""
        editor = "vi"
        file_path = "some_file.txt"
        line_number = 42
        expect_spawn_editor(file_path,
                            line_number,
                            {"EDITOR": editor},
                            (editor, f"+{line_number}", file_path))

    def test_unrecognized_editor_with_line(self) -> None:
        """Tests that line numbers are ignored for unrecognized editors."""
        editor = "some_unrecognized_editor"
        file_path = "some_file.txt"
        line_number = 42
        expect_spawn_editor(file_path,
                            line_number,
                            {"EDITOR": editor},
                            (editor, file_path))

    def test_arguments(self) -> None:
        """Tests that a full path and arguments to the editor are preserved."""
        editor = "/some/path with spaces/vi"
        file_path = "some_file.txt"
        line_number: typing.Optional[int] = None
        expect_spawn_editor(file_path,
                            line_number,
                            {"EDITOR": f"\"{editor}\" --one -2 three"},
                            (editor, "--one", "-2", "three", file_path))

        line_number = 42
        expect_spawn_editor(file_path,
                            line_number,
                            {"EDITOR": f"\"{editor}\" --one -2 three"},
                            (editor, "--one", "-2", "three",
                             f"+{line_number}", file_path))

    def test_hyphen_prefix(self) -> None:
        """
        Tests that file paths are tweaked to prevent file paths from starting
        with a hyphen.
        """
        editor = "vi"
        file_path = "-some_file.txt"
        line_number: typing.Optional[int] = None
        expect_spawn_editor(file_path,
                            line_number,
                            {"EDITOR": editor},
                            (editor, f"./{file_path}"))

        line_number = 42
        expect_spawn_editor(file_path,
                            line_number,
                            {"EDITOR": editor},
                            (editor, f"+{line_number}", f"./{file_path}"))

    def test_editor_identification(self) -> None:
        """
        Tests that file extensions and directories are ignored when identifying
        editors.
        """
        editor = "C:/Program Files/Sublime Text/subl.exe"
        file_path = "some_file.txt"
        line_number = 42
        expect_spawn_editor(file_path,
                            line_number,
                            {"EDITOR": f"\"{editor}\" --wait"},
                            (editor, "--wait", f"{file_path}:{line_number}"))

    def test_precedence(self) -> None:
        """Tests that the editor is chosen in the expected order."""
        file_path = "some_file.txt"
        line_number = 42
        editor = "some_editor"
        visual = "some_visual_editor"
        explicit_editor = "explicit_editor"

        fake_environment: typing.Dict[str, str] = {}
        expect_spawn_editor(file_path,
                            line_number,
                            fake_environment,
                            ("vi", f"+{line_number}", file_path))

        fake_environment["EDITOR"] = editor
        expect_spawn_editor(file_path,
                            line_number,
                            fake_environment,
                            ("some_editor", file_path))

        fake_environment["VISUAL"] = visual
        expect_spawn_editor(file_path,
                            line_number,
                            fake_environment,
                            (editor, file_path))

        fake_environment["DISPLAY"] = ":0.0"
        expect_spawn_editor(file_path,
                            line_number,
                            fake_environment,
                            (visual, file_path))

        expect_spawn_editor(file_path,
                            line_number,
                            fake_environment,
                            (explicit_editor, file_path),
                            editor=explicit_editor)


if __name__ == "__main__":
    unittest.main()
