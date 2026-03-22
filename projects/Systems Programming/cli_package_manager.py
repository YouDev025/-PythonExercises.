"""
cli_package_manager.py
A simulated command-line package manager built with Python OOP.
Supports install, uninstall, update, search, and dependency resolution.
"""

from __future__ import annotations
import sys
import textwrap
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set
from enum import Enum, auto


# ──────────────────────────────────────────────
# Enums & Exceptions
# ──────────────────────────────────────────────

class InstallStatus(Enum):
    INSTALLED = auto()
    NOT_INSTALLED = auto()
    OUTDATED = auto()


class PackageError(Exception):
    """Base exception for all package-manager errors."""


class PackageNotFoundError(PackageError):
    def __init__(self, name: str):
        super().__init__(f"Package '{name}' not found in repository.")


class CircularDependencyError(PackageError):
    def __init__(self, cycle: List[str]):
        path = " → ".join(cycle)
        super().__init__(f"Circular dependency detected: {path}")


class DependencyConflictError(PackageError):
    pass


class AlreadyInstalledError(PackageError):
    def __init__(self, name: str, version: str):
        super().__init__(f"Package '{name}' (v{version}) is already installed.")


class NotInstalledError(PackageError):
    def __init__(self, name: str):
        super().__init__(f"Package '{name}' is not installed.")


class ValidationError(PackageError):
    pass


# ──────────────────────────────────────────────
# Package
# ──────────────────────────────────────────────

@dataclass
class Package:
    """Represents a single software package."""
    name: str
    version: str
    description: str
    dependencies: List[str] = field(default_factory=list)   # names only
    installation_status: InstallStatus = InstallStatus.NOT_INSTALLED

    # ── validation ──────────────────────────────
    def __post_init__(self) -> None:
        self._validate_name(self.name)
        self._validate_version(self.version)

    @staticmethod
    def _validate_name(name: str) -> None:
        if not name or not name.replace("-", "").replace("_", "").isalnum():
            raise ValidationError(
                f"Invalid package name '{name}'. Use letters, digits, hyphens, or underscores."
            )

    @staticmethod
    def _validate_version(version: str) -> None:
        parts = version.split(".")
        if not (1 <= len(parts) <= 3) or not all(p.isdigit() for p in parts):
            raise ValidationError(
                f"Invalid version '{version}'. Expected format: MAJOR[.MINOR[.PATCH]]."
            )

    # ── helpers ──────────────────────────────────
    def version_tuple(self) -> tuple:
        return tuple(int(p) for p in self.version.split("."))

    @property
    def is_installed(self) -> bool:
        return self.installation_status == InstallStatus.INSTALLED

    def mark_installed(self) -> None:
        self.installation_status = InstallStatus.INSTALLED

    def mark_uninstalled(self) -> None:
        self.installation_status = InstallStatus.NOT_INSTALLED

    def mark_outdated(self) -> None:
        self.installation_status = InstallStatus.OUTDATED

    # ── display ──────────────────────────────────
    def short_info(self) -> str:
        status_icon = {
            InstallStatus.INSTALLED: "✔",
            InstallStatus.NOT_INSTALLED: "○",
            InstallStatus.OUTDATED: "↑",
        }[self.installation_status]
        deps = ", ".join(self.dependencies) if self.dependencies else "none"
        return (
            f"  {status_icon} {self.name:<20} v{self.version:<10} "
            f"deps=[{deps}]  {self.description}"
        )

    def __repr__(self) -> str:
        return f"Package(name={self.name!r}, version={self.version!r}, status={self.installation_status.name})"


# ──────────────────────────────────────────────
# Repository
# ──────────────────────────────────────────────

class Repository:
    """Stores and manages available package metadata."""

    def __init__(self, name: str = "default") -> None:
        self.name = name
        self._packages: Dict[str, Package] = {}   # name → latest Package

    # ── mutations ───────────────────────────────
    def add_package(self, pkg: Package) -> None:
        """Add or overwrite a package entry in the repo."""
        if pkg.name in self._packages:
            existing = self._packages[pkg.name]
            if pkg.version_tuple() <= existing.version_tuple():
                raise PackageError(
                    f"Repository already has '{pkg.name}' v{existing.version}. "
                    f"New version ({pkg.version}) must be higher."
                )
        self._packages[pkg.name] = pkg

    def remove_package(self, name: str) -> None:
        if name not in self._packages:
            raise PackageNotFoundError(name)
        del self._packages[name]

    # ── queries ─────────────────────────────────
    def get(self, name: str) -> Package:
        if name not in self._packages:
            raise PackageNotFoundError(name)
        return self._packages[name]

    def exists(self, name: str) -> bool:
        return name in self._packages

    def search(self, query: str) -> List[Package]:
        q = query.lower()
        return [
            p for p in self._packages.values()
            if q in p.name.lower() or q in p.description.lower()
        ]

    def all_packages(self) -> List[Package]:
        return sorted(self._packages.values(), key=lambda p: p.name)

    def __len__(self) -> int:
        return len(self._packages)

    def __repr__(self) -> str:
        return f"Repository(name={self.name!r}, packages={len(self)})"


