"""
terminal_text_editor.py
=======================
A fully‑featured, cross‑platform terminal text editor.

Works on  Windows (Python 3.6+)  and  Linux / macOS  with NO extra packages.
Uses raw ANSI escape codes for rendering and platform‑specific raw‑key input:
  • Windows  – msvcrt.getwch()
  • Unix      – termios + tty raw mode

Modes
-----
  NORMAL  – navigate & run commands  (vim‑style, default)
  INSERT  – type text freely
  COMMAND – enter : commands in the status bar
  SEARCH  – enter /pattern

Key bindings (NORMAL mode)
--------------------------
  h j k l  / Arrow keys   move cursor
  i                        enter INSERT mode
  a                        INSERT after cursor
  o / O                    open new line below / above
  x                        delete character under cursor
  dd                       delete current line
  u                        undo  (up to 50 levels)
  Ctrl+R                   redo
  G  /  gg                 jump to last / first line
  0  /  $                  start / end of line
  PgUp / PgDn              scroll by page
  /                        search mode
  n / N                    next / previous search match
  :                        command mode

COMMAND mode  (:...)
--------------------
  :w [file]   save / save-as
  :q          quit  (blocks if unsaved)
  :q!         force quit
  :wq  :x     save and quit
  :o <file>   open file
  :new        new empty buffer
  :set nu     toggle line numbers
  :goto <n>   jump to line n
  :help       show help overlay
"""

from __future__ import annotations

import os
import sys
import copy
from enum import Enum, auto
from typing import Optional

# ──────────────────────────────────────────────
# Platform detection & raw-terminal bootstrap
# ──────────────────────────────────────────────

IS_WINDOWS = sys.platform == "win32"

if IS_WINDOWS:
    import msvcrt
    import ctypes
    import ctypes.wintypes

    def _enable_ansi_windows() -> None:
        """Enable VIRTUAL_TERMINAL_PROCESSING on the Windows console."""
        ENABLE_VIRTUAL_TERMINAL_PROCESSING = 0x0004
        kernel32 = ctypes.windll.kernel32
        # stdout
        hOut = kernel32.GetStdHandle(ctypes.c_ulong(-11))
        mode = ctypes.wintypes.DWORD(0)
        kernel32.GetConsoleMode(hOut, ctypes.byref(mode))
        kernel32.SetConsoleMode(hOut, mode.value | ENABLE_VIRTUAL_TERMINAL_PROCESSING)

else:
    import tty
    import termios
    import select

# ──────────────────────────────────────────────
# ANSI helpers
# ──────────────────────────────────────────────

ESC = "\x1b"


class A:
    """ANSI escape-code factory."""
    RESET       = f"{ESC}[0m"
    BOLD        = f"{ESC}[1m"
    HIDE_CUR    = f"{ESC}[?25l"
    SHOW_CUR    = f"{ESC}[?25h"
    ALT_SCREEN  = f"{ESC}[?1049h"
    NORM_SCREEN = f"{ESC}[?1049l"
    CLEAR       = f"{ESC}[2J"
    ERASE_EOL   = f"{ESC}[K"

    # Foreground
    FG_BLACK  = f"{ESC}[30m"
    FG_RED    = f"{ESC}[91m"
    FG_YELLOW = f"{ESC}[93m"
    FG_BLUE   = f"{ESC}[94m"
    FG_CYAN   = f"{ESC}[96m"

    # Background
    BG_WHITE  = f"{ESC}[107m"
    BG_CYAN   = f"{ESC}[46m"
    BG_GREEN  = f"{ESC}[42m"
    BG_YELLOW = f"{ESC}[43m"

    @staticmethod
    def move(row: int, col: int) -> str:
        """1-indexed absolute cursor position."""
        return f"{ESC}[{row};{col}H"


def term_size() -> tuple[int, int]:
    """Return (rows, cols), falling back to 24x80."""
    try:
        sz = os.get_terminal_size()
        return sz.lines, sz.columns
    except OSError:
        return 24, 80


# ──────────────────────────────────────────────
# Special key constants
# ──────────────────────────────────────────────

class Key:
    UP        = "<UP>"
    DOWN      = "<DOWN>"
    LEFT      = "<LEFT>"
    RIGHT     = "<RIGHT>"
    HOME      = "<HOME>"
    END       = "<END>"
    PGUP      = "<PGUP>"
    PGDN      = "<PGDN>"
    DELETE    = "<DEL>"
    BACKSPACE = "<BS>"
    ENTER     = "<ENTER>"
    ESC       = "<ESC>"
    CTRL_R    = "<C-R>"
    CTRL_S    = "<C-S>"
    CTRL_Q    = "<C-Q>"
    UNKNOWN   = "<UNKNOWN>"


