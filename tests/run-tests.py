#!/usr/bin/env python3

"""Unit tests for spawneditor."""

import itertools
import os
import pathlib
import tempfile
import typing
import unittest
import unittest.mock

import spawneditor


class FakePosixPath(pathlib.PurePosixPath):
    """
    Fake version of `pathlib.PosixPath` that can run on non-POSIX systems.
    """
    def exists(self) -> bool:
        """
        Implementation of `pathlib.PosixPath.exists` that ignores the existence
        of `/usr/bin/editor`.
        """
        return os.path.abspath(self) != "/usr/bin/editor"


def expect_edit_file(file_path: str,
                     *,
                     line_number: typing.Optional[int],
                     environment: typing.Dict[str, str],
                     expected_command: typing.Iterable[str],
                     editor: typing.Optional[str] = None,
                     os_name: str = "posix") -> None:
    """
    Verifies the behavior of `spawneditor.edit_file`, setting up necessary
    mocks.
    """
    with unittest.mock.patch("os.environ", environment), \
         unittest.mock.patch("os.name", os_name), \
         unittest.mock.patch("pathlib.Path", FakePosixPath), \
         unittest.mock.patch("subprocess.run") as mock_run:
        spawneditor.edit_file(file_path,
                              line_number=line_number,
                              editor=editor)
        mock_run.assert_called_once_with(expected_command,
                                         stdin=None,
                                         check=True)


def expect_edit_temporary(
        test_case: unittest.TestCase,
        *,
        content_lines: typing.Optional[typing.Iterable[str]] = None,
        temporary_prefix: typing.Optional[str] = None,
        line_number: typing.Optional[int] = None,
        editor: typing.Optional[str] = None,
        stdin: typing.Optional[typing.TextIO] = None) -> None:
    """
    Verifies the behavior of `spawn_editor.edit_tempoary`, setting up necessary
    mocks.
    """
    temp_file: typing.Optional[typing.IO[typing.Any]] = None
    original_temp_file = tempfile.NamedTemporaryFile

    expected_line_number = line_number
    expected_editor = editor
    expected_stdin = stdin

    output_lines = [
        "Lorem ipsum dolor sit amet,\n",
        "consectetur adipiscing elit.\n",
        "Cras dictum libero magna,\n",
        "at aliquet quam accumsan ultricies.\n",
        "Vestibulum efficitur eu.",  # Newline intentionally omitted.
    ]

    def temp_file_wrapper(*args: typing.Any,
                          **kwargs: typing.Any) -> typing.IO[typing.Any]:
        """
        A wrapper around `tempfile.NamedTemporaryFile` that captures the path
        to the temporary file.
        """
        nonlocal temp_file
        # pylint: disable=consider-using-with
        temp_file = original_temp_file(*args, **kwargs)
        return temp_file

    def fake_edit_file(file_path: str,
                       *,
                       line_number: typing.Optional[int] = None,
                       editor: typing.Optional[str] = None,
                       stdin: typing.Optional[typing.TextIO] = None) -> None:
        """
        Fake version of `spawneditor.edit_file` that verifies that it was
        called with the expected arguments, that the edited file has the
        expected content, and that writes predetermined output to the edited
        file.
        """
        if temporary_prefix is not None:
            test_case.assertTrue(
                os.path.basename(file_path).startswith(temporary_prefix))
        assert temp_file is not None
        test_case.assertEqual(file_path, temp_file.name)
        test_case.assertEqual(line_number, expected_line_number)
        test_case.assertEqual(editor, expected_editor)
        test_case.assertEqual(stdin, expected_stdin)

        # Verify the initial file contents.
        test_case.assertTrue(os.path.isfile(file_path))
        with open(file_path, "r") as f:
            test_case.assertEqual(
                f.read(),
                "\n".join(itertools.chain(content_lines, [""]))
                if content_lines else "")

        with open(file_path, "w") as f:
            f.writelines(output_lines)

    with unittest.mock.patch("tempfile.NamedTemporaryFile",
                             temp_file_wrapper), \
         unittest.mock.patch("spawneditor.edit_file",
                             side_effect=fake_edit_file,
                             autospec=True) as mock_edit:

        mock_manager = unittest.mock.Mock()
        mock_manager.attach_mock(mock_edit, "edit_file")

        lines = spawneditor.edit_temporary(content_lines,
                                           temporary_prefix=temporary_prefix,
                                           line_number=line_number,
                                           editor=editor)
        mock_manager.edit_file.assert_called_once()
        assert temp_file is not None
        test_case.assertTrue(temp_file.closed)
        test_case.assertFalse(os.path.isfile(temp_file.name))
        test_case.assertEqual(lines, output_lines)


