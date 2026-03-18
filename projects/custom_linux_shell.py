#!/usr/bin/env python3
"""
custom_linux_shell.py
A simplified Linux-like shell simulator using OOP.
Supports: command execution, piping, input/output redirection,
          and built-in commands (cd, exit, pwd, help).
"""

import os
import sys
import subprocess
import shlex
from dataclasses import dataclass, field
from typing import Optional


# ─────────────────────────────────────────────
#  Data Model
# ─────────────────────────────────────────────

@dataclass
class Command:
    """
    Represents a single shell command with its arguments and
    optional I/O-redirection targets.

    Attributes:
        name          : The executable / built-in name.
        args          : Full argument list (name included as argv[0]).
        input_file    : Path to file used for stdin redirection  (<).
        output_file   : Path to file used for stdout redirection (> / >>).
        append_output : True when '>>' is used instead of '>'.
        input_stream  : Runtime file-object assigned by ShellExecutor.
        output_stream : Runtime file-object assigned by ShellExecutor.
    """
    name: str
    args: list[str] = field(default_factory=list)
    input_file:    Optional[str]  = None
    output_file:   Optional[str]  = None
    append_output: bool           = False
    input_stream:  Optional[object] = field(default=None, repr=False)
    output_stream: Optional[object] = field(default=None, repr=False)

    def __str__(self) -> str:
        parts = [f"Command({self.name!r}"]
        if self.args[1:]:
            parts.append(f"args={self.args[1:]}")
        if self.input_file:
            parts.append(f"< {self.input_file!r}")
        if self.output_file:
            op = ">>" if self.append_output else ">"
            parts.append(f"{op} {self.output_file!r}")
        return " ".join(parts) + ")"


# ─────────────────────────────────────────────
#  Parser
# ─────────────────────────────────────────────

class ParseError(Exception):
    """Raised when the user's input cannot be parsed into valid commands."""


class Parser:
    """
    Parses a raw input line into an ordered list of :class:`Command` objects.

    Supported operators
    -------------------
    ``|``   – pipe stdout of left command into stdin of right command
    ``<``   – redirect a file to stdin
    ``>``   – redirect stdout to a file (truncate)
    ``>>``  – redirect stdout to a file (append)
    """

    OPERATORS = frozenset({"<", ">", ">>"})

    # ── public API ──────────────────────────────

    def parse(self, line: str) -> list[Command]:
        """
        Parse *line* and return a list of :class:`Command` objects.

        Raises :class:`ParseError` on invalid syntax.
        """
        line = line.strip()
        if not line:
            return []

        try:
            tokens = shlex.split(line)
        except ValueError as exc:
            raise ParseError(f"Syntax error: {exc}") from exc

        # Split by pipe into segments, then parse each segment
        segments = self._split_pipes(tokens)
        if not segments:
            return []

        commands: list[Command] = []
        for seg in segments:
            cmd = self._parse_segment(seg)
            commands.append(cmd)

        # Validate: redirection in the middle of a pipeline is OK only at
        # the first (input) and last (output) positions.
        self._validate_pipeline_redirects(commands)

        return commands

    # ── private helpers ─────────────────────────

    def _split_pipes(self, tokens: list[str]) -> list[list[str]]:
        """Split a token list on ``|`` separators."""
        segments: list[list[str]] = []
        current: list[str] = []

        for tok in tokens:
            if tok == "|":
                if not current:
                    raise ParseError("Unexpected '|': no command before pipe.")
                segments.append(current)
                current = []
            else:
                current.append(tok)

        if not current:
            if segments:
                raise ParseError("Unexpected '|': no command after pipe.")
            return []

        segments.append(current)
        return segments

    def _parse_segment(self, tokens: list[str]) -> Command:
        """Build a :class:`Command` from a single pipe-segment token list."""
        if not tokens:
            raise ParseError("Empty command segment.")

        name = tokens[0]
        args: list[str] = [name]
        input_file:    Optional[str] = None
        output_file:   Optional[str] = None
        append_output: bool          = False

        i = 1
        while i < len(tokens):
            tok = tokens[i]

            if tok == "<":
                i += 1
                if i >= len(tokens):
                    raise ParseError("'<' requires a filename.")
                input_file = tokens[i]

            elif tok in (">", ">>"):
                append_output = tok == ">>"
                i += 1
                if i >= len(tokens):
                    raise ParseError(f"'{tok}' requires a filename.")
                output_file = tokens[i]

            else:
                args.append(tok)

            i += 1

        return Command(
            name=name,
            args=args,
            input_file=input_file,
            output_file=output_file,
            append_output=append_output,
        )

    @staticmethod
    def _validate_pipeline_redirects(commands: list[Command]) -> None:
        """
        In a pipeline, output redirection on non-final commands and
        input redirection on non-first commands would be confusing /
        meaningless. Warn but do not hard-error (bash behaviour).
        """
        for idx, cmd in enumerate(commands):
            if idx > 0 and cmd.input_file:
                print(
                    f"[shell] Warning: input redirection on command "
                    f"#{idx + 1} ('{cmd.name}') overrides pipe input.",
                    file=sys.stderr,
                )
            if idx < len(commands) - 1 and cmd.output_file:
                print(
                    f"[shell] Warning: output redirection on command "
                    f"#{idx + 1} ('{cmd.name}') overrides pipe output.",
                    file=sys.stderr,
                )


