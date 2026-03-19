"""
╔══════════════════════════════════════════════════════════════╗
║             File System Simulator  –  Python OOP             ║
║                                                              ║
║  Classes:                                                    ║
║    File          – leaf node with name, content, metadata    ║
║    Directory     – internal node with children               ║
║    PathResolver  – parses & resolves absolute/relative paths ║
║    FileSystem    – root + all high-level FS operations       ║
║    Shell         – interactive REPL with command dispatch    ║
╚══════════════════════════════════════════════════════════════╝
"""

from __future__ import annotations

import os
import shlex
import textwrap
from datetime import datetime
from typing import Dict, List, Optional, Union


# ═══════════════════════════════════════════════════════════════
# Exceptions
# ═══════════════════════════════════════════════════════════════

class FSError(Exception):
    """Base class for all file-system errors."""


class NotFoundError(FSError):
    def __init__(self, path: str):
        super().__init__(f"No such file or directory: '{path}'")


class AlreadyExistsError(FSError):
    def __init__(self, path: str):
        super().__init__(f"Already exists: '{path}'")


class NotADirectoryError_(FSError):        # avoids shadowing the built-in
    def __init__(self, path: str):
        super().__init__(f"Not a directory: '{path}'")


class IsADirectoryError_(FSError):
    def __init__(self, path: str):
        super().__init__(f"Is a directory: '{path}'")


class PermissionError_(FSError):
    def __init__(self, msg: str):
        super().__init__(msg)


class InvalidNameError(FSError):
    def __init__(self, name: str):
        super().__init__(f"Invalid name: '{name}'")


# ═══════════════════════════════════════════════════════════════
# File
# ═══════════════════════════════════════════════════════════════

class File:
    """
    Leaf node in the file-system tree.

    Attributes
    ----------
    name          : file name (no slashes)
    content       : raw text content
    creation_date : datetime when the file was created
    modified_date : datetime of last write
    """

    def __init__(self, name: str, content: str = "") -> None:
        self.name:          str      = name
        self.content:       str      = content
        self.creation_date: datetime = datetime.now()
        self.modified_date: datetime = self.creation_date

    # ── properties ────────────────────────────────────────────────────────────
    @property
    def size(self) -> int:
        """Size in bytes (UTF-8 encoded length of the content)."""
        return len(self.content.encode("utf-8"))

    @property
    def extension(self) -> str:
        """File extension (empty string if none)."""
        parts = self.name.rsplit(".", 1)
        return parts[1] if len(parts) == 2 else ""

    # ── read / write ──────────────────────────────────────────────────────────
    def read(self) -> str:
        return self.content

    def write(self, data: str, append: bool = False) -> None:
        if append:
            self.content += data
        else:
            self.content = data
        self.modified_date = datetime.now()

    # ── helpers ───────────────────────────────────────────────────────────────
    def stat(self) -> Dict[str, str]:
        return {
            "name":          self.name,
            "type":          "file",
            "size":          f"{self.size} bytes",
            "created":       self.creation_date.strftime("%Y-%m-%d %H:%M:%S"),
            "modified":      self.modified_date.strftime("%Y-%m-%d %H:%M:%S"),
            "extension":     self.extension or "(none)",
        }

    def __repr__(self) -> str:
        return f"File(name={self.name!r}, size={self.size})"


# ═══════════════════════════════════════════════════════════════
# Directory
# ═══════════════════════════════════════════════════════════════