# ──────────────────────────────────────────────
# Cross-platform raw key reader
# ──────────────────────────────────────────────

class KeyReader:
    """
    Reads one logical keypress.
    Returns a single printable character string, or a Key.* constant.
    """

    _WIN_EXT: dict[str, str] = {
        "H": Key.UP,    "P": Key.DOWN,
        "K": Key.LEFT,  "M": Key.RIGHT,
        "G": Key.HOME,  "O": Key.END,
        "I": Key.PGUP,  "Q": Key.PGDN,
        "S": Key.DELETE,
    }

    def read(self) -> str:
        return self._read_win() if IS_WINDOWS else self._read_unix()

    # ── Windows ──────────────────────────────

    def _read_win(self) -> str:
        ch = msvcrt.getwch()
        if ch in ("\x00", "\xe0"):
            ch2 = msvcrt.getwch()
            return self._WIN_EXT.get(ch2, Key.UNKNOWN)
        if ch == "\x1b":   return Key.ESC
        if ch in ("\r", "\n"): return Key.ENTER
        if ch in ("\x08", "\x7f"): return Key.BACKSPACE
        if ch == "\x12":   return Key.CTRL_R
        if ch == "\x13":   return Key.CTRL_S
        if ch == "\x11":   return Key.CTRL_Q
        return ch

    # ── Unix ─────────────────────────────────

    def _read_unix(self) -> str:
        ch = sys.stdin.read(1)
        if ch == "\x1b":
            rdy, _, _ = select.select([sys.stdin], [], [], 0.05)
            if not rdy:
                return Key.ESC
            seq = sys.stdin.read(1)
            if seq == "[":
                inner = sys.stdin.read(1)
                if inner == "A": return Key.UP
                if inner == "B": return Key.DOWN
                if inner == "C": return Key.RIGHT
                if inner == "D": return Key.LEFT
                if inner == "H": return Key.HOME
                if inner == "F": return Key.END
                if inner in ("3", "5", "6"):
                    tilde = sys.stdin.read(1)
                    if inner == "3" and tilde == "~": return Key.DELETE
                    if inner == "5" and tilde == "~": return Key.PGUP
                    if inner == "6" and tilde == "~": return Key.PGDN
            elif seq == "O":
                inner = sys.stdin.read(1)
                if inner == "H": return Key.HOME
                if inner == "F": return Key.END
            return Key.UNKNOWN
        if ch in ("\r", "\n"):     return Key.ENTER
        if ch in ("\x7f", "\x08"): return Key.BACKSPACE
        if ch == "\x12":           return Key.CTRL_R
        if ch == "\x13":           return Key.CTRL_S
        if ch == "\x11":           return Key.CTRL_Q
        return ch


# ──────────────────────────────────────────────
# Enums
# ──────────────────────────────────────────────

class Mode(Enum):
    NORMAL  = auto()
    INSERT  = auto()
    COMMAND = auto()
    SEARCH  = auto()


# ──────────────────────────────────────────────
# Cursor
# ──────────────────────────────────────────────

class Cursor:
    """Tracks (row, col) position within a Document."""

    def __init__(self, row: int = 0, col: int = 0) -> None:
        self.row = row
        self.col = col

    def up(self,    n: int = 1) -> None: self.row = max(0, self.row - n)
    def down(self,  n: int = 1) -> None: self.row += n
    def left(self,  n: int = 1) -> None: self.col = max(0, self.col - n)
    def right(self, n: int = 1) -> None: self.col += n

    def move_to(self, row: int, col: int) -> None:
        self.row = max(0, row)
        self.col = max(0, col)

    def clamp(self, max_row: int, max_col: int) -> None:
        self.row = max(0, min(self.row, max_row))
        self.col = max(0, min(self.col, max_col))

    def clone(self) -> "Cursor":
        return Cursor(self.row, self.col)

    def __repr__(self) -> str:
        return f"Cursor(row={self.row}, col={self.col})"


# ──────────────────────────────────────────────
# Document
# ──────────────────────────────────────────────

