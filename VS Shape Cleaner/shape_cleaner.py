#!/usr/bin/env python3
"""
Vintage Story Shape Cleaner

Cleans Vintage Story shape JSON files without parsing/reformatting/re-serializing
the JSON. The file is edited as raw text so existing formatting, indentation,
spacing, ordering, and line endings are preserved.

Cleans:
  1. "windMode": [...] properties from face objects.
  2. Single-line face entries whose object contains "enabled": false.
  3. Empty object properties such as "faces": {} and "textureSizes": {}.
  4. An empty trailing "animations": [] property.
  5. Missing domains in the "textures" object by adding "game:".

Usage:
  - Open the .bat launcher.
  - Drag and drop one or more .json / .jsonc files onto the window.
  - The window stays open and can receive files indefinitely.
"""

from __future__ import annotations

import json
import re
import shutil
import sys
from pathlib import Path

import tkinter as tk

from tkinterdnd2 import DND_FILES, TkinterDnD


# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------

# A backup is made before changing the original.
CREATE_BACKUP = True


# ---------------------------------------------------------------------------
# Patterns
# ---------------------------------------------------------------------------

# Removes:
#     , "windMode": [-1,-1,-1,-1]
#
# This intentionally only operates on a single line.
WIND_MODE_RE = re.compile(
    r',\s*"windMode"\s*:\s*\[[^\]\r\n]*\]'
)


# Matches a single-line JSON object property such as:
#     "down": { "texture": "#null", "uv": [...], "enabled": false }
#
# The entire property line is removed, including its trailing comma.
ENABLED_FALSE_LINE_RE = re.compile(
    r'^\s*"[^"\r\n]+":\s*\{'
    r'[^\{\}\r\n]*"enabled"\s*:\s*false[^\{\}\r\n]*\},?\s*'
    r'(?:\r?\n)?$'
)


# Matches an empty object property:
#
#     "textureSizes": {
#     },
#
# and collapses it into:
#
#     "textureSizes": {},
#
# This works for any property containing an actually empty object.
EMPTY_OBJECT_RE = re.compile(
    r'^(?P<indent>[ \t]*)'
    r'"(?P<name>[^"\r\n]+)"\s*:\s*\{'
    r'[ \t]*(?:\r?\n)?'
    r'[ \t]*\}'
    r'(?P<comma>,?)'
    r'[ \t]*(?:\r?\n)?$',
    re.MULTILINE,
)


def make_backup(path: Path) -> Path:
    """
    Create an incrementing backup next to the original file.

    Example:
        shape.json
        shape-backup1.json
        shape-backup2.json
        shape-backup3.json
    """

    counter = 1

    while True:
        backup = path.with_name(
            f"{path.stem}-backup{counter}{path.suffix}"
        )

        if not backup.exists():
            shutil.copy2(path, backup)
            return backup

        counter += 1


