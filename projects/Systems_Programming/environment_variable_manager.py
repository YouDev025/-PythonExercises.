"""
environment_variable_manager.py
A modular OOP-based environment variable manager with runtime overrides,
file import/export, and a full interactive console interface.
"""

from __future__ import annotations

import json
import os
import copy
import re
from datetime import datetime
from enum import Enum
from typing import Optional


# ─────────────────────────────────────────────
# Enums & Constants
# ─────────────────────────────────────────────

class Scope(str, Enum):
    USER   = "user"
    SYSTEM = "system"

VALID_KEY_RE = re.compile(r"^[A-Z_][A-Z0-9_]*$")   # POSIX-style variable names (uppercase)

COLORS = {
    "reset":  "\033[0m",
    "bold":   "\033[1m",
    "red":    "\033[91m",
    "green":  "\033[92m",
    "yellow": "\033[93m",
    "cyan":   "\033[96m",
    "blue":   "\033[94m",
    "grey":   "\033[90m",
}


def c(text: str, color: str) -> str:
    """Wrap text in ANSI colour codes."""
    return f"{COLORS.get(color, '')}{text}{COLORS['reset']}"


# ─────────────────────────────────────────────
# Core Domain Classes
# ─────────────────────────────────────────────

class EnvironmentVariable:
    """
    Represents a single environment variable with a key, value, scope,
    an optional description, and metadata timestamps.
    """

    def __init__(
        self,
        key: str,
        value: str,
        scope: Scope = Scope.USER,
        description: str = "",
    ) -> None:
        self.key         = self._validate_key(key)
        self.value       = str(value)
        self.scope       = Scope(scope)
        self.description = description.strip()
        self.created_at  = datetime.now().isoformat(timespec="seconds")
        self.updated_at  = self.created_at

    # ── Validation ─────────────────────────────

    @staticmethod
    def _validate_key(key: str) -> str:
        key = key.strip().upper()
        if not key:
            raise ValueError("Key must not be empty.")
        if not VALID_KEY_RE.match(key):
            raise ValueError(
                f"Invalid key '{key}'. Keys must start with a letter or underscore "
                "and contain only uppercase letters, digits, or underscores."
            )
        return key

    # ── Mutation ───────────────────────────────

    def update(self, value: str, description: Optional[str] = None) -> None:
        self.value      = str(value)
        self.updated_at = datetime.now().isoformat(timespec="seconds")
        if description is not None:
            self.description = description.strip()

    # ── Serialisation ──────────────────────────

    def to_dict(self) -> dict:
        return {
            "key":         self.key,
            "value":       self.value,
            "scope":       self.scope.value,
            "description": self.description,
            "created_at":  self.created_at,
            "updated_at":  self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "EnvironmentVariable":
        obj = cls(
            key         = data["key"],
            value       = data["value"],
            scope       = Scope(data.get("scope", "user")),
            description = data.get("description", ""),
        )
        obj.created_at = data.get("created_at", obj.created_at)
        obj.updated_at = data.get("updated_at", obj.updated_at)
        return obj

    # ── Dunder ─────────────────────────────────

    def __repr__(self) -> str:
        return (
            f"EnvironmentVariable(key={self.key!r}, value={self.value!r}, "
            f"scope={self.scope.value!r})"
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, EnvironmentVariable):
            return NotImplemented
        return self.key == other.key and self.scope == other.scope


# ─────────────────────────────────────────────

class EnvironmentStore:
    """
    Internal storage layer.  Keeps variables in two independent
    namespaces – USER and SYSTEM – keyed by variable name.
    """

    def __init__(self) -> None:
        self._store: dict[Scope, dict[str, EnvironmentVariable]] = {
            Scope.USER:   {},
            Scope.SYSTEM: {},
        }

    # ── Basic CRUD ─────────────────────────────

    def add(self, var: EnvironmentVariable) -> None:
        ns = self._store[var.scope]
        if var.key in ns:
            raise KeyError(f"Variable '{var.key}' already exists in scope '{var.scope.value}'.")
        ns[var.key] = var

    def get(self, key: str, scope: Scope) -> EnvironmentVariable:
        key = key.strip().upper()
        try:
            return self._store[scope][key]
        except KeyError:
            raise KeyError(f"Variable '{key}' not found in scope '{scope.value}'.")

    def update(self, key: str, scope: Scope, value: str, description: Optional[str] = None) -> None:
        var = self.get(key, scope)
        var.update(value, description)

    def delete(self, key: str, scope: Scope) -> EnvironmentVariable:
        key = key.strip().upper()
        try:
            return self._store[scope].pop(key)
        except KeyError:
            raise KeyError(f"Variable '{key}' not found in scope '{scope.value}'.")

    def exists(self, key: str, scope: Scope) -> bool:
        return key.strip().upper() in self._store[scope]

    # ── Bulk retrieval ─────────────────────────

    def all_variables(self) -> list[EnvironmentVariable]:
        result = []
        for ns in self._store.values():
            result.extend(ns.values())
        return result

    def by_scope(self, scope: Scope) -> list[EnvironmentVariable]:
        return list(self._store[scope].values())

    def search(self, pattern: str) -> list[EnvironmentVariable]:
        pattern = pattern.strip().upper()
        return [v for v in self.all_variables() if pattern in v.key or pattern in v.value]

    # ── Serialisation ──────────────────────────

    def to_dict(self) -> dict:
        return {
            scope.value: {k: v.to_dict() for k, v in ns.items()}
            for scope, ns in self._store.items()
        }

    def load_dict(self, data: dict) -> tuple[int, list[str]]:
        """Merge *data* into the store.  Returns (loaded_count, error_list)."""
        loaded, errors = 0, []
        for scope_str, variables in data.items():
            try:
                scope = Scope(scope_str)
            except ValueError:
                errors.append(f"Unknown scope '{scope_str}' – skipped.")
                continue
            for key, var_data in variables.items():
                try:
                    var = EnvironmentVariable.from_dict(var_data)
                    if self.exists(var.key, var.scope):
                        self.update(var.key, var.scope, var.value, var.description)
                    else:
                        self.add(var)
                    loaded += 1
                except Exception as exc:
                    errors.append(f"Error loading '{key}': {exc}")
        return loaded, errors

    def clear(self) -> None:
        for ns in self._store.values():
            ns.clear()


# ─────────────────────────────────────────────
# Manager (Service Layer)
# ─────────────────────────────────────────────

class EnvManager:
    """
    High-level façade over EnvironmentStore.
    Handles runtime overrides, file I/O, and business logic.
    """

    def __init__(self, store: Optional[EnvironmentStore] = None) -> None:
        self._store:     EnvironmentStore              = store or EnvironmentStore()
        self._overrides: dict[str, EnvironmentVariable] = {}   # key → temporary var
        self._override_stack: list[dict]               = []    # for nested contexts

    # ── Variable Operations ────────────────────

    def add(self, key: str, value: str, scope: Scope = Scope.USER, description: str = "") -> EnvironmentVariable:
        var = EnvironmentVariable(key, value, scope, description)
        self._store.add(var)
        return var

    def get(self, key: str, scope: Scope = Scope.USER) -> EnvironmentVariable:
        key = key.strip().upper()
        if key in self._overrides:
            return self._overrides[key]
        return self._store.get(key, scope)

    def update(self, key: str, scope: Scope, value: str, description: Optional[str] = None) -> None:
        self._store.update(key, scope, value, description)

    def delete(self, key: str, scope: Scope) -> EnvironmentVariable:
        return self._store.delete(key, scope)

    def list_all(self) -> list[EnvironmentVariable]:
        return self._store.all_variables()

    def list_by_scope(self, scope: Scope) -> list[EnvironmentVariable]:
        return self._store.by_scope(scope)

    def search(self, pattern: str) -> list[EnvironmentVariable]:
        return self._store.search(pattern)

    def exists(self, key: str, scope: Scope) -> bool:
        return self._store.exists(key, scope)

    # ── Runtime Overrides ─────────────────────

    def set_override(self, key: str, value: str, description: str = "runtime override") -> None:
        """Temporarily shadow a variable for the current session."""
        key = key.strip().upper()
        var = EnvironmentVariable(key, value, Scope.USER, description)
        self._overrides[key] = var

    def clear_override(self, key: str) -> bool:
        key = key.strip().upper()
        if key in self._overrides:
            del self._overrides[key]
            return True
        return False

    def clear_all_overrides(self) -> int:
        count = len(self._overrides)
        self._overrides.clear()
        return count

    def list_overrides(self) -> list[EnvironmentVariable]:
        return list(self._overrides.values())

    def push_override_context(self, overrides: dict[str, str]) -> None:
        """Save current overrides and apply a new set (context manager pattern)."""
        self._override_stack.append(copy.deepcopy(self._overrides))
        for k, v in overrides.items():
            self.set_override(k, v)

    def pop_override_context(self) -> None:
        """Restore the previous set of overrides."""
        if self._override_stack:
            self._overrides = self._override_stack.pop()
        else:
            self._overrides.clear()

    # ── File I/O ───────────────────────────────

    def export_json(self, filepath: str) -> int:
        """Export all variables to a JSON file.  Returns variable count."""
        data = {
            "exported_at": datetime.now().isoformat(timespec="seconds"),
            "variables":   self._store.to_dict(),
        }
        filepath = os.path.expanduser(filepath)
        with open(filepath, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2)
        return len(self._store.all_variables())

    def import_json(self, filepath: str) -> tuple[int, list[str]]:
        """Import variables from a JSON file.  Returns (count, errors)."""
        filepath = os.path.expanduser(filepath)
        if not os.path.isfile(filepath):
            raise FileNotFoundError(f"File not found: {filepath}")
        with open(filepath, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        variables_data = data.get("variables", data)   # support bare dict too
        return self._store.load_dict(variables_data)

    def export_env(self, filepath: str) -> int:
        """Export variables in shell .env format (KEY=value)."""
        filepath = os.path.expanduser(filepath)
        lines = [f"# Generated by EnvManager – {datetime.now().isoformat(timespec='seconds')}\n"]
        for var in sorted(self._store.all_variables(), key=lambda v: v.key):
            if var.description:
                lines.append(f"# {var.description}\n")
            lines.append(f"{var.key}={var.value}\n")
        with open(filepath, "w", encoding="utf-8") as fh:
            fh.writelines(lines)
        return len(self._store.all_variables())

    def reset_store(self) -> None:
        self._store.clear()
        self._overrides.clear()
        self._override_stack.clear()


# ─────────────────────────────────────────────
# Console UI
# ─────────────────────────────────────────────

class ConsoleUI:
    """Interactive terminal interface for EnvManager."""

    BANNER = r"""
  _____           __  __
 | ____|_ ____   |  \/  | __ _ _ __   __ _  __ _  ___ _ __
 |  _| | '_ \ \ / / |\/| |/ _` | '_ \ / _` |/ _` |/ _ \ '__|
 | |___| | | \ V /| |  | | (_| | | | | (_| | (_| |  __/ |
 |_____|_| |_|\_/ |_|  |_|\__,_|_| |_|\__,_|\__, |\___|_|
                                              |___/
"""

    MENU = """
{bold}──────────────────────────────────────────────{reset}
  {cyan}1{reset}  List all variables
  {cyan}2{reset}  List by scope
  {cyan}3{reset}  Get variable
  {cyan}4{reset}  Set variable
  {cyan}5{reset}  Update variable
  {cyan}6{reset}  Delete variable
  {cyan}7{reset}  Search variables
  {cyan}8{reset}  Runtime overrides
  {cyan}9{reset}  Export variables
  {cyan}10{reset} Import variables
  {cyan}11{reset} Reset store
  {cyan}0{reset}  Exit
{bold}──────────────────────────────────────────────{reset}
"""

    def __init__(self) -> None:
        self.manager = EnvManager()
        self._seed_demo_data()

    # ── Demo seed ──────────────────────────────

    def _seed_demo_data(self) -> None:
        samples = [
            ("HOME",        "/home/user",          Scope.USER,   "User home directory"),
            ("SHELL",       "/bin/bash",            Scope.USER,   "Default shell"),
            ("EDITOR",      "vim",                  Scope.USER,   "Preferred text editor"),
            ("PATH",        "/usr/local/bin:/usr/bin:/bin", Scope.SYSTEM, "Executable search path"),
            ("JAVA_HOME",   "/usr/lib/jvm/java-17", Scope.SYSTEM, "Java installation path"),
            ("LOG_LEVEL",   "INFO",                 Scope.SYSTEM, "Application log level"),
        ]
        for key, value, scope, desc in samples:
            try:
                self.manager.add(key, value, scope, desc)
            except Exception:
                pass

    # ── Helpers ────────────────────────────────

    @staticmethod
    def _fmt(text: str) -> str:
        return text.format(**COLORS)

    def _print_table(self, variables: list[EnvironmentVariable], title: str = "Variables") -> None:
        if not variables:
            print(c("  (none)", "grey"))
            return
        col_w = {"key": 20, "value": 32, "scope": 8, "desc": 26}
        header = (
            f"  {'KEY':<{col_w['key']}} {'VALUE':<{col_w['value']}} "
            f"{'SCOPE':<{col_w['scope']}} {'DESCRIPTION':<{col_w['desc']}}"
        )
        sep = "  " + "─" * (sum(col_w.values()) + 3 * len(col_w))
        print(c(f"\n  ── {title} ({len(variables)}) ──", "bold"))
        print(c(header, "cyan"))
        print(c(sep, "grey"))
        for v in sorted(variables, key=lambda x: (x.scope.value, x.key)):
            scope_color = "yellow" if v.scope == Scope.USER else "blue"
            key_str   = v.key[:col_w["key"]].ljust(col_w["key"])
            val_str   = (v.value[:col_w["value"] - 1] + "…" if len(v.value) > col_w["value"] else v.value).ljust(col_w["value"])
            scope_str = v.scope.value.ljust(col_w["scope"])
            desc_str  = (v.description[:col_w["desc"] - 1] + "…" if len(v.description) > col_w["desc"] else v.description).ljust(col_w["desc"])
            print(
                f"  {c(key_str, 'bold')} {c(val_str, 'reset')} "
                f"{c(scope_str, scope_color)} {c(desc_str, 'grey')}"
            )
        print()

    @staticmethod
    def _prompt(label: str, default: str = "") -> str:
        suffix = f" [{default}]" if default else ""
        try:
            val = input(f"  {c(label + suffix + ': ', 'cyan')}").strip()
        except (EOFError, KeyboardInterrupt):
            val = ""
        return val or default

    @staticmethod
    def _choose_scope() -> Scope:
        raw = ConsoleUI._prompt("Scope (user/system)", "user").lower()
        try:
            return Scope(raw)
        except ValueError:
            print(c("  Invalid scope; defaulting to 'user'.", "yellow"))
            return Scope.USER

    @staticmethod
    def _ok(msg: str)  -> None: print(c(f"  ✔  {msg}", "green"))
    @staticmethod
    def _err(msg: str) -> None: print(c(f"  ✖  {msg}", "red"))
    @staticmethod
    def _info(msg: str) -> None: print(c(f"  ℹ  {msg}", "yellow"))

    # ── Menu actions ───────────────────────────

    def _action_list_all(self) -> None:
        self._print_table(self.manager.list_all(), "All Variables")
        overrides = self.manager.list_overrides()
        if overrides:
            self._print_table(overrides, "Active Overrides (runtime)")

    def _action_list_by_scope(self) -> None:
        scope = self._choose_scope()
        self._print_table(self.manager.list_by_scope(scope), f"{scope.value.title()} Variables")

    def _action_get(self) -> None:
        key   = self._prompt("Key").upper()
        scope = self._choose_scope()
        try:
            var = self.manager.get(key, scope)
            print(c(f"\n  {'Key':12}: {var.key}", "bold"))
            print(f"  {'Value':12}: {c(var.value, 'green')}")
            print(f"  {'Scope':12}: {c(var.scope.value, 'yellow')}")
            print(f"  {'Description':12}: {var.description or '—'}")
            print(f"  {'Created':12}: {c(var.created_at, 'grey')}")
            print(f"  {'Updated':12}: {c(var.updated_at, 'grey')}")
            print()
        except KeyError as exc:
            self._err(str(exc))

    def _action_set(self) -> None:
        key   = self._prompt("Key")
        value = self._prompt("Value")
        scope = self._choose_scope()
        desc  = self._prompt("Description (optional)", "")
        try:
            var = self.manager.add(key, value, scope, desc)
            self._ok(f"Added  {c(var.key, 'bold')}  →  {var.value}")
        except (KeyError, ValueError) as exc:
            self._err(str(exc))

    def _action_update(self) -> None:
        key   = self._prompt("Key").upper()
        scope = self._choose_scope()
        if not self.manager.exists(key, scope):
            self._err(f"Variable '{key}' not found in scope '{scope.value}'.")
            return
        current = self.manager.get(key, scope)
        value = self._prompt("New value", current.value)
        desc  = self._prompt("New description (blank = keep)", current.description)
        try:
            self.manager.update(key, scope, value, desc if desc != current.description else None)
            self._ok(f"Updated  {c(key, 'bold')}")
        except (KeyError, ValueError) as exc:
            self._err(str(exc))

    def _action_delete(self) -> None:
        key   = self._prompt("Key").upper()
        scope = self._choose_scope()
        confirm = self._prompt(f"Delete '{key}' from '{scope.value}'? (yes/no)", "no").lower()
        if confirm not in ("yes", "y"):
            self._info("Deletion cancelled.")
            return
        try:
            self.manager.delete(key, scope)
            self._ok(f"Deleted  {c(key, 'bold')}")
        except KeyError as exc:
            self._err(str(exc))

    def _action_search(self) -> None:
        pattern = self._prompt("Search pattern")
        results = self.manager.search(pattern)
        self._print_table(results, f"Search: '{pattern}'")
        if not results:
            self._info("No matches found.")

    def _action_overrides(self) -> None:
        print(c("\n  Override sub-menu:", "bold"))
        print("  a) Set override   b) Clear override   c) Clear all   d) List   e) Back")
        choice = self._prompt("Choice").lower()
        if choice == "a":
            key   = self._prompt("Key").upper()
            value = self._prompt("Value")
            self.manager.set_override(key, value)
            self._ok(f"Override set:  {c(key, 'bold')}  →  {value}")
        elif choice == "b":
            key = self._prompt("Key").upper()
            if self.manager.clear_override(key):
                self._ok(f"Override cleared for  {c(key, 'bold')}")
            else:
                self._info(f"No active override for '{key}'.")
        elif choice == "c":
            n = self.manager.clear_all_overrides()
            self._ok(f"Cleared {n} override(s).")
        elif choice == "d":
            self._print_table(self.manager.list_overrides(), "Active Overrides")
        else:
            self._info("Returning to main menu.")

    def _action_export(self) -> None:
        print("  Format:  a) JSON   b) .env")
        fmt = self._prompt("Choice", "a").lower()
        default_file = "env_export.json" if fmt == "a" else "env_export.env"
        filepath = self._prompt("File path", default_file)
        try:
            if fmt == "b":
                n = self.manager.export_env(filepath)
            else:
                n = self.manager.export_json(filepath)
            self._ok(f"Exported {n} variable(s) to  {c(filepath, 'bold')}")
        except OSError as exc:
            self._err(f"Export failed: {exc}")

    def _action_import(self) -> None:
        filepath = self._prompt("JSON file path", "env_export.json")
        try:
            n, errors = self.manager.import_json(filepath)
            self._ok(f"Loaded {n} variable(s) from  {c(filepath, 'bold')}")
            for e in errors:
                self._err(e)
        except (FileNotFoundError, json.JSONDecodeError, OSError) as exc:
            self._err(f"Import failed: {exc}")

    def _action_reset(self) -> None:
        confirm = self._prompt("Reset ALL variables? This cannot be undone. (yes/no)", "no").lower()
        if confirm in ("yes", "y"):
            self.manager.reset_store()
            self._ok("Store reset.  All variables removed.")
        else:
            self._info("Reset cancelled.")

    # ── Main loop ──────────────────────────────

    def run(self) -> None:
        print(c(self.BANNER, "cyan"))
        print(c("  Environment Variable Manager  •  Type 0 to exit", "bold"))
        actions = {
            "1":  self._action_list_all,
            "2":  self._action_list_by_scope,
            "3":  self._action_get,
            "4":  self._action_set,
            "5":  self._action_update,
            "6":  self._action_delete,
            "7":  self._action_search,
            "8":  self._action_overrides,
            "9":  self._action_export,
            "10": self._action_import,
            "11": self._action_reset,
        }
        while True:
            print(self._fmt(self.MENU))
            choice = self._prompt("Select option").strip()
            if choice == "0":
                print(c("\n  Goodbye!\n", "green"))
                break
            action = actions.get(choice)
            if action:
                try:
                    action()
                except Exception as exc:          # safety net
                    self._err(f"Unexpected error: {exc}")
            else:
                self._info("Unknown option – please choose from the menu.")


# ─────────────────────────────────────────────
# Entry Point
# ─────────────────────────────────────────────

def main() -> None:
    ui = ConsoleUI()
    ui.run()



if __name__ == "__main__":
    main()