# pylint: disable=no-self-use
class TestEditFile(unittest.TestCase):
    """Tests `spawneditor.edit_file`."""
    def test_basic_without_line(self) -> None:
        """Tests basic usage without a line number."""
        editor = "vi"
        file_path = "some_file.txt"
        expect_edit_file(file_path,
                         line_number=None,
                         environment={"EDITOR": editor},
                         expected_command=(editor, file_path))

    def test_basic_with_line(self) -> None:
        """Tests basic usage with a line number."""
        editor = "vi"
        file_path = "some_file.txt"
        line_number = 42
        expect_edit_file(file_path,
                         line_number=line_number,
                         environment={"EDITOR": editor},
                         expected_command=(editor,
                                           f"+{line_number}",
                                           file_path))

    def test_unrecognized_editor_with_line(self) -> None:
        """Tests that line numbers are ignored for unrecognized editors."""
        editor = "some_unrecognized_editor"
        file_path = "some_file.txt"
        line_number = 42
        expect_edit_file(file_path,
                         line_number=line_number,
                         environment={"EDITOR": editor},
                         expected_command=(editor, file_path))

    def test_arguments(self) -> None:
        """Tests that a full path and arguments to the editor are preserved."""
        editor = "/some/path with spaces/vi"
        file_path = "some_file.txt"
        line_number: typing.Optional[int] = None
        expect_edit_file(
            file_path,
            line_number=line_number,
            environment={"EDITOR": f"\"{editor}\" --one -2 three"},
            expected_command=(editor, "--one", "-2", "three", file_path))

        line_number = 42
        expect_edit_file(
            file_path,
            line_number=line_number,
            environment={"EDITOR": f"\"{editor}\" --one -2 three"},
            expected_command=(editor,
                              "--one",
                              "-2",
                              "three",
                              f"+{line_number}",
                              file_path))

    def test_hyphen_prefix(self) -> None:
        """
        Tests that file paths are tweaked to prevent file paths from starting
        with a hyphen.
        """
        editor = "vi"
        file_path = "-some_file.txt"
        line_number: typing.Optional[int] = None
        expect_edit_file(file_path,
                         line_number=line_number,
                         environment={"EDITOR": editor},
                         expected_command=(editor, f"./{file_path}"))

        line_number = 42
        expect_edit_file(file_path,
                         line_number=line_number,
                         environment={"EDITOR": editor},
                         expected_command=(editor,
                                           f"+{line_number}",
                                           f"./{file_path}"))

    def test_editor_identification(self) -> None:
        """
        Tests that file extensions and directories are ignored when identifying
        editors.
        """
        editor = "C:/Program Files/Sublime Text/subl.exe"
        file_path = "some_file.txt"
        line_number = 42
        expect_edit_file(file_path,
                         line_number=line_number,
                         environment={"EDITOR": f"\"{editor}\" --wait"},
                         expected_command=(editor,
                                           "--wait",
                                           f"{file_path}:{line_number}"))

    def test_precedence(self) -> None:
        """Tests that the editor is chosen in the expected order."""
        file_path = "some_file.txt"
        line_number = 42
        editor = "some_editor"
        visual = "some_visual_editor"
        explicit_editor = "explicit_editor"

        fake_environment: typing.Dict[str, str] = {}
        expect_edit_file(file_path,
                         line_number=line_number,
                         environment=fake_environment,
                         expected_command=("vi", f"+{line_number}", file_path))

        fake_environment["EDITOR"] = editor
        expect_edit_file(file_path,
                         line_number=line_number,
                         environment=fake_environment,
                         expected_command=("some_editor", file_path))

        fake_environment["VISUAL"] = visual
        expect_edit_file(file_path,
                         line_number=line_number,
                         environment=fake_environment,
                         expected_command=(editor, file_path))

        fake_environment["DISPLAY"] = ":0.0"
        expect_edit_file(file_path,
                         line_number=line_number,
                         environment=fake_environment,
                         expected_command=(visual, file_path))

        expect_edit_file(file_path,
                         line_number=line_number,
                         environment=fake_environment,
                         expected_command=(explicit_editor, file_path),
                         editor=explicit_editor)


class TestEditTemporary(unittest.TestCase):
    """Tests `spawneditor.edit_temporary`."""
    def test_basic(self) -> None:
        """Tests basic usage with default arguments."""
        expect_edit_temporary(self)

    def test_with_content(self) -> None:
        """Tests usage with initial instructions."""
        instructions = ["Do some stuff below the line.", "---"]
        expect_edit_temporary(self,
                              content_lines=instructions,
                              line_number=len(instructions) + 1)


if __name__ == "__main__":
    unittest.main()