# ──────────────────────────────────────────────
# DependencyResolver
# ──────────────────────────────────────────────

class DependencyResolver:
    """
    Resolves installation order via topological sort (DFS).
    Detects circular dependencies before any package is installed.
    """

    def __init__(self, repo: Repository) -> None:
        self._repo = repo

    # ── public API ──────────────────────────────
    def resolve(self, package_name: str) -> List[str]:
        """
        Return an ordered list of package names that must be installed
        (dependencies first, target last) to satisfy all requirements.
        Already-installed packages are excluded from the result.
        Raises CircularDependencyError if a cycle is found.
        Raises PackageNotFoundError if any dependency is missing.
        """
        order: List[str] = []
        visited: Set[str] = set()
        self._dfs(package_name, visited, set(), order)
        return order

    def detect_conflicts(self, names: List[str]) -> List[str]:
        """
        Simple conflict detection: returns a list of human-readable
        conflict messages when two packages in *names* share a dependency
        that doesn't exist in the repository.
        """
        conflicts: List[str] = []
        for name in names:
            if not self._repo.exists(name):
                conflicts.append(f"'{name}' not found in repository.")
                continue
            pkg = self._repo.get(name)
            for dep in pkg.dependencies:
                if not self._repo.exists(dep):
                    conflicts.append(
                        f"'{name}' requires '{dep}', which is not in the repository."
                    )
        return conflicts

    # ── internals ───────────────────────────────
    def _dfs(
        self,
        name: str,
        visited: Set[str],
        in_stack: Set[str],
        order: List[str],
    ) -> None:
        if name in in_stack:
            cycle = list(in_stack) + [name]
            raise CircularDependencyError(cycle)

        if name in visited:
            return

        pkg = self._repo.get(name)          # raises PackageNotFoundError if missing
        in_stack.add(name)

        for dep_name in pkg.dependencies:
            self._dfs(dep_name, visited, in_stack, order)

        in_stack.discard(name)
        visited.add(name)

        if not pkg.is_installed:
            order.append(name)


# ──────────────────────────────────────────────
# PackageManager
# ──────────────────────────────────────────────

class PackageManager:
    """
    High-level orchestrator for install / uninstall / update / list operations.
    Delegates resolution to DependencyResolver and storage to Repository.
    """

    def __init__(self, repo: Repository) -> None:
        self._repo = repo
        self._resolver = DependencyResolver(repo)
        self._installed: Dict[str, Package] = {}   # name → installed Package

    # ── install ─────────────────────────────────
    def install(self, name: str) -> List[str]:
        """
        Install *name* and all its unsatisfied dependencies.
        Returns the list of packages that were actually installed.
        Raises AlreadyInstalledError, PackageNotFoundError, or CircularDependencyError.
        """
        if name in self._installed:
            raise AlreadyInstalledError(name, self._installed[name].version)

        conflicts = self._resolver.detect_conflicts([name])
        if conflicts:
            raise DependencyConflictError("\n  ".join(conflicts))

        install_order = self._resolver.resolve(name)

        newly_installed: List[str] = []
        for pkg_name in install_order:
            pkg = self._repo.get(pkg_name)
            pkg.mark_installed()
            self._installed[pkg_name] = pkg
            newly_installed.append(pkg_name)

        return newly_installed

    # ── uninstall ───────────────────────────────
    def uninstall(self, name: str, *, force: bool = False) -> List[str]:
        """
        Uninstall *name*.  By default raises if other installed packages depend on it.
        Pass force=True to remove anyway.
        Returns list of removed package names.
        """
        if name not in self._installed:
            raise NotInstalledError(name)

        # Check reverse-dependencies
        dependents = self._reverse_deps(name)
        if dependents and not force:
            dep_list = ", ".join(dependents)
            raise PackageError(
                f"Cannot uninstall '{name}': required by [{dep_list}]. "
                f"Use --force to override."
            )

        pkg = self._installed.pop(name)
        pkg.mark_uninstalled()
        return [name]

    # ── update ──────────────────────────────────
    def update(self, name: str) -> Optional[str]:
        """
        Update *name* to the latest version available in the repository.
        Returns the new version string, or None if already up-to-date.
        """
        if name not in self._installed:
            raise NotInstalledError(name)

        repo_pkg = self._repo.get(name)
        installed_pkg = self._installed[name]

        if repo_pkg.version_tuple() <= installed_pkg.version_tuple():
            return None   # already at the latest version

        # Perform the upgrade
        installed_pkg.mark_uninstalled()
        repo_pkg.mark_installed()
        self._installed[name] = repo_pkg
        return repo_pkg.version

    # ── list / search ───────────────────────────
    def list_installed(self) -> List[Package]:
        return sorted(self._installed.values(), key=lambda p: p.name)

    def search(self, query: str) -> List[Package]:
        return self._repo.search(query)

    def info(self, name: str) -> Package:
        return self._repo.get(name)

    # ── internals ───────────────────────────────
    def _reverse_deps(self, name: str) -> List[str]:
        """Return names of installed packages that directly depend on *name*."""
        return [
            pkg.name
            for pkg in self._installed.values()
            if name in pkg.dependencies
        ]