def collapse_empty_objects(text: str) -> tuple[str, int]:
    """
    Collapse empty multiline JSON objects.

    Example:

        "textureSizes": {
        },

    becomes:

        "textureSizes": {},

    This only collapses an object when its opening and closing braces are
    on consecutive lines.
    """

    lines = text.splitlines(keepends=True)

    collapsed_lines: list[str] = []
    count = 0
    i = 0

    while i < len(lines):
        if i + 1 < len(lines):
            opening_match = re.match(
                r'^([ \t]*)"([^"\r\n]+)"[ \t]*:[ \t]*\{[ \t]*(?:\r?\n)?$',
                lines[i],
            )

            closing_match = re.match(
                r'^[ \t]*\}([ \t]*,?)[ \t]*(?:\r?\n)?$',
                lines[i + 1],
            )

            if opening_match and closing_match:
                indent = opening_match.group(1)
                name = opening_match.group(2)

                closing_line = lines[i + 1]

                has_comma = bool(
                    re.search(r'\}[ \t]*,', closing_line)
                )

                comma = "," if has_comma else ""

                # Preserve the original line-ending style.
                if lines[i].endswith("\r\n"):
                    newline = "\r\n"
                elif lines[i].endswith("\n"):
                    newline = "\n"
                elif lines[i + 1].endswith("\r\n"):
                    newline = "\r\n"
                elif lines[i + 1].endswith("\n"):
                    newline = "\n"
                else:
                    newline = ""

                collapsed_lines.append(
                    f'{indent}"{name}": ' + "{}" + comma + newline
                )

                count += 1
                i += 2
                continue

        collapsed_lines.append(lines[i])
        i += 1

    return "".join(collapsed_lines), count

    """
    Collapse empty multiline JSON objects.

    Example:

        "textureSizes": {
        },

    becomes:

        "textureSizes": {},

    This only collapses an object when its opening and closing braces are
    on consecutive lines.
    """

    lines = text.splitlines(keepends=True)

    collapsed_lines: list[str] = []
    count = 0
    i = 0

    while i < len(lines):
        if i + 1 < len(lines):
            opening_match = re.match(
                r'^([ \t]*)"([^"\r\n]+)"[ \t]*:[ \t]*\{[ \t]*(?:\r?\n)?$',
                lines[i],
            )

            closing_match = re.match(
                r'^[ \t]*\}([ \t]*,?)[ \t]*(?:\r?\n)?$',
                lines[i + 1],
            )

            if opening_match and closing_match:
                indent = opening_match.group(1)
                name = opening_match.group(2)

                # Preserve the comma from the closing line.
                closing_line = lines[i + 1]
                has_comma = bool(
                    re.search(r'\}[ \t]*,', closing_line)
                )

                comma = "," if has_comma else ""

                # Preserve the original line ending.
                if lines[i].endswith("\r\n"):
                    newline = "\r\n"
                elif lines[i].endswith("\n"):
                    newline = "\n"
                elif lines[i + 1].endswith("\r\n"):
                    newline = "\r\n"
                elif lines[i + 1].endswith("\n"):
                    newline = "\n"
                else:
                    newline = ""

                collapsed_lines.append(
                    f'{indent}"{name}": {{{comma}}}{newline}'
                )

                count += 1
                i += 2
                continue

        collapsed_lines.append(lines[i])
        i += 1

    return "".join(collapsed_lines), count

    """
    Collapse empty multiline JSON objects.

    Example:

        "textureSizes": {
        },

    becomes:

        "textureSizes": {},

    This only collapses objects where the opening and closing braces are
    directly adjacent with no properties between them.
    """

    lines = text.splitlines(keepends=True)

    collapsed_lines: list[str] = []
    count = 0
    i = 0

    while i < len(lines):
        # Look for:
        #
        #     "textureSizes": {
        #     },
        #
        # or any other property with an empty object.
        if i + 1 < len(lines):
            opening_match = re.match(
                r'^(?P<indent>[ \t]*)'
                r'"(?P<name>[^"\r\n]+)"\s*:\s*\{\s*'
                r'(?:\r?\n)?$',
                lines[i],
            )

            closing_match = re.match(
                r'^(?P<closing_indent>[ \t]*)'
                r'\}(?P<comma>,?)'
                r'[ \t]*(?:\r?\n)?$',
                lines[i + 1],
            )

            if opening_match and closing_match:
                indent = opening_match.group("indent")
                name = opening_match.group("name")
                comma = closing_match.group("comma")

                # Preserve the line-ending style.
                if lines[i].endswith("\r\n"):
                    newline = "\r\n"
                elif lines[i].endswith("\n"):
                    newline = "\n"
                elif lines[i + 1].endswith("\r\n"):
                    newline = "\r\n"
                elif lines[i + 1].endswith("\n"):
                    newline = "\n"
                else:
                    newline = ""

                collapsed_lines.append(
                    f'{indent}"{name}": {{{{}}}}{comma}{newline}'.replace(
                        "{{{{}}}}",
                        "{}",
                    )
                )

                count += 1
                i += 2
                continue

        collapsed_lines.append(lines[i])
        i += 1

    return "".join(collapsed_lines), count

    """
    Collapse empty multiline JSON objects.

    Example:

        "textureSizes": {
        },

    becomes:

        "textureSizes": {},

    Existing indentation, comma, and line ending style are preserved.
    """

    count = 0

    def replace(match: re.Match[str]) -> str:
        nonlocal count
        count += 1

        indent = match.group("indent")
        name = match.group("name")
        comma = match.group("comma")

        # Determine the line-ending style from the matched text.
        full_match = match.group(0)

        if "\r\n" in full_match:
            newline = "\r\n"
        elif "\n" in full_match:
            newline = "\n"
        else:
            newline = ""

        return f'{indent}"{name}": {{{{}}}}{comma}{newline}'.replace(
            "{{{{}}}}",
            "{}",
        )

    return EMPTY_OBJECT_RE.sub(replace, text), count