# ─────────────────────────────────────────────
#  Executor
# ─────────────────────────────────────────────

class ExecutionError(Exception):
    """Raised when a command cannot be executed."""


class ShellExecutor:
    """
    Executes a pipeline of :class:`Command` objects.

    * Built-in commands (``cd``, ``pwd``, ``exit``, ``help``) are handled
      directly inside the process.
    * External commands are launched via :mod:`subprocess`.
    * Pipes between successive commands are wired automatically.
    * File-based I/O redirection is applied on the first / last command.
    """

    BUILTINS = frozenset({"cd", "pwd", "exit", "help"})

    def __init__(self) -> None:
        self._exit_requested = False

    # ── public API ──────────────────────────────

    @property
    def exit_requested(self) -> bool:
        return self._exit_requested

    def execute(self, commands: list[Command]) -> None:
        """Execute *commands* as a pipeline."""
        if not commands:
            return

        if len(commands) == 1:
            self._execute_single(commands[0])
        else:
            self._execute_pipeline(commands)

    # ── single command ───────────────────────────

    def _execute_single(self, cmd: Command) -> None:
        if cmd.name in self.BUILTINS:
            self._run_builtin(cmd, stdin=None, stdout=None)
        else:
            stdin_fh  = self._open_input(cmd)
            stdout_fh = self._open_output(cmd)
            try:
                self._run_external(cmd, stdin=stdin_fh, stdout=stdout_fh)
            finally:
                if stdin_fh  not in (None, subprocess.PIPE): stdin_fh.close()
                if stdout_fh not in (None, subprocess.PIPE): stdout_fh.close()

    # ── pipeline ────────────────────────────────

    def _execute_pipeline(self, commands: list[Command]) -> None:
        """
        Chain N commands:  cmd0 | cmd1 | … | cmdN-1

        Strategy
        --------
        Execute each command left-to-right keeping track of the previous
        process's stdout pipe so it can become the next process's stdin.
        Built-ins in the middle of a pipeline are executed with
        subprocess-compatible wiring via temporary threads (rare edge case).
        """
        processes: list[subprocess.Popen] = []
        prev_stdout = None   # stdout PIPE from previous process

        for idx, cmd in enumerate(commands):
            is_last  = idx == len(commands) - 1
            is_first = idx == 0

            # ── determine stdin ────────────────────
            if is_first and cmd.input_file:
                stdin_src = self._open_input(cmd)
            elif prev_stdout is not None:
                stdin_src = prev_stdout
            else:
                stdin_src = None   # inherit shell stdin

            # ── determine stdout ───────────────────
            if is_last and cmd.output_file:
                stdout_dst = self._open_output(cmd)
            elif not is_last:
                stdout_dst = subprocess.PIPE
            else:
                stdout_dst = None  # inherit shell stdout

            # ── built-ins in a pipeline are tricky –
            #    we run them as a subprocess of themselves for simplicity.
            #    Alternatively fall through to the external runner which
            #    will fail with "not found" – tell the user.
            if cmd.name in self.BUILTINS:
                print(
                    f"[shell] Warning: built-in '{cmd.name}' in a pipeline "
                    "runs in a sub-shell; state changes (e.g. cd) won't "
                    "affect the current shell.",
                    file=sys.stderr,
                )

            try:
                proc = subprocess.Popen(
                    cmd.args,
                    stdin=stdin_src,
                    stdout=stdout_dst,
                    stderr=None,   # inherited
                )
            except FileNotFoundError:
                print(f"[shell] {cmd.name}: command not found", file=sys.stderr)
                # Close dangling pipes to avoid deadlock
                if prev_stdout and prev_stdout != subprocess.PIPE:
                    try: prev_stdout.close()
                    except Exception: pass
                return
            except PermissionError:
                print(f"[shell] {cmd.name}: permission denied", file=sys.stderr)
                return

            processes.append(proc)

            # close the read-end of prev pipe in the parent now that the
            # child inherited it – otherwise the child never gets EOF.
            if prev_stdout and hasattr(prev_stdout, "close"):
                try: prev_stdout.close()
                except Exception: pass

            prev_stdout = proc.stdout   # may be None if not PIPE

        # Wait for all processes, propagate errors
        for proc in processes:
            proc.wait()
            if proc.returncode not in (0, None):
                # Non-zero exit codes are noted but not fatal for the shell
                pass

    # ── built-ins ────────────────────────────────

    def _run_builtin(
        self,
        cmd: Command,
        stdin,
        stdout,
    ) -> None:
        name = cmd.name
        args = cmd.args[1:]   # argv[0] is the command name itself

        if name == "exit":
            code = int(args[0]) if args else 0
            print(f"[shell] Exiting with code {code}.")
            self._exit_requested = True

        elif name == "cd":
            target = args[0] if args else os.path.expanduser("~")
            try:
                os.chdir(target)
            except FileNotFoundError:
                print(f"[shell] cd: {target}: No such file or directory",
                      file=sys.stderr)
            except NotADirectoryError:
                print(f"[shell] cd: {target}: Not a directory",
                      file=sys.stderr)
            except PermissionError:
                print(f"[shell] cd: {target}: Permission denied",
                      file=sys.stderr)

        elif name == "pwd":
            out = sys.stdout if stdout is None else stdout
            print(os.getcwd(), file=out)

        elif name == "help":
            self._print_help()

    # ── external commands ─────────────────────────

    def _run_external(
        self,
        cmd: Command,
        stdin,
        stdout,
    ) -> None:
        try:
            proc = subprocess.run(
                cmd.args,
                stdin=stdin,
                stdout=stdout,
            )
            if proc.returncode != 0:
                print(
                    f"[shell] '{cmd.name}' exited with status {proc.returncode}.",
                    file=sys.stderr,
                )
        except FileNotFoundError:
            print(f"[shell] {cmd.name}: command not found", file=sys.stderr)
        except PermissionError:
            print(f"[shell] {cmd.name}: permission denied", file=sys.stderr)
        except KeyboardInterrupt:
            print()   # newline after ^C

    # ── stream helpers ────────────────────────────

    @staticmethod
    def _open_input(cmd: Command):
        if cmd.input_file is None:
            return None
        try:
            return open(cmd.input_file, "r")
        except FileNotFoundError:
            raise ExecutionError(
                f"{cmd.input_file}: No such file or directory"
            )
        except PermissionError:
            raise ExecutionError(
                f"{cmd.input_file}: Permission denied"
            )

    @staticmethod
    def _open_output(cmd: Command):
        if cmd.output_file is None:
            return None
        mode = "a" if cmd.append_output else "w"
        try:
            return open(cmd.output_file, mode)
        except PermissionError:
            raise ExecutionError(
                f"{cmd.output_file}: Permission denied"
            )
        except IsADirectoryError:
            raise ExecutionError(
                f"{cmd.output_file}: Is a directory"
            )

    # ── help text ─────────────────────────────────

    @staticmethod
    def _print_help() -> None:
        help_text = """
╔══════════════════════════════════════════════════════╗
║           custom_linux_shell  –  Quick Reference     ║
╠══════════════════════════════════════════════════════╣
║  Built-in commands                                   ║
║  ─────────────────────────────────────────────────── ║
║  cd [dir]       Change directory (~ if omitted)      ║
║  pwd            Print current working directory      ║
║  exit [code]    Exit the shell (default code = 0)    ║
║  help           Show this help message               ║
║                                                      ║
║  Operators                                           ║
║  ─────────────────────────────────────────────────── ║
║  cmd1 | cmd2    Pipe stdout of cmd1 into cmd2        ║
║  cmd < file     Read stdin from file                 ║
║  cmd > file     Write stdout to file (truncate)      ║
║  cmd >> file    Append stdout to file                ║
║                                                      ║
║  All other commands are executed as system commands. ║
╚══════════════════════════════════════════════════════╝
"""
        print(help_text)