# ──────────────────────────────────────────────
# CLI  (presentation layer)
# ──────────────────────────────────────────────

HELP_TEXT = textwrap.dedent("""\
    ┌─────────────────────────────────────────────────────┐
    │              cli_package_manager  v1.0              │
    │         A simulated Python package manager          │
    └─────────────────────────────────────────────────────┘

    Commands
    ────────
      install   <name>          Install a package (+ dependencies)
      uninstall <name> [--force] Uninstall a package
      update    <name>          Update a package to the latest version
      list                      List installed packages
      search    <query>         Search repository for packages
      info      <name>          Show detailed package info
      repo                      List all packages in the repository
      help                      Show this help message
      exit / quit               Exit the program
""")

# ── ANSI helpers ─────────────────────────────

def _c(text: str, code: str) -> str:
    """Wrap text in an ANSI colour code (resets after)."""
    return f"\033[{code}m{text}\033[0m"

def ok(msg: str)    -> None: print(_c(f"  ✔  {msg}", "32"))
def err(msg: str)   -> None: print(_c(f"  ✘  {msg}", "31"))
def info(msg: str)  -> None: print(_c(f"  ℹ  {msg}", "36"))
def warn(msg: str)  -> None: print(_c(f"  ⚠  {msg}", "33"))
def head(msg: str)  -> None: print(_c(msg, "1;34"))


# ── command handlers ─────────────────────────

def cmd_install(pm: PackageManager, args: List[str]) -> None:
    if not args:
        err("Usage: install <package_name>"); return
    name = args[0]
    try:
        installed = pm.install(name)
        for pkg_name in installed[:-1]:
            ok(f"Installed dependency: {pkg_name}")
        ok(f"Successfully installed: {installed[-1]}")
    except AlreadyInstalledError as e:
        warn(str(e))
    except PackageError as e:
        err(str(e))


def cmd_uninstall(pm: PackageManager, args: List[str]) -> None:
    if not args:
        err("Usage: uninstall <package_name> [--force]"); return
    name = args[0]
    force = "--force" in args
    try:
        pm.uninstall(name, force=force)
        ok(f"Uninstalled: {name}")
    except PackageError as e:
        err(str(e))


def cmd_update(pm: PackageManager, args: List[str]) -> None:
    if not args:
        err("Usage: update <package_name>"); return
    name = args[0]
    try:
        new_ver = pm.update(name)
        if new_ver:
            ok(f"Updated '{name}' → v{new_ver}")
        else:
            info(f"'{name}' is already at the latest version.")
    except PackageError as e:
        err(str(e))


def cmd_list(pm: PackageManager, _args: List[str]) -> None:
    pkgs = pm.list_installed()
    if not pkgs:
        info("No packages installed."); return
    head(f"\n  Installed packages ({len(pkgs)})")
    print("  " + "─" * 65)
    for p in pkgs:
        print(p.short_info())
    print()


def cmd_search(pm: PackageManager, args: List[str]) -> None:
    if not args:
        err("Usage: search <query>"); return
    query = " ".join(args)
    results = pm.search(query)
    if not results:
        info(f"No packages matched '{query}'."); return
    head(f"\n  Search results for '{query}' ({len(results)} found)")
    print("  " + "─" * 65)
    for p in results:
        print(p.short_info())
    print()