class Directory:
    """
    Internal (branch) node in the file-system tree.

    Children are stored in an ordered dict so listings are stable.
    """

    def __init__(self, name: str, parent: Optional["Directory"] = None) -> None:
        self.name:          str                              = name
        self.parent:        Optional[Directory]             = parent
        self.creation_date: datetime                        = datetime.now()
        self._children:     Dict[str, Union[File, Directory]] = {}

    # ── child access ─────────────────────────────────────────────────────────
    def add(self, node: Union[File, "Directory"]) -> None:
        if node.name in self._children:
            raise AlreadyExistsError(node.name)
        self._children[node.name] = node

    def remove(self, name: str) -> None:
        if name not in self._children:
            raise NotFoundError(name)
        del self._children[name]

    def get(self, name: str) -> Union[File, "Directory"]:
        if name not in self._children:
            raise NotFoundError(name)
        return self._children[name]

    def __contains__(self, name: str) -> bool:
        return name in self._children

    # ── listing helpers ───────────────────────────────────────────────────────
    def list_children(self) -> List[Union[File, "Directory"]]:
        return list(self._children.values())

    @property
    def dirs(self) -> List["Directory"]:
        return [c for c in self._children.values() if isinstance(c, Directory)]

    @property
    def files(self) -> List[File]:
        return [c for c in self._children.values() if isinstance(c, File)]

    @property
    def total_size(self) -> int:
        """Recursive size of all files under this directory."""
        size = sum(f.size for f in self.files)
        size += sum(d.total_size for d in self.dirs)
        return size

    # ── metadata ──────────────────────────────────────────────────────────────
    def stat(self) -> Dict[str, str]:
        return {
            "name":          self.name,
            "type":          "directory",
            "children":      str(len(self._children)),
            "total_size":    f"{self.total_size} bytes",
            "created":       self.creation_date.strftime("%Y-%m-%d %H:%M:%S"),
        }

    def __repr__(self) -> str:
        return f"Directory(name={self.name!r}, children={len(self._children)})"


# ═══════════════════════════════════════════════════════════════
# PathResolver
# ═══════════════════════════════════════════════════════════════

class PathResolver:
    """
    Stateless helper for parsing and resolving paths.

    Supports:
      • Absolute paths starting with '/'
      • Relative paths (resolved against a supplied cwd)
      • '..'  (parent)  and  '.'  (current) components
      • Consecutive '//' slashes (normalised away)
    """

    SEPARATOR = "/"
    INVALID_CHARS = set('<>:"\\|?*\x00')

    # ── validation ────────────────────────────────────────────────────────────
    @staticmethod
    def validate_name(name: str) -> None:
        """Raise InvalidNameError if *name* is not acceptable as a file/dir name."""
        if not name:
            raise InvalidNameError("(empty string)")
        if name in (".", ".."):
            raise InvalidNameError(name)
        if PathResolver.SEPARATOR in name:
            raise InvalidNameError(name)
        if any(ch in PathResolver.INVALID_CHARS for ch in name):
            raise InvalidNameError(name)

    # ── splitting ─────────────────────────────────────────────────────────────
    @staticmethod
    def split(path: str) -> List[str]:
        """
        Split a path string into clean component parts.
        '/a//b/../c' → ['a', '..', 'c']  (keeps '..' for caller to resolve)
        """
        return [p for p in path.split(PathResolver.SEPARATOR) if p]

    @staticmethod
    def is_absolute(path: str) -> bool:
        return path.startswith(PathResolver.SEPARATOR)

    # ── resolution ────────────────────────────────────────────────────────────
    @staticmethod
    def resolve(path: str, cwd: Directory, root: Directory) -> Union[File, Directory]:
        """
        Walk the tree and return the node at *path*.

        Parameters
        ----------
        path : absolute or relative path string
        cwd  : current working directory
        root : the filesystem root

        Raises
        ------
        NotFoundError, NotADirectoryError_
        """
        node: Union[File, Directory] = root if PathResolver.is_absolute(path) else cwd
        parts = PathResolver.split(path)

        for i, part in enumerate(parts):
            if part == ".":
                continue
            if part == "..":
                if isinstance(node, Directory) and node.parent is not None:
                    node = node.parent
                # silently stay at root if '..' beyond root
                continue
            # descend one level
            if not isinstance(node, Directory):
                raise NotADirectoryError_(PathResolver.join(parts[:i]))
            node = node.get(part)          # raises NotFoundError if missing

        return node

    @staticmethod
    def resolve_parent(path: str, cwd: Directory, root: Directory):
        """
        Return (parent_directory, child_name) for *path*.

        Useful for create / delete operations where the final component
        does not yet exist (or is being removed).
        """
        parts = PathResolver.split(path)
        if not parts:
            raise FSError("Cannot resolve empty path.")

        child_name = parts[-1]
        parent_path_parts = parts[:-1]
        is_abs = PathResolver.is_absolute(path)

        if parent_path_parts:
            parent_path = (PathResolver.SEPARATOR if is_abs else "") + \
                          PathResolver.SEPARATOR.join(parent_path_parts)
            parent = PathResolver.resolve(parent_path, cwd, root)
        else:
            parent = root if is_abs else cwd

        if not isinstance(parent, Directory):
            raise NotADirectoryError_(path)

        return parent, child_name

    @staticmethod
    def join(*parts: str) -> str:
        return PathResolver.SEPARATOR.join(parts)

    # ── absolute path of a node ───────────────────────────────────────────────
    @staticmethod
    def abspath(node: Union[File, Directory], root: Directory) -> str:
        """Walk up via .parent links to build the absolute path string."""
        segments: List[str] = []
        current: Union[File, Directory] = node
        while True:
            segments.append(current.name)
            if current is root:
                break
            if isinstance(current, Directory):
                if current.parent is None:
                    break
                current = current.parent
            else:
                # File has no parent attr, but FileSystem always attaches one
                parent = getattr(current, "_parent_dir", None)
                if parent is None:
                    break
                current = parent
        segments.reverse()
        path = PathResolver.SEPARATOR.join(segments[1:])  # skip root name
        return PathResolver.SEPARATOR + path