# ─────────────────────────────────────────────
#  Shell (main loop)
# ─────────────────────────────────────────────

class Shell:
    """
    The top-level shell object.

    Responsibilities
    ----------------
    * Display the prompt.
    * Read user input (with graceful handling of EOF / Ctrl-C).
    * Delegate parsing to :class:`Parser`.
    * Delegate execution to :class:`ShellExecutor`.
    * Maintain the read-eval-print loop until ``exit`` is requested.
    """

    BANNER = r"""
  ___ _   _ ___ _____ ___  __  __   ___ _  _ ___ _    _
 / __| | | / __|_   _/ _ \|  \/  | / __| || | __| |  | |
| (__| |_| \__ \ | || (_) | |\/| | \__ \ __ | _|| |__| |__
 \___|\___/|___/ |_| \___/|_|  |_| |___/_||_|___|____|____|

  Type  'help'  for available commands and operators.
  Type  'exit'  to quit.
"""

    def __init__(self) -> None:
        self._parser   = Parser()
        self._executor = ShellExecutor()

    # ── public API ──────────────────────────────

    def run(self) -> None:
        """Start the interactive read-eval-print loop."""
        print(self.BANNER)
        while not self._executor.exit_requested:
            try:
                line = self._read_line()
            except EOFError:
                # Ctrl-D
                print("\n[shell] EOF detected. Exiting.")
                break

            line = line.strip()
            if not line or line.startswith("#"):
                continue   # blank lines and comments are silently ignored

            self._process(line)

    # ── private helpers ──────────────────────────

    def _prompt(self) -> str:
        """Build the prompt string: user@host:cwd$"""
        try:
            cwd  = os.getcwd()
            home = os.path.expanduser("~")
            # Replace home prefix with '~' for brevity
            if cwd.startswith(home):
                cwd = "~" + cwd[len(home):]
        except OSError:
            cwd = "?"

        user = os.environ.get("USER", os.environ.get("USERNAME", "user"))
        host = os.uname().nodename if hasattr(os, "uname") else "localhost"

        return f"\033[1;32m{user}@{host}\033[0m:\033[1;34m{cwd}\033[0m$ "

    def _read_line(self) -> str:
        """Read a line from stdin, printing the prompt first."""
        try:
            return input(self._prompt())
        except KeyboardInterrupt:
            # Ctrl-C clears the current line and starts fresh
            print()
            return ""

    def _process(self, line: str) -> None:
        """Parse and execute one input line."""
        try:
            commands = self._parser.parse(line)
        except ParseError as exc:
            print(f"[shell] Parse error: {exc}", file=sys.stderr)
            return

        if not commands:
            return

        try:
            self._executor.execute(commands)
        except ExecutionError as exc:
            print(f"[shell] Execution error: {exc}", file=sys.stderr)
        except KeyboardInterrupt:
            print()   # newline after Ctrl-C mid-command


# ─────────────────────────────────────────────
#  Entry point
# ─────────────────────────────────────────────

def main() -> None:
    shell = Shell()
    shell.run()


if __name__ == "__main__":
    main()