class Document:
    """
    Holds the textual state of an open buffer.
    Provides line-level operations and undo/redo snapshots.
    """

    MAX_UNDO = 50

    def __init__(self, file_name: str = "untitled") -> None:
        self.file_name:   str       = file_name
        self.content:     list[str] = [""]
        self.modified:    bool      = False
        self._undo_stack: list[tuple[list[str], Cursor]] = []
        self._redo_stack: list[tuple[list[str], Cursor]] = []

    # ── Undo / redo ──────────────────────────

    def snapshot(self, cursor: Cursor) -> None:
        state = (copy.deepcopy(self.content), cursor.clone())
        self._undo_stack.append(state)
        if len(self._undo_stack) > self.MAX_UNDO:
            self._undo_stack.pop(0)
        self._redo_stack.clear()

    def undo(self, cursor: Cursor) -> Optional[Cursor]:
        if not self._undo_stack:
            return None
        self._redo_stack.append((copy.deepcopy(self.content), cursor.clone()))
        content, saved = self._undo_stack.pop()
        self.content  = content
        self.modified = True
        return saved

    def redo(self, cursor: Cursor) -> Optional[Cursor]:
        if not self._redo_stack:
            return None
        self._undo_stack.append((copy.deepcopy(self.content), cursor.clone()))
        content, saved = self._redo_stack.pop()
        self.content  = content
        self.modified = True
        return saved

    # ── Line primitives ──────────────────────

    def line_count(self) -> int:
        return len(self.content)

    def get_line(self, row: int) -> str:
        return self.content[row] if 0 <= row < len(self.content) else ""

    def set_line(self, row: int, text: str) -> None:
        if 0 <= row < len(self.content):
            self.content[row] = text
            self.modified = True

    def insert_line(self, row: int, text: str = "") -> None:
        self.content.insert(row, text)
        self.modified = True

    def delete_line(self, row: int) -> str:
        if len(self.content) == 1:
            deleted, self.content[0] = self.content[0], ""
        else:
            deleted = self.content.pop(row)
        self.modified = True
        return deleted

    # ── File I/O ─────────────────────────────

    def load(self, path: str) -> None:
        path = os.path.expanduser(path)
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            lines = fh.read().splitlines()
        self.content   = lines if lines else [""]
        self.file_name = os.path.basename(path)
        self.modified  = False
        self._undo_stack.clear()
        self._redo_stack.clear()

    def save(self, path: Optional[str] = None) -> str:
        if path:
            self.file_name = os.path.basename(path)
        save_path = os.path.expanduser(path or self.file_name)
        with open(save_path, "w", encoding="utf-8") as fh:
            fh.write("\n".join(self.content) + "\n")
        self.modified = False
        return save_path

    def __repr__(self) -> str:
        return (f"Document(file={self.file_name!r}, "
                f"lines={self.line_count()}, modified={self.modified})")


# ──────────────────────────────────────────────
# Editor  (editing operations, screen-agnostic)
# ──────────────────────────────────────────────

