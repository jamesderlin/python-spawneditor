# spawneditor

A Python module that attempts to provide a common interface for opening an
editor at a specified line in a file.

The launched editor will be chosen from, in order:

1. The explicitly specified editor.
2. The `VISUAL` environment variable, if `DISPLAY` is available.
3. The `EDITOR` environment variable.
4. Hard-coded paths to common editors.


## Installation

```shell
pip install --user spawneditor
```

Alternatively clone the Git repository as a Git submodule named `spawneditor`.


## Examples

```python
import spawneditor

# Open an existing file in the default editor.
spawneditor.edit_file("path/to/file.txt")

# A line number may be specified.
spawneditor.edit_file("path/to/file.txt", line_number=123)

# Edits a blank temporary file.
edited_lines = spawneditor.edit_temporary()  

# Edits a temporary file with specified content.  Unlike `edit_file`,
# `edit_temporary` returns the contents of the edited file.
instructions = [
    "Instructions:",
    "Enter some text below the line.",
    "----",
]
new_contents = spawneditor.edit_temporary(instructions,
                                          line_number=(len(instructions) + 1))

# ... or, if you prefer a single string with newlines:
new_contents = spawneditor.edit_temporary(
    sss["Instructions:\nEnter some text below the line.\n----"],
    line_number=4,
)

for line in new_contents:
    print(line, end="")
```


## FAQ

### Q: How does `spawneditor` know how to invoke the editor at a specified line number? 

`spawneditor` is hard-coded to recognize and invoke some common editors based on
the name of the executed binary.


### Q: What is considered a "common editor"?

See the `editor_syntax_table` in [`spawneditor.py`].


### Q: What if my editor isn't supported?

Other editors should still work.  At worst, the specified file should be opened
in the default editor, just not at the specified line.

If your editor isn't supported, I also encourage filing an issue or pull request
to add support.


### Q: Why not provide some mechanism for end-users to specify the syntax for their editor?

It's tempting to support using, say, a configuration file to allow users to
specify how to invoke arbitrary editors.  I currently prefer not to because:
* It adds code complexity and incurs a penalty for what is likely to be a rare
  situation.
* It reduces incentives to make `spawneditor` support other editors directly.
* The fallback behavior of opening the file in the default editor (just not at
  the specified line number) should be acceptable.

One pathological situation where an override would be necessary is if an editor
uses the same executable name as one of the recognized editors *and* uses a
different command-line syntax for specifying the line number.  However, that
also should be a very rare situation.


### Q: Why does `spawneditor.edit_file` immediately return when spawning a multi-document editor (e.g. Visual Studio Code, Sublime Text)?

Multi-document editors are typically also *single-instance*: when the editor is
invoked, a new process will be spawned, but that process then will forward the
request to an existing, primary process.  The new, secondary process then will
immediately exit and cause `spawneditor.edit_file` to return.  Such editors typically
provide a command-line option (e.g. `--wait` for Visual Studio Code and Sublime
Text) to keep the secondary process alive until the file is closed by the
primary process.  Consult the documentation to your editor.


### Q: Aren't there already Python packages that do this?

Yes.  The [`editor`] and [`python-editor`] packages are alternatives that also
invoke the default editor.  Currently neither one supports opening a file to a
specified line number.  Were I aware of them when I wrote `spawneditor`, and
possibly I would have tried contributing to them instead.  However,
`spawneditor` is implemented rather differently than either one, and I'm not
sure that either project would have appreciated drastic changes.  There likely
is room for cross-pollination.

---

Copyright © 2020-2021 James D. Lin.

[`spawneditor.py`]: https://github.com/jamesderlin/python-spawneditor/blob/master/spawneditor.py
[`editor`]: https://pypi.org/project/editor/
[`python-editor`]: https://pypi.org/project/python-editor/