def add_game_domain_to_textures(text: str) -> tuple[str, int]:
    """
    Add the "game:" domain to texture paths inside the root "textures" object.

    Example:

        "textures": {
            "rustyglow": "block/machine/statictranslocator/rustyglow",
            "cupronickel1": "block/metal/sheet/cupronickel1"
        }

    becomes:

        "textures": {
            "rustyglow": "game:block/machine/statictranslocator/rustyglow",
            "cupronickel1": "game:block/metal/sheet/cupronickel1"
        }

    Existing domains such as "game:", "purposefulstorage:", etc. are left alone.

    Returns:
        (cleaned_text, number_of_textures_changed)
    """

    # Match the textures object itself.
    #
    # Shape texture values are simple strings, so this intentionally keeps
    # the matcher restricted to lines inside the textures object.
    textures_re = re.compile(
        r'(?P<header>^[ \t]*"textures"\s*:\s*\{\s*(?:\r?\n)?)'
        r'(?P<body>'
        r'(?:'
        r'^[ \t]*"[^"\r\n]+"\s*:\s*"[^"\r\n]*"\s*,?[ \t]*(?:\r?\n)?'
        r')*'
        r')'
        r'(?P<closing>^[ \t]*\}[ \t]*,?[ \t]*(?:\r?\n)?)',
        re.MULTILINE,
    )

    # A texture value that does NOT already start with a domain.
    #
    # Valid existing examples:
    #     game:block/...
    #     purposefulstorage:block/...
    #     somethingelse:foo/...
    #
    # Invalid / missing domain:
    #     block/...
    TEXTURE_VALUE_RE = re.compile(
        r'(?P<prefix>'
        r'^[ \t]*"[^"\r\n]+"\s*:\s*"'
        r')'
        r'(?P<path>'
        r'(?![A-Za-z0-9_.-]+:)[^"\r\n]*'
        r')'
        r'(?P<suffix>"[ \t]*,?[ \t]*(?:\r?\n)?)',
        re.MULTILINE,
    )

    changed_count = 0

    def replace_textures(match: re.Match[str]) -> str:
        nonlocal changed_count

        body = match.group("body")

        def replace_texture_value(
            texture_match: re.Match[str],
        ) -> str:
            nonlocal changed_count

            changed_count += 1

            return (
                texture_match.group("prefix")
                + "game:"
                + texture_match.group("path")
                + texture_match.group("suffix")
            )

        body = TEXTURE_VALUE_RE.sub(
            replace_texture_value,
            body,
        )

        return (
            match.group("header")
            + body
            + match.group("closing")
        )

    cleaned = textures_re.sub(
        replace_textures,
        text,
    )

    return cleaned, changed_count


def remove_empty_trailing_animations(text: str) -> tuple[str, int]:
    """
    Remove an empty trailing "animations": [] property.

    Example:

        "elements": [
            ...
        ],
        "animations": [
        ]
    }

    becomes:

        "elements": [
            ...
        ]

    This only removes animations when it is the final property before the
    root object's closing brace and contains no entries.
    """

    # Look specifically for:
    #
    #     "animations": [
    #     ]
    # }
    #
    # where animations is the final root-level property.

    match = re.search(
        r'(?P<before>,[ \t]*\r?\n)'
        r'(?P<indent>[ \t]*)"animations"\s*:\s*\['
        r'[ \t]*(?:\r?\n)?'
        r'[ \t]*\]'
        r'[ \t]*(?:\r?\n)?'
        r'(?P<closing>[ \t]*\})'
        r'[ \t]*$',
        text,
    )

    if match is None:
        # Also support the compact:
        #
        #     ,"animations": [] }
        #
        match = re.search(
            r'(?P<before>,[ \t]*)'
            r'"animations"\s*:\s*\[\s*\]'
            r'[ \t]*(?P<closing>\})'
            r'[ \t]*$',
            text,
        )

    if match is None:
        return text, 0

    # Remove the comma belonging to the property immediately before
    # "animations", as well as the entire animations property.
    #
    # Keep the closing root brace.
    cleaned = (
        text[:match.start("before")]
        + match.group("closing")
    )

    return cleaned, 1