def cmd_info(pm: PackageManager, args: List[str]) -> None:
    if not args:
        err("Usage: info <package_name>"); return
    name = args[0]
    try:
        p = pm.info(name)
        head(f"\n  Package: {p.name}")
        print(f"  Version     : {p.version}")
        print(f"  Status      : {p.installation_status.name}")
        print(f"  Description : {p.description}")
        deps = ", ".join(p.dependencies) if p.dependencies else "none"
        print(f"  Dependencies: {deps}\n")
    except PackageError as e:
        err(str(e))


def cmd_repo(pm: PackageManager, _args: List[str]) -> None:
    pkgs = pm._repo.all_packages()
    head(f"\n  Repository — {len(pkgs)} packages available")
    print("  " + "─" * 65)
    for p in pkgs:
        print(p.short_info())
    print()


# ── command dispatch ─────────────────────────

COMMANDS = {
    "install"  : cmd_install,
    "uninstall": cmd_uninstall,
    "update"   : cmd_update,
    "list"     : cmd_list,
    "search"   : cmd_search,
    "info"     : cmd_info,
    "repo"     : cmd_repo,
}


# ──────────────────────────────────────────────
# Sample seed data
# ──────────────────────────────────────────────

def _build_sample_repo() -> Repository:
    repo = Repository("PyPI-mirror")

    packages = [
        Package("requests",   "2.31.0", "HTTP library for Python",
                dependencies=["urllib3", "certifi"]),
        Package("urllib3",    "2.0.7",  "HTTP client library",
                dependencies=[]),
        Package("certifi",    "2023.11.17", "Mozilla's CA Bundle",
                dependencies=[]),
        Package("numpy",      "1.26.2", "Fundamental array library",
                dependencies=[]),
        Package("pandas",     "2.1.3",  "Data analysis and manipulation",
                dependencies=["numpy", "python-dateutil"]),
        Package("python-dateutil", "2.8.2", "Date utilities for Python",
                dependencies=[]),
        Package("matplotlib", "3.8.2",  "Plotting and visualisation",
                dependencies=["numpy", "pillow"]),
        Package("pillow",     "10.1.0", "Python Imaging Library fork",
                dependencies=[]),
        Package("scikit-learn","1.3.2", "Machine-learning toolkit",
                dependencies=["numpy", "scipy"]),
        Package("scipy",      "1.11.4", "Scientific computing tools",
                dependencies=["numpy"]),
        Package("flask",      "3.0.0",  "Lightweight WSGI web framework",
                dependencies=["werkzeug", "jinja2", "click"]),
        Package("werkzeug",   "3.0.1",  "WSGI utility library",
                dependencies=["markupsafe"]),
        Package("jinja2",     "3.1.2",  "Fast templating engine",
                dependencies=["markupsafe"]),
        Package("markupsafe", "2.1.3",  "Safe string-markup helper",
                dependencies=[]),
        Package("click",      "8.1.7",  "CLI creation toolkit",
                dependencies=[]),
        Package("sqlalchemy", "2.0.23", "SQL toolkit and ORM",
                dependencies=[]),
        Package("pytest",     "7.4.3",  "Testing framework",
                dependencies=["pluggy"]),
        Package("pluggy",     "1.3.0",  "Plugin management system",
                dependencies=[]),
        Package("black",      "23.11.0","Opinionated code formatter",
                dependencies=["click"]),
        Package("mypy",       "1.7.1",  "Static type checker",
                dependencies=[]),
    ]

    for pkg in packages:
        repo.add_package(pkg)
    return repo


# ──────────────────────────────────────────────
# Entry point
# ──────────────────────────────────────────────

def main() -> None:
    repo = _build_sample_repo()
    pm   = PackageManager(repo)

    print(HELP_TEXT)
    info(f"Repository loaded: {len(repo)} packages available.")
    info("Legend:  ✔ installed   ○ available   ↑ outdated\n")

    while True:
        try:
            raw = input(_c("pkg> ", "1;32")).strip()
        except (EOFError, KeyboardInterrupt):
            print()
            info("Goodbye!"); break

        if not raw:
            continue

        tokens = raw.split()
        cmd, *args = tokens

        if cmd in ("exit", "quit"):
            info("Goodbye!"); break
        elif cmd == "help":
            print(HELP_TEXT)
        elif cmd in COMMANDS:
            COMMANDS[cmd](pm, args)
        else:
            err(f"Unknown command: '{cmd}'.  Type 'help' for available commands.")


if __name__ == "__main__":
    main()