class Editor:
    """All mutations on a Document through a Cursor."""

    def __init__(self, doc: Document, cursor: Cursor) -> None:
        self.doc    = doc
        self.cursor = cursor

    def _clamp(self) -> None:
        max_row = max(0, self.doc.line_count() - 1)
        max_col = len(self.doc.get_line(self.cursor.row))
        self.cursor.clamp(max_row, max_col)

    def _snap_col(self) -> None:
        self.cursor.col = min(self.cursor.col,
                              len(self.doc.get_line(self.cursor.row)))

    # ── Cursor movement ──────────────────────

    def move_up(self) -> None:
        self.cursor.up()
        self._snap_col()

    def move_down(self) -> None:
        self.cursor.down()
        self.cursor.row = min(self.cursor.row, self.doc.line_count() - 1)
        self._snap_col()

    def move_left(self) -> None:
        if self.cursor.col > 0:
            self.cursor.left()
        elif self.cursor.row > 0:
            self.cursor.row -= 1
            self.cursor.col  = len(self.doc.get_line(self.cursor.row))

    def move_right(self) -> None:
        line = self.doc.get_line(self.cursor.row)
        if self.cursor.col < len(line):
            self.cursor.right()
        elif self.cursor.row < self.doc.line_count() - 1:
            self.cursor.row += 1
            self.cursor.col  = 0

    def move_line_start(self) -> None:
        self.cursor.col = 0

    def move_line_end(self) -> None:
        self.cursor.col = len(self.doc.get_line(self.cursor.row))

    def move_to_line(self, n: int) -> None:
        self.cursor.row = max(0, min(n, self.doc.line_count() - 1))
        self._snap_col()

    def move_to_first_line(self) -> None:
        self.move_to_line(0)

    def move_to_last_line(self) -> None:
        self.move_to_line(self.doc.line_count() - 1)

    # ── Insertion ────────────────────────────

    def insert_char(self, ch: str) -> None:
        self.doc.snapshot(self.cursor)
        r, c = self.cursor.row, self.cursor.col
        line = self.doc.get_line(r)
        self.doc.set_line(r, line[:c] + ch + line[c:])
        self.cursor.col += len(ch)

    def insert_newline(self) -> None:
        self.doc.snapshot(self.cursor)
        r, c = self.cursor.row, self.cursor.col
        line = self.doc.get_line(r)
        self.doc.set_line(r, line[:c])
        self.doc.insert_line(r + 1, line[c:])
        self.cursor.row = r + 1
        self.cursor.col = 0

    def open_line_below(self) -> None:
        self.doc.snapshot(self.cursor)
        self.doc.insert_line(self.cursor.row + 1, "")
        self.cursor.row += 1
        self.cursor.col  = 0

    def open_line_above(self) -> None:
        self.doc.snapshot(self.cursor)
        self.doc.insert_line(self.cursor.row, "")
        self.cursor.col = 0

    # ── Deletion ─────────────────────────────

    def delete_char_under(self) -> None:
        r, c = self.cursor.row, self.cursor.col
        line = self.doc.get_line(r)
        if not line:
            return
        self.doc.snapshot(self.cursor)
        self.doc.set_line(r, line[:c] + line[c + 1:])
        self._snap_col()

    def backspace(self) -> None:
        r, c = self.cursor.row, self.cursor.col
        if c > 0:
            self.doc.snapshot(self.cursor)
            line = self.doc.get_line(r)
            self.doc.set_line(r, line[:c - 1] + line[c:])
            self.cursor.col -= 1
        elif r > 0:
            self.doc.snapshot(self.cursor)
            prev    = self.doc.get_line(r - 1)
            curr    = self.doc.get_line(r)
            new_col = len(prev)
            self.doc.set_line(r - 1, prev + curr)
            self.doc.delete_line(r)
            self.cursor.row = r - 1
            self.cursor.col = new_col

    def delete_line(self) -> None:
        self.doc.snapshot(self.cursor)
        self.doc.delete_line(self.cursor.row)
        self._clamp()

    # ── Undo / Redo ──────────────────────────

    def undo(self) -> bool:
        saved = self.doc.undo(self.cursor)
        if saved:
            self.cursor.row = saved.row
            self.cursor.col = saved.col
            self._clamp()
            return True
        return False

    def redo(self) -> bool:
        saved = self.doc.redo(self.cursor)
        if saved:
            self.cursor.row = saved.row
            self.cursor.col = saved.col
            self._clamp()
            return True
        return False

    # ── Search ───────────────────────────────

    def find_all(self, pattern: str) -> list[tuple[int, int]]:
        hits: list[tuple[int, int]] = []
        for r, line in enumerate(self.doc.content):
            start = 0
            while True:
                idx = line.find(pattern, start)
                if idx == -1:
                    break
                hits.append((r, idx))
                start = idx + 1
        return hits


# ──────────────────────────────────────────────
# CommandHandler
# ──────────────────────────────────────────────