def clean_shape_file(path: Path) -> tuple[int, int, int, int, int, Path | None]:
    """
    Clean one shape file in-place.

    Returns:
        (
            wind_mode_count,
            enabled_false_count,
            empty_objects_count,
            textures_domain_count,
            animations_removed,
            backup_path
        )
    """

    # Read raw bytes so line endings and BOM can be preserved exactly.
    with path.open("rb") as f:
        raw = f.read()

    # Preserve an existing UTF-8 BOM exactly as it was.
    has_bom = raw.startswith(b"\xef\xbb\xbf")
    original_bytes = raw[3:] if has_bom else raw
    original = original_bytes.decode("utf-8")

    # -------------------------------------------------------------------
    # 1. Remove windMode
    # -------------------------------------------------------------------

    wind_mode_count = len(
        WIND_MODE_RE.findall(original)
    )

    text = WIND_MODE_RE.sub(
        "",
        original,
    )

    # -------------------------------------------------------------------
    # 2. Remove enabled:false face entries
    # -------------------------------------------------------------------

    lines = text.splitlines(keepends=True)

    kept_lines: list[str] = []
    enabled_false_count = 0

    for line in lines:
        if ENABLED_FALSE_LINE_RE.match(line):
            enabled_false_count += 1
            continue

        kept_lines.append(line)

    # If an enabled:false entry was the last property in an object, its
    # previous surviving property may still have a trailing comma:
    #
    #     "up": { ... },
    #     "down": { ... enabled:false }
    #
    # becomes:
    #
    #     "up": { ... }
    #
    # Only a comma immediately before a closing brace is touched.
    for i in range(len(kept_lines) - 1):
        next_line = kept_lines[i + 1]

        if re.match(r'^\s*}', next_line):
            current_line = kept_lines[i].rstrip("\r\n").rstrip()

            if current_line.endswith("{") or current_line.endswith("["):
                continue

            kept_lines[i] = re.sub(
                r',(\s*(?:\r?\n)?)$',
                r'\1',
                kept_lines[i],
                count=1,
            )

    text = "".join(kept_lines)

    # -------------------------------------------------------------------
    # 3. Collapse empty objects
    # -------------------------------------------------------------------

    text, empty_objects_count = collapse_empty_objects(text)

    # -------------------------------------------------------------------
    # 4. Add game: to texture paths without a domain
    # -------------------------------------------------------------------

    text, textures_domain_count = add_game_domain_to_textures(text)

    # -------------------------------------------------------------------
    # 5. Remove empty trailing animations
    # -------------------------------------------------------------------

    text, animations_removed = remove_empty_trailing_animations(text)

    # -------------------------------------------------------------------
    # Validate
    # -------------------------------------------------------------------

    # Validate the resulting JSON before touching the original file.
    # This does not serialize it; it is only a safety check.
    try:
        json.loads(text)
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            "The cleaned result did not pass JSON validation, so the original "
            "file was NOT changed.\n\n"
            f"JSON error: {exc}"
        ) from exc

    # Nothing actually changed.
    if text == original:
        return (
            wind_mode_count,
            enabled_false_count,
            empty_objects_count,
            textures_domain_count,
            animations_removed,
            None,
        )

    # -------------------------------------------------------------------
    # Backup + write
    # -------------------------------------------------------------------

    backup_path = make_backup(path) if CREATE_BACKUP else None

    cleaned_bytes = text.encode("utf-8")

    if has_bom:
        cleaned_bytes = b"\xef\xbb\xbf" + cleaned_bytes

    with path.open("wb") as f:
        f.write(cleaned_bytes)

    return (
        wind_mode_count,
        enabled_false_count,
        empty_objects_count,
        textures_domain_count,
        animations_removed,
        backup_path,
    )


# ---------------------------------------------------------------------------
# GUI
# ---------------------------------------------------------------------------