# ═══════════════════════════════════════════════════════════════
# FileSystem
# ═══════════════════════════════════════════════════════════════

class FileSystem:
    """
    The main file-system manager.

    Keeps track of:
      • root     – the single root Directory
      • cwd      – current working directory
    """

    def __init__(self) -> None:
        self.root: Directory = Directory("/")
        self.root.parent = self.root          # root's parent is itself
        self._cwd: Directory = self.root

    # ── navigation ────────────────────────────────────────────────────────────
    @property
    def cwd(self) -> Directory:
        return self._cwd

    @property
    def cwd_path(self) -> str:
        return PathResolver.abspath(self._cwd, self.root)

    def cd(self, path: str) -> str:
        """Change current working directory. Returns new path."""
        node = PathResolver.resolve(path, self._cwd, self.root)
        if not isinstance(node, Directory):
            raise NotADirectoryError_(path)
        self._cwd = node
        return self.cwd_path

    # ── listing ───────────────────────────────────────────────────────────────
    def ls(self, path: str = ".") -> List[Union[File, Directory]]:
        """List directory contents. Defaults to cwd."""
        node = PathResolver.resolve(path, self._cwd, self.root)
        if isinstance(node, File):
            return [node]
        return node.list_children()

    # ── directory operations ──────────────────────────────────────────────────
    def mkdir(self, path: str) -> Directory:
        """Create a directory (one level; use mkdir -p style via mkdirp for nested)."""
        parent, name = PathResolver.resolve_parent(path, self._cwd, self.root)
        PathResolver.validate_name(name)
        if name in parent:
            raise AlreadyExistsError(path)
        new_dir = Directory(name, parent=parent)
        parent.add(new_dir)
        return new_dir

    def mkdirp(self, path: str) -> Directory:
        """Create directory and all missing intermediate directories."""
        parts = PathResolver.split(path)
        is_abs = PathResolver.is_absolute(path)
        node: Directory = self.root if is_abs else self._cwd
        for part in parts:
            if part in (".", ".."):
                continue
            PathResolver.validate_name(part)
            if part not in node:
                new_dir = Directory(part, parent=node)
                node.add(new_dir)
            child = node.get(part)
            if not isinstance(child, Directory):
                raise NotADirectoryError_(part)
            node = child
        return node

    def rmdir(self, path: str, recursive: bool = False) -> None:
        """Remove a directory. Must be empty unless recursive=True."""
        node = PathResolver.resolve(path, self._cwd, self.root)
        if not isinstance(node, Directory):
            raise NotADirectoryError_(path)
        if node is self.root:
            raise PermissionError_("Cannot remove root directory.")
        if node is self._cwd:
            raise PermissionError_("Cannot remove the current working directory.")
        if node.list_children() and not recursive:
            raise FSError(f"Directory not empty: '{path}'. Use 'rm -r' to remove recursively.")
        parent = node.parent
        parent.remove(node.name)

    # ── file operations ───────────────────────────────────────────────────────
    def touch(self, path: str) -> File:
        """Create an empty file (or update timestamps if it exists)."""
        parent, name = PathResolver.resolve_parent(path, self._cwd, self.root)
        PathResolver.validate_name(name)
        if name in parent:
            existing = parent.get(name)
            if isinstance(existing, File):
                existing.modified_date = datetime.now()
                return existing
            raise IsADirectoryError_(path)
        new_file = File(name)
        new_file._parent_dir = parent       # back-reference for abspath
        parent.add(new_file)
        return new_file

    def write_file(self, path: str, content: str, append: bool = False) -> File:
        """Write (or append) content to a file, creating it if necessary."""
        parent, name = PathResolver.resolve_parent(path, self._cwd, self.root)
        PathResolver.validate_name(name)
        if name not in parent:
            f = File(name)
            f._parent_dir = parent
            parent.add(f)
        node = parent.get(name)
        if not isinstance(node, File):
            raise IsADirectoryError_(path)
        node.write(content, append=append)
        return node

    def read_file(self, path: str) -> str:
        """Return the content of a file."""
        node = PathResolver.resolve(path, self._cwd, self.root)
        if isinstance(node, Directory):
            raise IsADirectoryError_(path)
        return node.read()

    def rm(self, path: str, recursive: bool = False) -> None:
        """Remove a file or (if recursive) a directory tree."""
        node = PathResolver.resolve(path, self._cwd, self.root)
        if isinstance(node, Directory):
            self.rmdir(path, recursive=recursive)
            return
        parent, name = PathResolver.resolve_parent(path, self._cwd, self.root)
        parent.remove(name)

    def cp(self, src_path: str, dst_path: str) -> None:
        """Copy a file to a new location."""
        src = PathResolver.resolve(src_path, self._cwd, self.root)
        if isinstance(src, Directory):
            raise FSError("cp does not support directories (use cp -r in a future release).")
        dst_parent, dst_name = PathResolver.resolve_parent(dst_path, self._cwd, self.root)
        PathResolver.validate_name(dst_name)
        new_file = File(dst_name, content=src.content)
        new_file._parent_dir = dst_parent
        dst_parent.add(new_file)

    def mv(self, src_path: str, dst_path: str) -> None:
        """Move / rename a file or directory."""
        src = PathResolver.resolve(src_path, self._cwd, self.root)

        # Determine destination
        try:
            dst = PathResolver.resolve(dst_path, self._cwd, self.root)
            # dst exists and is a directory → move src *into* dst
            if isinstance(dst, Directory):
                dst_parent = dst
                dst_name = src.name
            else:
                raise AlreadyExistsError(dst_path)
        except NotFoundError:
            dst_parent, dst_name = PathResolver.resolve_parent(dst_path, self._cwd, self.root)
            PathResolver.validate_name(dst_name)

        # Remove from old parent
        src_parent, src_name = PathResolver.resolve_parent(src_path, self._cwd, self.root)
        src_parent.remove(src_name)

        # Rename & attach
        src.name = dst_name
        if isinstance(src, Directory):
            src.parent = dst_parent
        else:
            src._parent_dir = dst_parent
        dst_parent.add(src)

    # ── stat & find ───────────────────────────────────────────────────────────
    def stat(self, path: str) -> Dict[str, str]:
        node = PathResolver.resolve(path, self._cwd, self.root)
        return node.stat()

    def find(self, path: str, name_pattern: str) -> List[str]:
        """
        Recursively search for files/directories whose name contains
        *name_pattern* (case-insensitive).
        """
        results: List[str] = []
        start = PathResolver.resolve(path, self._cwd, self.root)
        if not isinstance(start, Directory):
            raise NotADirectoryError_(path)
        self._find_recursive(start, name_pattern.lower(), results)
        return results

    def _find_recursive(self, node: Directory, pattern: str, acc: List[str]) -> None:
        for child in node.list_children():
            if pattern in child.name.lower():
                acc.append(PathResolver.abspath(child, self.root)
                           if isinstance(child, Directory)
                           else PathResolver.abspath(child, self.root))
            if isinstance(child, Directory):
                self._find_recursive(child, pattern, acc)

    def tree(self, path: str = "/") -> str:
        """Return an ASCII-art directory tree."""
        node = PathResolver.resolve(path, self._cwd, self.root)
        if not isinstance(node, Directory):
            raise NotADirectoryError_(path)
        lines: List[str] = []
        self._tree_recursive(node, "", lines, is_last=True)
        return "\n".join(lines)

    def _tree_recursive(self, node: Directory, prefix: str,
                        lines: List[str], is_last: bool) -> None:
        connector = "└── " if is_last else "├── "
        icon = "📁 " if isinstance(node, Directory) else "📄 "
        lines.append(prefix + connector + icon + node.name)
        if isinstance(node, Directory):
            children = node.list_children()
            for i, child in enumerate(children):
                is_child_last = (i == len(children) - 1)
                extension = "    " if is_last else "│   "
                if isinstance(child, Directory):
                    self._tree_recursive(child, prefix + extension,
                                         lines, is_child_last)
                else:
                    child_connector = "└── " if is_child_last else "├── "
                    lines.append(prefix + extension + child_connector + "📄 " + child.name)

    # ── disk usage ────────────────────────────────────────────────────────────
    def du(self, path: str = ".") -> int:
        """Return total disk usage (bytes) under *path*."""
        node = PathResolver.resolve(path, self._cwd, self.root)
        if isinstance(node, File):
            return node.size
        return node.total_size


