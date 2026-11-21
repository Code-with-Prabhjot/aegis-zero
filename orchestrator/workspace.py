"""
AEGIS-0 Confined Write Workspace

Approved write actions land here. Every target path is resolved inside a
single workspace root; absolute paths, `..` traversal, symlink escapes and
writes into `.git` are rejected. Writes are atomic (temp file + os.replace)
and every write can be undone byte-for-byte from the captured original.

By default the workspace is a sandbox directory (`.aegis-workspace/` at the
repository root) so demo approvals never overwrite the project's own source.
Point AEGIS_WORKSPACE_ROOT at a real checkout to apply changes there.
"""

import hashlib
import os
import re
import tempfile
from typing import Optional

ABSENT_DIGEST = "absent"


class WorkspaceError(ValueError):
    """Raised when a target path is not allowed inside the workspace."""


class Workspace:
    def __init__(self, root: str):
        self.root = os.path.realpath(os.path.abspath(root))

    @staticmethod
    def digest(content: Optional[str]) -> str:
        """SHA-256 of file content, or a sentinel for a file that doesn't exist."""
        if content is None:
            return ABSENT_DIGEST
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    def resolve(self, target: str) -> str:
        """Returns the absolute path for `target`, or raises WorkspaceError."""
        if not target or not target.strip() or "\x00" in target:
            raise WorkspaceError("Empty or invalid target path.")
        if os.path.isabs(target) or re.match(r"^[A-Za-z]:", target) or target.startswith(("\\\\", "//")):
            raise WorkspaceError("Absolute target paths are not allowed.")

        parts = re.split(r"[\\/]+", target)
        if any(p == ".git" for p in parts):
            raise WorkspaceError("Writes into .git are not allowed.")

        full = os.path.realpath(os.path.join(self.root, target))
        try:
            inside = os.path.commonpath([full, self.root]) == self.root
        except ValueError:  # different drives on Windows
            inside = False
        if not inside or full == self.root:
            raise WorkspaceError("Target path escapes the workspace.")
        return full

    def relative(self, target: str) -> str:
        return os.path.relpath(self.resolve(target), self.root).replace("\\", "/")

    def read(self, target: str) -> Optional[str]:
        path = self.resolve(target)
        if not os.path.isfile(path):
            return None
        with open(path, "r", encoding="utf-8", newline="") as fh:
            return fh.read()

    def write(self, target: str, content: str) -> str:
        """Atomically writes `content` to `target`; returns the absolute path."""
        path = self.resolve(target)
        directory = os.path.dirname(path)
        os.makedirs(directory, exist_ok=True)
        fd, tmp = tempfile.mkstemp(prefix=".aegis-", suffix=".tmp", dir=directory)
        try:
            with os.fdopen(fd, "w", encoding="utf-8", newline="") as fh:
                fh.write(content)
            os.replace(tmp, path)
        except BaseException:
            if os.path.exists(tmp):
                os.remove(tmp)
            raise
        return path

    def restore(self, target: str, original: Optional[str]) -> None:
        """Restores `target` to `original`; None means the file didn't exist."""
        if original is None:
            path = self.resolve(target)
            if os.path.isfile(path):
                os.remove(path)
        else:
            self.write(target, original)