class ShapeCleanerApp:
    def __init__(self, root: TkinterDnD.Tk):
        self.root = root

        self.root.title("Vintage Story Shape Cleaner")
        self.root.geometry("720x500")
        self.root.minsize(560, 400)

        # ---------------------------------------------------------------
        # Main frame
        # ---------------------------------------------------------------

        main = tk.Frame(root, padx=20, pady=20)
        main.pack(fill="both", expand=True)

        title = tk.Label(
            main,
            text="Vintage Story Shape Cleaner",
            font=("Segoe UI", 18, "bold"),
        )
        title.pack(pady=(0, 5))

        subtitle = tk.Label(
            main,
            text="Drag and drop .json / .jsonc shape files here",
            font=("Segoe UI", 10),
        )
        subtitle.pack(pady=(0, 15))

        # ---------------------------------------------------------------
        # Drop area
        # ---------------------------------------------------------------

        self.drop_area = tk.Frame(
            main,
            relief="groove",
            borderwidth=2,
            height=130,
        )
        self.drop_area.pack(fill="x", pady=(0, 15))
        self.drop_area.pack_propagate(False)

        drop_label = tk.Label(
            self.drop_area,
            text="DROP FILES HERE",
            font=("Segoe UI", 16, "bold"),
        )
        drop_label.pack(expand=True)

        drop_hint = tk.Label(
            self.drop_area,
            text="You can keep dropping files here as long as this window is open.",
            font=("Segoe UI", 9),
        )
        drop_hint.pack(pady=(0, 20))

        # Register the drop area and its children.
        self.drop_area.drop_target_register(DND_FILES)
        self.drop_area.dnd_bind("<<Drop>>", self.on_drop)

        drop_label.drop_target_register(DND_FILES)
        drop_label.dnd_bind("<<Drop>>", self.on_drop)

        drop_hint.drop_target_register(DND_FILES)
        drop_hint.dnd_bind("<<Drop>>", self.on_drop)

        # ---------------------------------------------------------------
        # Log
        # ---------------------------------------------------------------

        log_frame = tk.Frame(main)
        log_frame.pack(fill="both", expand=True)

        self.log = tk.Text(
            log_frame,
            wrap="word",
            state="disabled",
            font=("Consolas", 9),
        )
        self.log.pack(
            side="left",
            fill="both",
            expand=True,
        )

        scrollbar = tk.Scrollbar(
            log_frame,
            command=self.log.yview,
        )
        scrollbar.pack(
            side="right",
            fill="y",
        )

        self.log.configure(yscrollcommand=scrollbar.set)

        self.write_log(
            "Ready. Drop a Vintage Story shape file above.\n"
        )

        # ---------------------------------------------------------------
        # Buttons
        # ---------------------------------------------------------------

        button_frame = tk.Frame(main)
        button_frame.pack(fill="x", pady=(12, 0))

        clear_button = tk.Button(
            button_frame,
            text="Clear Log",
            command=self.clear_log,
        )
        clear_button.pack(side="right")

    # -------------------------------------------------------------------
    # Logging
    # -------------------------------------------------------------------

    def write_log(self, message: str) -> None:
        self.log.configure(state="normal")
        self.log.insert("end", message)
        self.log.see("end")
        self.log.configure(state="disabled")

    def clear_log(self) -> None:
        self.log.configure(state="normal")
        self.log.delete("1.0", "end")
        self.log.configure(state="disabled")

    # -------------------------------------------------------------------
    # Drag & Drop
    # -------------------------------------------------------------------

    def on_drop(self, event) -> None:
        """
        Receive files dropped onto the window.

        tkinterdnd2 provides the dropped paths through event.data.
        splitlist() is used because Windows paths may contain spaces.
        """

        try:
            dropped_files = self.root.tk.splitlist(event.data)
        except Exception:
            dropped_files = [event.data]

        for filename in dropped_files:
            path = Path(filename)

            # Ignore directories.
            if not path.is_file():
                self.write_log(
                    f"[IGNORED] Not a file:\n{path}\n\n"
                )
                continue

            self.process_file(path)

    # -------------------------------------------------------------------
    # File processing
    # -------------------------------------------------------------------

    def process_file(self, path: Path) -> None:
        self.write_log(
            f"Cleaning:\n{path}\n"
        )

        try:
            (
                wind_count,
                enabled_count,
                empty_objects_count,
                textures_domain_count,
                animations_removed,
                backup,
            ) = clean_shape_file(path)

            if (
                wind_count == 0
                and enabled_count == 0
                and empty_objects_count == 0
                and textures_domain_count == 0
                and animations_removed == 0
            ):
                self.write_log(
                    "  Nothing to clean.\n\n"
                )
                return

            self.write_log(
                f"  windMode removed: {wind_count}\n"
                f"  enabled: false entries removed: {enabled_count}\n"
                f"  empty objects collapsed: {empty_objects_count}\n"
                f"  texture domains added: {textures_domain_count}\n"
                f"  empty animations removed: {animations_removed}\n"
            )

            if backup is not None:
                self.write_log(
                    f"  Backup:\n"
                    f"  {backup}\n"
                )

            self.write_log(
                "  ✓ Cleaned successfully.\n\n"
            )

        except Exception as exc:
            self.write_log(
                f"  ✗ ERROR:\n"
                f"  {exc}\n\n"
            )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    root = TkinterDnD.Tk()

    app = ShapeCleanerApp(root)

    # If files were supplied to the .bat / Python script directly,
    # process them when the GUI opens.
    paths = [Path(arg) for arg in sys.argv[1:]]

    for path in paths:
        if path.is_file():
            app.process_file(path)
        else:
            app.write_log(
                f"[IGNORED] File not found:\n{path}\n\n"
            )

    root.mainloop()


if __name__ == "__main__":
    main()