class CommandHandler:
    """Parses and dispatches colon commands entered in COMMAND mode."""

    def __init__(self, tui: "TuiEditor") -> None:
        self._tui = tui

    def execute(self, cmd_str: str) -> dict:
        result = {"ok": True, "message": "", "quit": False}
        parts  = cmd_str.strip().split(maxsplit=1)
        if not parts:
            return result
        verb = parts[0].lower()
        arg  = parts[1].strip() if len(parts) > 1 else ""

        dispatch = {
            "w": self._save,   "write": self._save,
            "q": lambda a: self._quit(False),
            "quit": lambda a: self._quit(False),
            "q!": lambda a: self._quit(True),
            "quit!": lambda a: self._quit(True),
            "wq": self._wq,    "x": self._wq,   "exit": self._wq,
            "o": self._open,   "open": self._open,
            "e": self._open,   "edit": self._open,
            "new": lambda a: self._new(),
            "set": self._set,
            "goto": self._goto,
            "help": self._toggle_help,
        }
        fn = dispatch.get(verb)
        if fn:
            result = fn(arg)
        else:
            result = {"ok": False, "message": f"Unknown command: {verb}", "quit": False}
        return result

    def _save(self, arg: str) -> dict:
        try:
            path = self._tui.doc.save(arg or None)
            return {"ok": True, "message": f'Saved "{path}"', "quit": False}
        except OSError as exc:
            return {"ok": False, "message": f"Save error: {exc}", "quit": False}

    def _quit(self, force: bool) -> dict:
        if self._tui.doc.modified and not force:
            return {"ok": False,
                    "message": "Unsaved changes! Use :q! to force-quit, or :wq to save and quit.",
                    "quit": False}
        return {"ok": True, "message": "", "quit": True}

    def _wq(self, arg: str) -> dict:
        res = self._save(arg)
        return self._quit(force=True) if res["ok"] else res

    def _open(self, arg: str) -> dict:
        if not arg:
            return {"ok": False, "message": "Usage: :o <filename>", "quit": False}
        try:
            self._tui.doc    = Document()
            self._tui.doc.load(arg)
            self._tui.editor = Editor(self._tui.doc, self._tui.cursor)
            self._tui.cursor.move_to(0, 0)
            self._tui.viewport_top = 0
            return {"ok": True, "message": f'Opened "{arg}"', "quit": False}
        except OSError as exc:
            return {"ok": False, "message": f"Open error: {exc}", "quit": False}

    def _new(self) -> dict:
        self._tui.doc    = Document("untitled")
        self._tui.editor = Editor(self._tui.doc, self._tui.cursor)
        self._tui.cursor.move_to(0, 0)
        self._tui.viewport_top = 0
        return {"ok": True, "message": "New document created.", "quit": False}

    def _set(self, arg: str) -> dict:
        if arg in ("nu", "number", "linenumber"):
            self._tui.show_line_numbers = not self._tui.show_line_numbers
            state = "on" if self._tui.show_line_numbers else "off"
            return {"ok": True, "message": f"Line numbers {state}.", "quit": False}
        return {"ok": False, "message": f"Unknown option: {arg}", "quit": False}

    def _goto(self, arg: str) -> dict:
        try:
            n = int(arg) - 1
            self._tui.editor.move_to_line(n)
            return {"ok": True, "message": f"Jumped to line {arg}.", "quit": False}
        except ValueError:
            return {"ok": False, "message": "Usage: :goto <line_number>", "quit": False}

    def _toggle_help(self, _: str) -> dict:
        self._tui.show_help = not self._tui.show_help
        return {"ok": True,
                "message": "Help overlay toggled (press any key to dismiss).",
                "quit": False}


# ──────────────────────────────────────────────
# Help overlay text
# ──────────────────────────────────────────────

HELP_LINES = [
    "+--------------------------------------------+",
    "|       TERMINAL TEXT EDITOR  HELP           |",
    "+---------------------+----------------------+",
    "|  NORMAL MODE        |  COMMAND MODE (:...) |",
    "+---------------------+----------------------+",
    "|  h/j/k/l  move      |  :w [file]  save     |",
    "|  Arrows   move      |  :q         quit     |",
    "|  i        insert    |  :q!        force q  |",
    "|  a        append    |  :wq / :x   save+q   |",
    "|  o        line down |  :o <file>  open     |",
    "|  O        line up   |  :new       new buf  |",
    "|  x        del char  |  :set nu    line nos |",
    "|  dd       del line  |  :goto <n>  jump     |",
    "|  u        undo      |  :help      toggle   |",
    "|  Ctrl+R   redo      +----------------------+",
    "|  G        last line |  SEARCH MODE (/)     |",
    "|  gg       first ln  |  /pattern   search   |",
    "|  0 / $    col 0/end |  n / N   next/prev   |",
    "|  PgUp/Dn  scroll    +----------------------+",
    "|  /        search    |  Ctrl+S  quick save  |",
    "|  :        command   |  Ctrl+Q  force quit  |",
    "|  ESC      normal    |                      |",
    "+---------------------+----------------------+",
    "         Press any key to close              ",
]


# ──────────────────────────────────────────────
# TuiEditor  (rendering + main loop)
# ──────────────────────────────────────────────

