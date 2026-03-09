"""
console_mini_framework.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
A modular, extensible console application framework built
with Python OOP.

Architecture
  Command          – base class every command inherits from
  CommandArgument  – typed, validated argument descriptor
  CommandRegistry  – stores, groups, and discovers commands
  ConsoleContext   – shared runtime state passed to commands
  ConsoleApplication – REPL loop, parser, dispatcher
  Middleware       – pre/post execution hooks

Built-in demo commands (shipped as an example plugin)
  help [command]        list commands or show detail
  version               print framework version
  echo <text…>          print text back
  upper <text…>         uppercase text
  lower <text…>         lowercase text
  reverse <text…>       reverse text
  count <text…>         character / word counts
  calc <expr>           evaluate a math expression
  env set/get/del/list  tiny key-value environment store
  history [n]           show command history
  alias <name> <cmd>    define a command alias
  clear                 clear the screen
  exit / quit           exit the framework
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

from __future__ import annotations

import os
import re
import sys
import shlex
import textwrap
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Callable, Optional


# ─────────────────────────────────────────────────────────────
#  ANSI COLOURS
# ─────────────────────────────────────────────────────────────
CYAN    = "\033[96m"
GREEN   = "\033[92m"
YELLOW  = "\033[93m"
RED     = "\033[91m"
BLUE    = "\033[94m"
MAGENTA = "\033[95m"
WHITE   = "\033[97m"
BOLD    = "\033[1m"
DIM     = "\033[2m"
RESET   = "\033[0m"


# ─────────────────────────────────────────────────────────────
#  EXCEPTIONS
# ─────────────────────────────────────────────────────────────
class CommandError(Exception):
    """Raised when a command fails due to bad usage or logic."""

class ArgumentError(CommandError):
    """Raised when command arguments are invalid."""

class CommandNotFoundError(CommandError):
    """Raised when no command matches the input."""


# ─────────────────────────────────────────────────────────────
#  COMMAND ARGUMENT DESCRIPTOR
# ─────────────────────────────────────────────────────────────
class CommandArgument:
    """
    Describes a single argument a command accepts.

    Parameters
    ----------
    name        : internal name used in the parsed dict
    description : human-readable help text
    required    : whether omitting raises ArgumentError
    default     : value used when argument is absent
    arg_type    : callable to coerce the raw string
    variadic    : if True, consumes all remaining tokens
    """

    VALID_TYPES = (str, int, float, bool)

    def __init__(
        self,
        name:        str,
        description: str  = "",
        required:    bool = True,
        default:     Any  = None,
        arg_type:    type = str,
        variadic:    bool = False,
    ):
        if arg_type not in self.VALID_TYPES:
            raise ValueError(
                f"arg_type must be one of {self.VALID_TYPES}."
            )
        self._name        = name
        self._description = description
        self._required    = required
        self._default     = default
        self._arg_type    = arg_type
        self._variadic    = variadic

    # ── properties ───────────────────────────────────────────
    @property
    def name(self) -> str:        return self._name
    @property
    def description(self) -> str: return self._description
    @property
    def required(self) -> bool:   return self._required
    @property
    def default(self) -> Any:     return self._default
    @property
    def arg_type(self) -> type:   return self._arg_type
    @property
    def variadic(self) -> bool:   return self._variadic

    def coerce(self, raw: str) -> Any:
        """Convert a raw string token to the declared type."""
        try:
            if self._arg_type is bool:
                return raw.lower() in ("1", "true", "yes", "on")
            return self._arg_type(raw)
        except (ValueError, TypeError) as exc:
            raise ArgumentError(
                f"Argument '{self._name}' expects {self._arg_type.__name__}, "
                f"got '{raw}'."
            ) from exc

    def usage_hint(self) -> str:
        tag = f"<{self._name}…>" if self._variadic else f"<{self._name}>"
        if not self._required:
            tag = f"[{tag[1:-1]}]"
        return tag

    def __repr__(self) -> str:
        return (
            f"CommandArgument({self._name!r}, required={self._required}, "
            f"type={self._arg_type.__name__}, variadic={self._variadic})"
        )


# ─────────────────────────────────────────────────────────────
#  CONSOLE CONTEXT  (shared state / output helpers)
# ─────────────────────────────────────────────────────────────
class ConsoleContext:
    """
    Passed to every command's execute().
    Provides output helpers, the env store, history access,
    and a reference back to the application.
    """

    def __init__(self, app: "ConsoleApplication"):
        self._app = app
        self._env: dict[str, str] = {}

    # ── output helpers ────────────────────────────────────────
    def out(self, text: str = "", colour: str = ""):
        print(f"{colour}{text}{RESET}" if colour else text)

    def success(self, text: str):
        self.out(f"  {GREEN}✔  {text}{RESET}")

    def error(self, text: str):
        self.out(f"  {RED}✖  {text}{RESET}")

    def warn(self, text: str):
        self.out(f"  {YELLOW}⚠  {text}{RESET}")

    def info(self, text: str):
        self.out(f"  {CYAN}ℹ  {text}{RESET}")

    def line(self, char: str = "─", width: int = 60, colour: str = DIM):
        self.out(colour + char * width)

    def table(self, rows: list[tuple], headers: Optional[list[str]] = None,
              col_colours: Optional[list[str]] = None):
        """Simple fixed-width table."""
        all_rows = ([tuple(headers)] + list(rows)) if headers else list(rows)
        if not all_rows:
            return
        widths = [max(len(str(cell)) for cell in col) + 2
                  for col in zip(*all_rows)]
        if headers:
            hdr = "  " + "".join(
                f"{BOLD}{str(h):<{widths[i]}}{RESET}"
                for i, h in enumerate(headers)
            )
            print(hdr)
            print("  " + DIM + "─" * sum(widths) + RESET)
        for row in (list(rows)):
            line = "  "
            for i, cell in enumerate(row):
                c = (col_colours[i] if col_colours and i < len(col_colours)
                     else "")
                line += f"{c}{str(cell):<{widths[i]}}{RESET}"
            print(line)

    # ── environment store ─────────────────────────────────────
    def env_set(self, key: str, value: str):
        self._env[key.upper()] = value

    def env_get(self, key: str) -> Optional[str]:
        return self._env.get(key.upper())

    def env_del(self, key: str) -> bool:
        return self._env.pop(key.upper(), None) is not None

    def env_all(self) -> dict[str, str]:
        return dict(self._env)

    # ── application accessors ─────────────────────────────────
    @property
    def registry(self) -> "CommandRegistry":
        return self._app.registry

    @property
    def history(self) -> list[str]:
        return self._app.history


# ─────────────────────────────────────────────────────────────
#  COMMAND  (abstract base)
# ─────────────────────────────────────────────────────────────
class Command(ABC):
    """
    Abstract base every command must inherit.

    Subclasses override
      name        → str
      description → str
      arguments   → list[CommandArgument]   (optional)
      group       → str                     (optional grouping)
      aliases     → list[str]               (optional)
      execute(ctx, **kwargs) → None
    """

    # ── class-level metadata (override in subclasses) ─────────
    name:        str  = ""
    description: str  = ""
    group:       str  = "General"
    aliases:     list = []
    arguments:   list = []      # list[CommandArgument]

    # ── argument parsing ──────────────────────────────────────
    def parse_args(self, tokens: list[str]) -> dict[str, Any]:
        """
        Match positional tokens against self.arguments descriptor list.
        Returns a dict of {arg_name: coerced_value}.
        """
        result: dict[str, Any] = {}
        descriptors: list[CommandArgument] = self.arguments

        token_idx = 0
        for i, descriptor in enumerate(descriptors):
            if descriptor.variadic:
                # Consume all remaining tokens joined as a single string
                remaining = tokens[token_idx:]
                if descriptor.required and not remaining:
                    raise ArgumentError(
                        f"Required argument '{descriptor.name}' is missing."
                    )
                result[descriptor.name] = (
                    " ".join(remaining) if remaining else descriptor.default
                )
                token_idx = len(tokens)
                break
            elif token_idx < len(tokens):
                result[descriptor.name] = descriptor.coerce(tokens[token_idx])
                token_idx += 1
            elif descriptor.required:
                raise ArgumentError(
                    f"Required argument '{descriptor.name}' is missing."
                )
            else:
                result[descriptor.name] = descriptor.default

        # Warn about unexpected extra tokens (non-variadic commands)
        if token_idx < len(tokens):
            leftover = tokens[token_idx:]
            raise ArgumentError(
                f"Unexpected argument(s): {' '.join(leftover)!r}. "
                f"Use 'help {self.name}' for usage."
            )

        return result

    def usage(self) -> str:
        """One-liner usage string."""
        args_str = " ".join(a.usage_hint() for a in self.arguments)
        return f"{self.name} {args_str}".strip()

    def help_text(self) -> str:
        """Multi-line detail shown by `help <command>`."""
        sep   = "─" * 56
        lines = [
            sep,
            f"{BOLD}{CYAN}{self.name}{RESET}",
            f"  {self.description}",
            f"  {DIM}Group: {self.group}{RESET}",
        ]
        if self.aliases:
            lines.append(f"  {DIM}Aliases: {', '.join(self.aliases)}{RESET}")
        lines.append(f"\n  {BOLD}Usage:{RESET}  {self.usage()}")
        if self.arguments:
            lines.append(f"\n  {BOLD}Arguments:{RESET}")
            for arg in self.arguments:
                req_tag = f"{RED}required{RESET}" if arg.required else f"{DIM}optional{RESET}"
                default = (f"  default={arg.default!r}"
                           if not arg.required and arg.default is not None else "")
                lines.append(
                    f"    {CYAN}{arg.usage_hint():<16}{RESET}"
                    f"  {req_tag}  {arg.arg_type.__name__:<6}"
                    f"  {arg.description}{default}"
                )
        lines.append(sep)
        return "\n".join(lines)

    @abstractmethod
    def execute(self, ctx: ConsoleContext, **kwargs: Any) -> None:
        """Run the command. kwargs are the parsed arguments."""

    def __repr__(self) -> str:
        return f"Command({self.name!r})"


# ─────────────────────────────────────────────────────────────
#  COMMAND REGISTRY
# ─────────────────────────────────────────────────────────────
class CommandRegistry:
    """
    Central store for all registered commands.

    Supports
      • register(command_instance_or_class)
      • lookup by name or alias
      • list by group
      • decorator @registry.command(...)
    """

    def __init__(self):
        self._commands: dict[str, Command] = {}   # name → instance
        self._aliases:  dict[str, str]     = {}   # alias → canonical name

    # ── registration ─────────────────────────────────────────
    def register(self, cmd: "Command | type") -> Command:
        """Accept either a class or an instance."""
        instance = cmd() if isinstance(cmd, type) else cmd
        if not instance.name:
            raise ValueError(f"Command class {type(instance).__name__} has no name.")
        if instance.name in self._commands:
            raise ValueError(f"Command '{instance.name}' is already registered.")

        self._commands[instance.name] = instance
        for alias in instance.aliases:
            if alias in self._aliases or alias in self._commands:
                raise ValueError(
                    f"Alias '{alias}' conflicts with an existing command/alias."
                )
            self._aliases[alias] = instance.name
        return instance

    def unregister(self, name: str) -> bool:
        """Remove a command and its aliases."""
        cmd = self._commands.pop(name, None)
        if cmd is None:
            return False
        self._aliases = {
            k: v for k, v in self._aliases.items() if v != name
        }
        return True

    def register_alias(self, alias: str, target_name: str):
        """Add a runtime alias for an existing command."""
        if target_name not in self._commands:
            raise KeyError(f"Command '{target_name}' not found.")
        if alias in self._commands or alias in self._aliases:
            raise ValueError(f"'{alias}' is already in use.")
        self._aliases[alias] = target_name

    # ── lookup ───────────────────────────────────────────────
    def resolve(self, name: str) -> Optional[Command]:
        """Return the command for name or alias, or None."""
        canonical = self._aliases.get(name, name)
        return self._commands.get(canonical)

    def get(self, name: str) -> Command:
        cmd = self.resolve(name)
        if cmd is None:
            raise CommandNotFoundError(
                f"Unknown command: '{name}'. Type 'help' to list commands."
            )
        return cmd

    def all_commands(self) -> list[Command]:
        return sorted(self._commands.values(), key=lambda c: c.name)

    def groups(self) -> dict[str, list[Command]]:
        groups: dict[str, list[Command]] = {}
        for cmd in self.all_commands():
            groups.setdefault(cmd.group, []).append(cmd)
        return dict(sorted(groups.items()))

    def aliases_for(self, name: str) -> list[str]:
        return [a for a, n in self._aliases.items() if n == name]

    def command_names(self) -> list[str]:
        return list(self._commands.keys())

    def __len__(self) -> int:
        return len(self._commands)

    def __contains__(self, name: str) -> bool:
        return self.resolve(name) is not None

    # ── decorator factory ─────────────────────────────────────
    def command(
        self,
        name:        str,
        description: str           = "",
        group:       str           = "General",
        aliases:     list[str]     = None,
        arguments:   list[CommandArgument] = None,
    ):
        """
        Decorator that wraps a plain function as a Command and registers it.

        Usage:
            @registry.command("greet", "Say hello", arguments=[
                CommandArgument("name", "Who to greet")
            ])
            def greet_cmd(ctx, name):
                ctx.out(f"Hello, {name}!")
        """
        def decorator(fn: Callable) -> Command:
            # Build a Command subclass dynamically from the function
            cmd_class = type(
                f"{name.capitalize()}FnCommand",
                (Command,),
                {
                    "name":        name,
                    "description": description,
                    "group":       group,
                    "aliases":     aliases or [],
                    "arguments":   arguments or [],
                    "execute":     staticmethod(
                        lambda ctx, **kw: fn(ctx, **kw)
                    ),
                },
            )
            self.register(cmd_class)
            return self.resolve(name)

        return decorator


# ─────────────────────────────────────────────────────────────
#  MIDDLEWARE  (pre/post-execution hooks)
# ─────────────────────────────────────────────────────────────
class Middleware(ABC):
    """
    Hook into the execution pipeline.
    Override before() and/or after() as needed.
    """

    @abstractmethod
    def before(self, ctx: ConsoleContext, cmd: Command,
               kwargs: dict) -> bool:
        """
        Called before execute().
        Return False to abort the command.
        """

    @abstractmethod
    def after(self, ctx: ConsoleContext, cmd: Command,
              kwargs: dict, error: Optional[Exception]):
        """Called after execute() (error is None on success)."""


class LoggingMiddleware(Middleware):
    """Prints timing info for every command execution."""

    def before(self, ctx, cmd, kwargs) -> bool:
        self._start = datetime.now()
        return True

    def after(self, ctx, cmd, kwargs, error):
        elapsed = (datetime.now() - self._start).total_seconds() * 1000
        if error is None:
            ctx.out(f"  {DIM}[{elapsed:.1f}ms]{RESET}")


# ─────────────────────────────────────────────────────────────
#  CONSOLE APPLICATION  (REPL)
# ─────────────────────────────────────────────────────────────
class ConsoleApplication:
    """
    The main REPL engine.

    Flow
    ────
    1. read raw input line
    2. tokenise with shlex.split (respects quoted strings)
    3. resolve command name → Command via registry
    4. run middleware.before()
    5. parse_args() → kwargs
    6. cmd.execute(ctx, **kwargs)
    7. run middleware.after()
    """

    VERSION = "1.0.0"

    def __init__(
        self,
        name:    str = "Console",
        prompt:  str = ">>> ",
        version: str = "1.0.0",
        timing:  bool = False,
    ):
        self._name    = name
        self._prompt  = prompt
        self._version = version
        self._registry   = CommandRegistry()
        self._context    = ConsoleContext(self)
        self._middleware: list[Middleware] = []
        self._history:    list[str]        = []
        self._running     = False

        if timing:
            self._middleware.append(LoggingMiddleware())

        # Register all built-in commands
        _register_builtins(self._registry)

    # ── properties ───────────────────────────────────────────
    @property
    def registry(self) -> CommandRegistry:
        return self._registry

    @property
    def context(self) -> ConsoleContext:
        return self._context

    @property
    def history(self) -> list[str]:
        return list(self._history)

    @property
    def name(self) -> str:
        return self._name

    @property
    def version(self) -> str:
        return self._version

    # ── middleware ───────────────────────────────────────────
    def use(self, middleware: Middleware):
        """Attach a middleware instance."""
        self._middleware.append(middleware)

    # ── execution ────────────────────────────────────────────
    def execute(self, line: str) -> bool:
        """
        Parse and run one command line.
        Returns False if the app should stop (exit command).
        """
        line = line.strip()
        if not line or line.startswith("#"):
            return True

        self._history.append(line)

        try:
            tokens = shlex.split(line)
        except ValueError as exc:
            self._context.error(f"Parse error: {exc}")
            return True

        cmd_name, *raw_args = tokens

        # Check runtime aliases set via `alias` command
        rt_aliases: dict[str, str] = getattr(self, "_rt_aliases", {})
        if cmd_name in rt_aliases:
            # Expand alias and re-parse
            expanded = rt_aliases[cmd_name] + (
                " " + " ".join(raw_args) if raw_args else ""
            )
            return self.execute(expanded)

        try:
            cmd = self._registry.get(cmd_name)
        except CommandNotFoundError as exc:
            self._context.error(str(exc))
            return True

        # Exit sentinel
        if cmd_name in ("exit", "quit"):
            return False

        kwargs: dict = {}
        error: Optional[Exception] = None

        # Pre-middleware
        proceed = True
        for mw in self._middleware:
            if not mw.before(self._context, cmd, kwargs):
                proceed = False
                break

        if proceed:
            try:
                kwargs = cmd.parse_args(raw_args)
                cmd.execute(self._context, **kwargs)
            except (CommandError, ArgumentError) as exc:
                error = exc
                self._context.error(str(exc))
            except Exception as exc:
                error = exc
                self._context.error(f"Unexpected error: {exc}")

        # Post-middleware
        for mw in self._middleware:
            mw.after(self._context, cmd, kwargs, error)

        return True

    # ── REPL loop ────────────────────────────────────────────
    def run(self):
        """Start the interactive REPL."""
        self._running = True
        _print_banner(self)

        while self._running:
            try:
                line = input(f"{CYAN}{self._prompt}{RESET}")
            except (EOFError, KeyboardInterrupt):
                print()
                self._context.info("Use 'exit' to quit.")
                continue

            if not self.execute(line):
                self._context.success("Goodbye!")
                self._running = False

    # ── batch mode ───────────────────────────────────────────
    def run_script(self, lines: list[str]):
        """Execute a list of command strings non-interactively."""
        for line in lines:
            if not self.execute(line):
                break


# ─────────────────────────────────────────────────────────────
#  BUILT-IN COMMANDS
# ─────────────────────────────────────────────────────────────

# ── help ─────────────────────────────────────────────────────
class HelpCommand(Command):
    name        = "help"
    description = "List all commands or show detail for a specific command."
    group       = "Framework"
    aliases     = ["?"]
    arguments   = [
        CommandArgument("command", "Command name to describe",
                        required=False, default=None),
    ]

    def execute(self, ctx: ConsoleContext, command=None, **_):
        if command:
            cmd = ctx.registry.resolve(command)
            if not cmd:
                ctx.error(f"No command named '{command}'.")
                return
            ctx.out(cmd.help_text())
            return

        ctx.out()
        ctx.line("═", 62, CYAN)
        ctx.out(f"  {BOLD}{CYAN}Available Commands{RESET}")
        ctx.line("═", 62, CYAN)

        for group, cmds in ctx.registry.groups().items():
            ctx.out(f"\n  {BOLD}{MAGENTA}{group}{RESET}")
            rows = []
            for c in cmds:
                all_aliases = ctx.registry.aliases_for(c.name)
                alias_hint  = (f"  {DIM}({', '.join(all_aliases)}){RESET}"
                               if all_aliases else "")
                rows.append((
                    f"  {CYAN}{c.name:<18}{RESET}{alias_hint}",
                    c.description,
                ))
            for name_col, desc_col in rows:
                print(f"    {name_col}  {DIM}{desc_col}{RESET}")

        ctx.out()
        total = len(ctx.registry)
        ctx.info(f"{total} command(s) registered. Type 'help <command>' for details.")
        ctx.line()


# ── version ──────────────────────────────────────────────────
class VersionCommand(Command):
    name        = "version"
    description = "Print framework and Python version information."
    group       = "Framework"
    aliases     = ["ver"]

    def execute(self, ctx: ConsoleContext, **_):
        import platform
        ctx.out(f"\n  {BOLD}Framework:{RESET}  {ctx.registry.resolve('version') and ''}"
                f"{ctx.history and ''}"  # access ctx to avoid unused warning
                )
        ctx.table(
            rows=[
                ("Framework",  "Console Mini Framework"),
                ("Version",    ConsoleApplication.VERSION),
                ("Python",     platform.python_version()),
                ("Platform",   platform.system()),
                ("Architecture", platform.machine()),
            ],
            col_colours=[CYAN, WHITE],
        )
        ctx.out()


# ── echo ─────────────────────────────────────────────────────
class EchoCommand(Command):
    name        = "echo"
    description = "Print text to the console."
    group       = "Text"
    arguments   = [
        CommandArgument("text", "Text to echo", variadic=True),
    ]

    def execute(self, ctx: ConsoleContext, text="", **_):
        ctx.out(f"  {text}")


# ── upper ─────────────────────────────────────────────────────
class UpperCommand(Command):
    name        = "upper"
    description = "Convert text to UPPER CASE."
    group       = "Text"
    arguments   = [
        CommandArgument("text", "Text to convert", variadic=True),
    ]

    def execute(self, ctx: ConsoleContext, text="", **_):
        ctx.out(f"  {text.upper()}")


# ── lower ─────────────────────────────────────────────────────
class LowerCommand(Command):
    name        = "lower"
    description = "Convert text to lower case."
    group       = "Text"
    arguments   = [
        CommandArgument("text", "Text to convert", variadic=True),
    ]

    def execute(self, ctx: ConsoleContext, text="", **_):
        ctx.out(f"  {text.lower()}")


# ── reverse ───────────────────────────────────────────────────
class ReverseCommand(Command):
    name        = "reverse"
    description = "Reverse a string."
    group       = "Text"
    arguments   = [
        CommandArgument("text", "Text to reverse", variadic=True),
    ]

    def execute(self, ctx: ConsoleContext, text="", **_):
        ctx.out(f"  {text[::-1]}")


# ── count ─────────────────────────────────────────────────────
class CountCommand(Command):
    name        = "count"
    description = "Count characters, words, and lines in text."
    group       = "Text"
    arguments   = [
        CommandArgument("text", "Text to count", variadic=True),
    ]

    def execute(self, ctx: ConsoleContext, text="", **_):
        chars   = len(text)
        words   = len(text.split())
        lines   = text.count("\n") + 1 if text else 0
        ctx.table(
            rows=[
                ("Characters", str(chars)),
                ("Words",      str(words)),
                ("Lines",      str(lines)),
            ],
            col_colours=[CYAN, WHITE],
        )


# ── calc ──────────────────────────────────────────────────────
class CalcCommand(Command):
    name        = "calc"
    description = "Evaluate a safe arithmetic expression."
    group       = "Utility"
    aliases     = ["math", "eval"]
    arguments   = [
        CommandArgument("expression", "Expression e.g. 2 + 3 * 4",
                        variadic=True),
    ]

    # Whitelist: digits, operators, parens, spaces, dots, percent
    _SAFE_PATTERN = re.compile(r"^[\d\s\+\-\*\/\(\)\.\%\*\*]+$")

    def execute(self, ctx: ConsoleContext, expression="", **_):
        expr = expression.strip()
        if not self._SAFE_PATTERN.match(expr):
            raise CommandError(
                "Expression contains unsafe characters. "
                "Only digits and operators (+,-,*,/,%,**,()) are allowed."
            )
        try:
            result = eval(expr, {"__builtins__": {}})  # noqa: S307
            ctx.out(f"\n  {CYAN}{expr}{RESET}  =  {BOLD}{WHITE}{result}{RESET}\n")
        except ZeroDivisionError:
            raise CommandError("Division by zero.")
        except Exception as exc:
            raise CommandError(f"Evaluation error: {exc}") from exc


# ── env ───────────────────────────────────────────────────────
class EnvCommand(Command):
    name        = "env"
    description = "Manage the environment key-value store."
    group       = "Utility"
    arguments   = [
        CommandArgument("action",
                        "set | get | del | list",
                        variadic=False),
        CommandArgument("key",
                        "Variable name (not needed for list)",
                        required=False, default=None),
        CommandArgument("value",
                        "Value (only for set)",
                        required=False, default=None, variadic=True),
    ]

    def execute(self, ctx: ConsoleContext,
                action="", key=None, value=None, **_):
        action = action.lower()

        if action == "list":
            env = ctx.env_all()
            if not env:
                ctx.info("Environment is empty.")
                return
            ctx.table(
                rows=[(k, v) for k, v in sorted(env.items())],
                headers=["Variable", "Value"],
                col_colours=[CYAN, WHITE],
            )

        elif action == "set":
            if not key:
                raise ArgumentError("Usage: env set <KEY> <value>")
            if value is None:
                raise ArgumentError("Usage: env set <KEY> <value>")
            ctx.env_set(key, value)
            ctx.success(f"${key.upper()} = {value!r}")

        elif action == "get":
            if not key:
                raise ArgumentError("Usage: env get <KEY>")
            val = ctx.env_get(key)
            if val is None:
                ctx.warn(f"${key.upper()} is not set.")
            else:
                ctx.out(f"  ${CYAN}{key.upper()}{RESET} = {WHITE}{val!r}{RESET}")

        elif action == "del":
            if not key:
                raise ArgumentError("Usage: env del <KEY>")
            if ctx.env_del(key):
                ctx.success(f"${key.upper()} deleted.")
            else:
                ctx.warn(f"${key.upper()} was not set.")
        else:
            raise CommandError(
                f"Unknown env action '{action}'. Use: set, get, del, list."
            )


# ── history ───────────────────────────────────────────────────
class HistoryCommand(Command):
    name        = "history"
    description = "Show command history."
    group       = "Framework"
    aliases     = ["hist"]
    arguments   = [
        CommandArgument("count", "Number of entries to show",
                        required=False, default=20, arg_type=int),
    ]

    def execute(self, ctx: ConsoleContext, count=20, **_):
        hist = ctx.history[-count:]
        if not hist:
            ctx.info("No history yet.")
            return
        ctx.out(f"\n  {BOLD}Command History{RESET}  (last {len(hist)})")
        ctx.line()
        for i, entry in enumerate(hist, 1):
            ctx.out(f"  {DIM}{i:>4}{RESET}  {entry}")
        ctx.out()


# ── alias ─────────────────────────────────────────────────────
class AliasCommand(Command):
    name        = "alias"
    description = "Define a runtime alias for a command."
    group       = "Framework"
    arguments   = [
        CommandArgument("alias_name", "New alias"),
        CommandArgument("command",    "Target command (+ args)",
                        variadic=True),
    ]

    def execute(self, ctx: ConsoleContext, alias_name="", command="", **_):
        # Store on the application object at runtime
        app = ctx._app  # intentional back-reference
        if not hasattr(app, "_rt_aliases"):
            app._rt_aliases = {}
        if alias_name in ctx.registry.command_names():
            raise CommandError(
                f"'{alias_name}' is already a registered command name."
            )
        app._rt_aliases[alias_name] = command
        ctx.success(f"Alias '{alias_name}' → '{command}' created.")


# ── clear ─────────────────────────────────────────────────────
class ClearCommand(Command):
    name        = "clear"
    description = "Clear the console screen."
    group       = "Framework"
    aliases     = ["cls"]

    def execute(self, ctx: ConsoleContext, **_):
        os.system("cls" if os.name == "nt" else "clear")


# ── exit / quit ───────────────────────────────────────────────
class ExitCommand(Command):
    name        = "exit"
    description = "Exit the console application."
    group       = "Framework"
    aliases     = ["quit", "bye"]

    def execute(self, ctx: ConsoleContext, **_):
        # Handled by the REPL loop; this body is never reached
        pass


# ── greet (example user-defined command) ─────────────────────
class GreetCommand(Command):
    name        = "greet"
    description = "Greet a user by name."
    group       = "Demo"
    arguments   = [
        CommandArgument("name",    "Name to greet"),
        CommandArgument("title",   "Optional title (Mr/Ms/Dr…)",
                        required=False, default=""),
        CommandArgument("shout",   "Uppercase the greeting",
                        required=False, default=False, arg_type=bool),
    ]

    def execute(self, ctx: ConsoleContext,
                name="", title="", shout=False, **_):
        full_name = f"{title} {name}".strip() if title else name
        msg = f"Hello, {full_name}! Welcome to the Console Framework."
        if shout:
            msg = msg.upper()
        ctx.out(f"\n  {GREEN}{msg}{RESET}\n")


# ── timer (example utility command) ──────────────────────────
class TimerCommand(Command):
    name        = "timer"
    description = "Run a countdown (demo of argument coercion)."
    group       = "Demo"
    arguments   = [
        CommandArgument("seconds", "Duration in seconds",
                        arg_type=int),
    ]

    def execute(self, ctx: ConsoleContext, seconds=0, **_):
        import time
        if seconds < 1 or seconds > 60:
            raise ArgumentError("Seconds must be between 1 and 60.")
        ctx.info(f"Counting down from {seconds}…")
        for i in range(seconds, 0, -1):
            print(f"\r  {YELLOW}{i:>3}{RESET}", end="", flush=True)
            time.sleep(1)
        print(f"\r  {GREEN}Done!      {RESET}")


# ── sysinfo ───────────────────────────────────────────────────
class SysInfoCommand(Command):
    name        = "sysinfo"
    description = "Display basic system information."
    group       = "Utility"
    aliases     = ["sys"]

    def execute(self, ctx: ConsoleContext, **_):
        import platform
        ctx.out(f"\n  {BOLD}System Information{RESET}")
        ctx.line()
        ctx.table(
            rows=[
                ("OS",          platform.system()),
                ("OS Release",  platform.release()),
                ("Machine",     platform.machine()),
                ("Processor",   platform.processor() or "N/A"),
                ("Python",      sys.version.split()[0]),
                ("Time",        datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
            ],
            col_colours=[CYAN, WHITE],
        )
        ctx.out()


# ─────────────────────────────────────────────────────────────
#  BUILT-IN REGISTRATION
# ─────────────────────────────────────────────────────────────
def _register_builtins(registry: CommandRegistry):
    for cmd_class in (
        HelpCommand,
        VersionCommand,
        EchoCommand,
        UpperCommand,
        LowerCommand,
        ReverseCommand,
        CountCommand,
        CalcCommand,
        EnvCommand,
        HistoryCommand,
        AliasCommand,
        ClearCommand,
        ExitCommand,
        GreetCommand,
        TimerCommand,
        SysInfoCommand,
    ):
        registry.register(cmd_class)


# ─────────────────────────────────────────────────────────────
#  BANNER
# ─────────────────────────────────────────────────────────────
def _print_banner(app: ConsoleApplication):
    print()
    print(f"{CYAN}{'═' * 64}{RESET}")
    print(f"""
  {BOLD}{CYAN}
   ██████╗ ██████╗ ███╗  ██╗███████╗ ██████╗ ██╗     ███████╗
  ██╔════╝██╔═══██╗████╗ ██║██╔════╝██╔═══██╗██║     ██╔════╝
  ██║     ██║   ██║██╔██╗██║███████╗██║   ██║██║     █████╗
  ██║     ██║   ██║██║╚████║╚════██║██║   ██║██║     ██╔══╝
  ╚██████╗╚██████╔╝██║ ╚███║███████║╚██████╔╝███████╗███████╗
   ╚═════╝ ╚═════╝ ╚═╝  ╚══╝╚══════╝ ╚═════╝ ╚══════╝╚══════╝
  {RESET}{BOLD}  M I N I   F R A M E W O R K   v{app.version}{RESET}
  {DIM}  Type 'help' to list commands. Type 'exit' to quit.{RESET}
""")
    print(f"{CYAN}{'═' * 64}{RESET}\n")


# ─────────────────────────────────────────────────────────────
#  ENTRY POINT
# ─────────────────────────────────────────────────────────────
def main():
    app = ConsoleApplication(
        name    = "Console Mini Framework",
        prompt  = "cmf> ",
        version = "1.0.0",
        timing  = False,     # set True to show execution time per command
    )

    # ── Show how easy it is to add a custom command via the
    #    decorator API (no class needed):
    @app.registry.command(
        "repeat",
        description = "Repeat text N times.",
        group       = "Demo",
        arguments   = [
            CommandArgument("times", "Repetition count",
                            arg_type=int),
            CommandArgument("text",  "Text to repeat",
                            variadic=True),
        ],
    )
    def repeat_cmd(ctx: ConsoleContext, times: int = 1, text: str = ""):
        if times < 1 or times > 50:
            raise ArgumentError("Times must be between 1 and 50.")
        ctx.out(("\n  " + text) * times + "\n")

    app.run()


if __name__ == "__main__":
    main()