# ═══════════════════════════════════════════════════════════════
# Shell (REPL)
# ═══════════════════════════════════════════════════════════════

class Shell:
    """
    Interactive shell that maps typed commands to FileSystem operations.

    Commands
    --------
    pwd                     – print working directory
    ls   [path]             – list contents
    cd   <path>             – change directory
    mkdir [-p] <path>       – create directory
    rmdir <path>            – remove empty directory
    touch <path>            – create/touch file
    write <path> <text…>    – overwrite file with text
    append <path> <text…>   – append text to file
    cat  <path>             – print file content
    rm   [-r] <path>        – remove file or directory
    cp   <src> <dst>        – copy file
    mv   <src> <dst>        – move / rename
    stat <path>             – show metadata
    find [path] <pattern>   – search by name pattern
    tree [path]             – ASCII directory tree
    du   [path]             – disk usage
    help                    – show help
    exit / quit             – leave the shell
    """

    BANNER = r"""
 ╔═══════════════════════════════════════════════════════╗
 ║        P y F S  –  File System Simulator  v1.0        ║
 ║                                                       ║
 ║  Type  help  for a list of commands.                  ║
 ║  Type  exit  to quit.                                 ║
 ╚═══════════════════════════════════════════════════════╝
"""

    def __init__(self) -> None:
        self.fs    = FileSystem()
        self._running = True
        self._seed_demo()

    # ── demo seed ─────────────────────────────────────────────────────────────
    def _seed_demo(self) -> None:
        """Pre-populate the filesystem with a sample structure."""
        self.fs.mkdirp("/home/alice/documents")
        self.fs.mkdirp("/home/alice/pictures")
        self.fs.mkdirp("/home/bob")
        self.fs.mkdirp("/etc")
        self.fs.mkdirp("/var/log")
        self.fs.write_file("/home/alice/documents/notes.txt",
                           "Remember to buy milk.\nCall dentist on Monday.\n")
        self.fs.write_file("/home/alice/documents/todo.md",
                           "# TODO\n- [ ] Finish project\n- [x] Write tests\n")
        self.fs.write_file("/etc/hosts",
                           "127.0.0.1  localhost\n::1        localhost\n")
        self.fs.write_file("/var/log/syslog.txt", "System started OK.\n")
        self.fs.cd("/home/alice")

    # ── REPL ──────────────────────────────────────────────────────────────────
    def run(self) -> None:
        print(self.BANNER)
        while self._running:
            try:
                prompt = f"\033[1;32m{self.fs.cwd_path}\033[0m $ "
                raw = input(prompt).strip()
            except (EOFError, KeyboardInterrupt):
                print("\nexit")
                break

            if not raw:
                continue

            try:
                tokens = shlex.split(raw)
            except ValueError as e:
                self._err(f"Parse error: {e}")
                continue

            self._dispatch(tokens)

    def _dispatch(self, tokens: List[str]) -> None:
        cmd, *args = tokens
        handlers = {
            "pwd":    self._cmd_pwd,
            "ls":     self._cmd_ls,
            "cd":     self._cmd_cd,
            "mkdir":  self._cmd_mkdir,
            "rmdir":  self._cmd_rmdir,
            "touch":  self._cmd_touch,
            "write":  self._cmd_write,
            "append": self._cmd_append,
            "cat":    self._cmd_cat,
            "rm":     self._cmd_rm,
            "cp":     self._cmd_cp,
            "mv":     self._cmd_mv,
            "stat":   self._cmd_stat,
            "find":   self._cmd_find,
            "tree":   self._cmd_tree,
            "du":     self._cmd_du,
            "help":   self._cmd_help,
            "exit":   self._cmd_exit,
            "quit":   self._cmd_exit,
            "clear":  lambda _: os.system("clear" if os.name != "nt" else "cls") or None,
        }
        handler = handlers.get(cmd.lower())
        if handler is None:
            self._err(f"Unknown command: '{cmd}'. Type 'help' for a list.")
        else:
            try:
                handler(args)
            except FSError as e:
                self._err(str(e))

    # ── command implementations ───────────────────────────────────────────────

    def _cmd_pwd(self, _args: List[str]) -> None:
        print(self.fs.cwd_path)

    def _cmd_ls(self, args: List[str]) -> None:
        path = args[0] if args else "."
        children = self.fs.ls(path)
        if not children:
            print("  (empty)")
            return
        # Sort: dirs first, then files, alphabetically within each group
        dirs  = sorted([c for c in children if isinstance(c, Directory)], key=lambda x: x.name)
        files = sorted([c for c in children if isinstance(c, File)],      key=lambda x: x.name)
        col_w = max((len(c.name) for c in children), default=10) + 4
        for d in dirs:
            print(f"  \033[1;34m{'📁 ' + d.name:<{col_w}}\033[0m  <DIR>")
        for f in files:
            size_str = f"{f.size}B"
            print(f"  \033[0;37m{'📄 ' + f.name:<{col_w}}\033[0m  {size_str:>8}  "
                  f"{f.modified_date.strftime('%Y-%m-%d %H:%M')}")

    def _cmd_cd(self, args: List[str]) -> None:
        if not args:
            self.fs.cd("/")
        else:
            new_path = self.fs.cd(args[0])
            # Prompt updates automatically via self.fs.cwd_path

    def _cmd_mkdir(self, args: List[str]) -> None:
        if not args:
            self._err("Usage: mkdir [-p] <path>")
            return
        if args[0] == "-p":
            if len(args) < 2:
                self._err("Usage: mkdir -p <path>")
                return
            self.fs.mkdirp(args[1])
            print(f"  Created: {args[1]}")
        else:
            self.fs.mkdir(args[0])
            print(f"  Created: {args[0]}")

    def _cmd_rmdir(self, args: List[str]) -> None:
        if not args:
            self._err("Usage: rmdir <path>")
            return
        self.fs.rmdir(args[0])
        print(f"  Removed directory: {args[0]}")

    def _cmd_touch(self, args: List[str]) -> None:
        if not args:
            self._err("Usage: touch <path>")
            return
        self.fs.touch(args[0])
        print(f"  Touched: {args[0]}")

    def _cmd_write(self, args: List[str]) -> None:
        if len(args) < 2:
            self._err("Usage: write <path> <content...>")
            return
        content = " ".join(args[1:])
        self.fs.write_file(args[0], content + "\n")
        print(f"  Written {len(content)} chars to '{args[0]}'.")

    def _cmd_append(self, args: List[str]) -> None:
        if len(args) < 2:
            self._err("Usage: append <path> <content...>")
            return
        content = " ".join(args[1:])
        self.fs.write_file(args[0], content + "\n", append=True)
        print(f"  Appended {len(content)} chars to '{args[0]}'.")

    def _cmd_cat(self, args: List[str]) -> None:
        if not args:
            self._err("Usage: cat <path>")
            return
        content = self.fs.read_file(args[0])
        if not content:
            print("  (empty file)")
        else:
            # Show with line numbers
            for i, line in enumerate(content.splitlines(), 1):
                print(f"  {i:>3} │ {line}")

    def _cmd_rm(self, args: List[str]) -> None:
        if not args:
            self._err("Usage: rm [-r] <path>")
            return
        recursive = False
        if args[0] == "-r":
            recursive = True
            args = args[1:]
        if not args:
            self._err("Usage: rm [-r] <path>")
            return
        self.fs.rm(args[0], recursive=recursive)
        print(f"  Removed: {args[0]}")

    def _cmd_cp(self, args: List[str]) -> None:
        if len(args) < 2:
            self._err("Usage: cp <src> <dst>")
            return
        self.fs.cp(args[0], args[1])
        print(f"  Copied '{args[0]}' → '{args[1]}'.")

    def _cmd_mv(self, args: List[str]) -> None:
        if len(args) < 2:
            self._err("Usage: mv <src> <dst>")
            return
        self.fs.mv(args[0], args[1])
        print(f"  Moved '{args[0]}' → '{args[1]}'.")

    def _cmd_stat(self, args: List[str]) -> None:
        if not args:
            self._err("Usage: stat <path>")
            return
        info = self.fs.stat(args[0])
        print()
        for k, v in info.items():
            print(f"  {k:<14} {v}")
        print()

    def _cmd_find(self, args: List[str]) -> None:
        if not args:
            self._err("Usage: find [path] <pattern>")
            return
        if len(args) == 1:
            path, pattern = "/", args[0]
        else:
            path, pattern = args[0], args[1]
        results = self.fs.find(path, pattern)
        if results:
            for r in results:
                print(f"  {r}")
        else:
            print(f"  No matches for '{pattern}'.")

    def _cmd_tree(self, args: List[str]) -> None:
        path = args[0] if args else self.fs.cwd_path
        print()
        print(self.fs.tree(path))
        print()

    def _cmd_du(self, args: List[str]) -> None:
        path = args[0] if args else "."
        size = self.fs.du(path)
        print(f"  {size} bytes  {path}")

    def _cmd_help(self, _args: List[str]) -> None:
        help_text = textwrap.dedent("""\

         ┌─────────────────────────────────────────────────────────────┐
         │                   Available Commands                        │
         ├──────────────────────┬──────────────────────────────────────┤
         │  pwd                 │ Print working directory              │
         │  ls [path]           │ List directory contents              │
         │  cd <path>           │ Change directory                     │
         │  mkdir [-p] <path>   │ Create directory (-p = recursive)    │
         │  rmdir <path>        │ Remove empty directory               │
         │  touch <path>        │ Create / timestamp a file            │
         │  write <path> <txt>  │ Write text to file (overwrites)      │
         │  append <path> <txt> │ Append text to file                  │
         │  cat <path>          │ Print file contents                  │
         │  rm [-r] <path>      │ Remove file or directory (-r=recurse)│
         │  cp <src> <dst>      │ Copy file                            │
         │  mv <src> <dst>      │ Move / rename file or directory      │
         │  stat <path>         │ Show file/directory metadata         │
         │  find [path] <pat>   │ Search by name pattern               │
         │  tree [path]         │ ASCII directory tree                 │
         │  du [path]           │ Disk usage (bytes)                   │
         │  clear               │ Clear screen                        │
         │  help                │ Show this help                       │
         │  exit / quit         │ Exit the shell                       │
         └──────────────────────┴──────────────────────────────────────┘

         Paths: use '/' for absolute, '.' for current, '..' for parent.
         Spaces in names: quote them, e.g.  mkdir "my folder"
        """)
        print(help_text)

    def _cmd_exit(self, _args: List[str]) -> None:
        print("  Goodbye! 👋")
        self._running = False

    # ── helpers ───────────────────────────────────────────────────────────────
    @staticmethod
    def _err(msg: str) -> None:
        print(f"\033[1;31m  Error: {msg}\033[0m")


# ═══════════════════════════════════════════════════════════════
# Entry point
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    Shell().run()