class TuiEditor:
    """
    ANSI-based terminal UI.
    Owns the screen buffer, dispatches raw key events,
    delegates mutations to Editor, routes : commands to CommandHandler.
    """

    def __init__(self, file_path: Optional[str] = None) -> None:
        name = os.path.basename(file_path) if file_path else "untitled"
        self.doc    = Document(name)
        self.cursor = Cursor()
        self.editor = Editor(self.doc, self.cursor)
        self.cmd_handler = CommandHandler(self)

        self.mode:              Mode  = Mode.NORMAL
        self.cmd_buffer:        str   = ""
        self.status_message:    str   = ""
        self.viewport_top:      int   = 0
        self.show_line_numbers: bool  = True
        self.show_help:         bool  = False

        self._search_pattern: str                   = ""
        self._search_hits:    list[tuple[int, int]] = []
        self._search_idx:     int                   = 0
        self._dd_pending:     bool                  = False

        self._key_reader = KeyReader()
        self._old_term   = None      # saved Unix terminal settings

        if file_path:
            path = os.path.expanduser(file_path)
            if os.path.isfile(path):
                try:
                    self.doc.load(path)
                except OSError as exc:
                    self.status_message = f"Cannot open file: {exc}"

    # ── Public entry point ───────────────────

    def run(self) -> None:
        if IS_WINDOWS:
            _enable_ansi_windows()
        self._enter_raw()
        try:
            sys.stdout.write(A.ALT_SCREEN + A.HIDE_CUR)
            sys.stdout.flush()
            self._loop()
        finally:
            sys.stdout.write(A.SHOW_CUR + A.NORM_SCREEN + A.RESET)
            sys.stdout.flush()
            self._leave_raw()

    # ── Raw-mode management ──────────────────

    def _enter_raw(self) -> None:
        if not IS_WINDOWS:
            self._old_term = termios.tcgetattr(sys.stdin)
            tty.setraw(sys.stdin.fileno())

    def _leave_raw(self) -> None:
        if not IS_WINDOWS and self._old_term is not None:
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self._old_term)

    # ── Main loop ────────────────────────────

    def _loop(self) -> None:
        while True:
            rows, cols = term_size()
            self._scroll_viewport(rows)
            self._render(rows, cols)
            if self.show_help:
                self._render_help(rows, cols)
                self._key_reader.read()
                self.show_help = False
                continue
            key = self._key_reader.read()
            if self._dispatch(key):
                break

    # ── Viewport ─────────────────────────────

    def _scroll_viewport(self, rows: int) -> None:
        text_rows = rows - 2
        if self.cursor.row < self.viewport_top:
            self.viewport_top = self.cursor.row
        elif self.cursor.row >= self.viewport_top + text_rows:
            self.viewport_top = self.cursor.row - text_rows + 1

    # ── Rendering ────────────────────────────

    def _render(self, rows: int, cols: int) -> None:
        buf: list[str] = [A.move(1, 1)]

        # ── Title bar (row 1) ──
        mod   = " [+]" if self.doc.modified else "    "
        title = f"  {self.doc.file_name}{mod}  --  terminal_text_editor  "
        title = title[:cols].ljust(cols)
        buf.append(A.BG_WHITE + A.FG_BLACK + A.BOLD + title + A.RESET)

        # ── Text area (rows 2 .. rows-1) ──
        text_rows = rows - 2
        ln_w      = (len(str(self.doc.line_count())) + 1) if self.show_line_numbers else 0
        text_w    = cols - ln_w

        # Build highlight set for search matches
        hit_cols: set[tuple[int, int]] = set()
        if self._search_pattern and self._search_hits:
            pat_len = len(self._search_pattern)
            for (hr, hc) in self._search_hits:
                for i in range(pat_len):
                    hit_cols.add((hr, hc + i))

        for sr in range(text_rows):
            dr = self.viewport_top + sr
            buf.append(A.move(sr + 2, 1))

            if dr >= self.doc.line_count():
                buf.append(A.FG_BLUE + "~" + A.RESET + A.ERASE_EOL)
                continue

            # Line number
            if self.show_line_numbers:
                ln_str    = str(dr + 1).rjust(ln_w - 1) + " "
                num_color = A.FG_RED if dr == self.cursor.row else A.FG_YELLOW
                buf.append(num_color + ln_str + A.RESET)

            # Line content with search highlights
            line    = self.doc.get_line(dr)
            visible = line[:text_w]
            for ci, ch in enumerate(visible):
                if (dr, ci) in hit_cols:
                    buf.append(A.BG_YELLOW + A.FG_BLACK + ch + A.RESET)
                else:
                    buf.append(ch)
            buf.append(A.ERASE_EOL)

        # ── Status bar (last row) ──
        buf.append(A.move(rows, 1))
        buf.append(self._build_status_bar(cols))

        # ── Physical cursor ──
        buf.append(A.SHOW_CUR)
        buf.append(self._cursor_position(rows, cols, ln_w))

        sys.stdout.write("".join(buf))
        sys.stdout.flush()

    def _build_status_bar(self, cols: int) -> str:
        # Command / search prompt
        if self.mode in (Mode.COMMAND, Mode.SEARCH):
            prefix = ":" if self.mode == Mode.COMMAND else "/"
            bar    = (prefix + self.cmd_buffer)[:cols].ljust(cols)
            return A.BG_CYAN + A.FG_BLACK + A.BOLD + bar + A.RESET

        # Normal / Insert
        labels   = {Mode.NORMAL: " NORMAL ", Mode.INSERT: " INSERT "}
        bg_map   = {Mode.NORMAL: A.BG_GREEN, Mode.INSERT: A.BG_YELLOW}
        label    = labels.get(self.mode, " NORMAL ")
        label_bg = bg_map.get(self.mode, A.BG_GREEN)

        pos  = f" {self.cursor.row + 1}:{self.cursor.col + 1} "
        msg  = self.status_message
        gap  = cols - len(label) - len(msg) - len(pos)
        rest = (msg + " " * max(0, gap) + pos)[:cols - len(label)]

        return (label_bg + A.FG_BLACK + A.BOLD + label + A.RESET
                + A.BG_CYAN + A.FG_BLACK + rest + A.RESET)

    def _cursor_position(self, rows: int, cols: int, ln_w: int) -> str:
        if self.mode in (Mode.COMMAND, Mode.SEARCH):
            cy = rows
            cx = len(self.cmd_buffer) + 2   # 1 for prefix char, 1 for 1-indexed
        else:
            cy = self.cursor.row - self.viewport_top + 2
            cx = self.cursor.col + ln_w + 1
        cy = max(1, min(cy, rows))
        cx = max(1, min(cx, cols))
        return A.move(cy, cx)

    def _render_help(self, rows: int, cols: int) -> None:
        start_y = max(2, (rows - len(HELP_LINES)) // 2)
        buf = []
        for i, line in enumerate(HELP_LINES):
            y = start_y + i
            if y >= rows:
                break
            x = max(1, (cols - len(line)) // 2)
            buf.append(A.move(y, x))
            buf.append(A.BG_WHITE + A.FG_BLACK + A.BOLD
                       + line[:cols] + A.RESET)
        sys.stdout.write("".join(buf))
        sys.stdout.flush()

    # ── Input dispatch ───────────────────────

    def _dispatch(self, key: str) -> bool:
        """Return True to quit the editor."""
        self.status_message = ""
        if   self.mode == Mode.NORMAL:  return self._handle_normal(key)
        elif self.mode == Mode.INSERT:  self._handle_insert(key)
        elif self.mode == Mode.COMMAND: return self._handle_command(key)
        elif self.mode == Mode.SEARCH:  self._handle_search(key)
        return False

    # ── NORMAL mode ──────────────────────────

    def _handle_normal(self, key: str) -> bool:
        # Basic movement
        move_map = {
            Key.UP:    self.editor.move_up,
            "k":       self.editor.move_up,
            Key.DOWN:  self.editor.move_down,
            "j":       self.editor.move_down,
            Key.LEFT:  self.editor.move_left,
            "h":       self.editor.move_left,
            Key.RIGHT: self.editor.move_right,
            "l":       self.editor.move_right,
            Key.HOME:  self.editor.move_line_start,
            "0":       self.editor.move_line_start,
            Key.END:   self.editor.move_line_end,
            "$":       self.editor.move_line_end,
        }
        if key in move_map:
            move_map[key]()
            self._dd_pending = False
            return False

        # Page navigation
        if key == Key.PGUP:
            rows, _ = term_size()
            self.editor.move_to_line(self.cursor.row - (rows - 2))
            self._dd_pending = False
            return False
        if key == Key.PGDN:
            rows, _ = term_size()
            self.editor.move_to_line(self.cursor.row + (rows - 2))
            self._dd_pending = False
            return False

        # Jump to start / end of document
        if key == "G":
            self.editor.move_to_last_line()
            self._dd_pending = False
            return False
        if key == "g":
            self.editor.move_to_first_line()
            self._dd_pending = False
            return False

        # Enter other modes
        if key == "i":
            self.mode = Mode.INSERT
            self._dd_pending = False
            return False
        if key == "a":
            self.editor.move_right()
            self.mode = Mode.INSERT
            self._dd_pending = False
            return False
        if key == "o":
            self.editor.open_line_below()
            self.mode = Mode.INSERT
            self._dd_pending = False
            return False
        if key == "O":
            self.editor.open_line_above()
            self.mode = Mode.INSERT
            self._dd_pending = False
            return False
        if key == ":":
            self.mode = Mode.COMMAND
            self.cmd_buffer  = ""
            self._dd_pending = False
            return False
        if key == "/":
            self.mode = Mode.SEARCH
            self.cmd_buffer  = ""
            self._dd_pending = False
            return False

        # Edit operations
        if key == "x":
            self.editor.delete_char_under()
            self.status_message = "Deleted character"
            self._dd_pending = False
            return False
        if key == "d":
            if self._dd_pending:
                self.editor.delete_line()
                self.status_message  = "Line deleted"
                self._dd_pending     = False
            else:
                self._dd_pending     = True
                self.status_message  = "d -- press d again to delete line"
            return False
        if key == "u":
            ok = self.editor.undo()
            self.status_message = "Undo" if ok else "Nothing to undo"
            self._dd_pending    = False
            return False
        if key == Key.CTRL_R:
            ok = self.editor.redo()
            self.status_message = "Redo" if ok else "Nothing to redo"
            self._dd_pending    = False
            return False

        # Quick shortcuts
        if key == Key.CTRL_S:
            res = self.cmd_handler._save("")
            self.status_message = res["message"]
            return False
        if key == Key.CTRL_Q:
            return True

        # Search navigation
        if key == "n":
            self._search_jump(forward=True)
            return False
        if key == "N":
            self._search_jump(forward=False)
            return False

        if key != Key.ESC:
            self._dd_pending = False
        return False

    # ── INSERT mode ──────────────────────────

    def _handle_insert(self, key: str) -> None:
        if key == Key.ESC:
            self.mode = Mode.NORMAL
            self.editor.move_left()
            return
        if key == Key.ENTER:    self.editor.insert_newline();       return
        if key == Key.BACKSPACE:self.editor.backspace();            return
        if key == Key.DELETE:   self.editor.delete_char_under();    return
        if key == Key.UP:       self.editor.move_up();              return
        if key == Key.DOWN:     self.editor.move_down();            return
        if key == Key.LEFT:     self.editor.move_left();            return
        if key == Key.RIGHT:    self.editor.move_right();           return
        if key == Key.HOME:     self.editor.move_line_start();      return
        if key == Key.END:      self.editor.move_line_end();        return
        if key == Key.CTRL_S:
            try:
                path = self.doc.save()
                self.status_message = f'Saved "{path}"'
            except OSError as exc:
                self.status_message = f"Save error: {exc}"
            return
        if len(key) == 1 and ord(key) >= 32:
            self.editor.insert_char(key)

    # ── COMMAND mode ─────────────────────────

    def _handle_command(self, key: str) -> bool:
        if key == Key.ESC:
            self.mode = Mode.NORMAL
            self.cmd_buffer = ""
            return False
        if key == Key.ENTER:
            self.mode = Mode.NORMAL
            result = self.cmd_handler.execute(self.cmd_buffer)
            self.status_message = result["message"]
            self.cmd_buffer     = ""
            return result.get("quit", False)
        if key == Key.BACKSPACE:
            self.cmd_buffer = self.cmd_buffer[:-1]
            return False
        if len(key) == 1 and ord(key) >= 32:
            self.cmd_buffer += key
        return False

    # ── SEARCH mode ──────────────────────────

    def _handle_search(self, key: str) -> None:
        if key == Key.ESC:
            self.mode = Mode.NORMAL
            self.cmd_buffer = ""
            return
        if key == Key.ENTER:
            self.mode            = Mode.NORMAL
            self._search_pattern = self.cmd_buffer
            self.cmd_buffer      = ""
            self._search_hits    = self.editor.find_all(self._search_pattern)
            self._search_idx     = 0
            if self._search_hits:
                self._jump_to_hit(0)
                self.status_message = (
                    f"/{self._search_pattern}  "
                    f"({len(self._search_hits)} match(es))"
                )
            else:
                self.status_message = f"Pattern not found: {self._search_pattern}"
            return
        if key == Key.BACKSPACE:
            self.cmd_buffer = self.cmd_buffer[:-1]
            return
        if len(key) == 1 and ord(key) >= 32:
            self.cmd_buffer += key

    def _search_jump(self, forward: bool) -> None:
        if not self._search_hits:
            self.status_message = "No search active -- press / to search"
            return
        delta = 1 if forward else -1
        self._search_idx = (self._search_idx + delta) % len(self._search_hits)
        self._jump_to_hit(self._search_idx)
        self.status_message = (
            f"Match {self._search_idx + 1}/{len(self._search_hits)}"
            f" -- {self._search_pattern}"
        )

    def _jump_to_hit(self, idx: int) -> None:
        row, col = self._search_hits[idx]
        self.editor.move_to_line(row)
        self.cursor.col = col



# ──────────────────────────────────────────────
# Entry point
# ──────────────────────────────────────────────

def main() -> None:
    file_path: Optional[str] = sys.argv[1] if len(sys.argv) > 1 else None
    editor = TuiEditor(file_path)
    try:
        editor.run()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()