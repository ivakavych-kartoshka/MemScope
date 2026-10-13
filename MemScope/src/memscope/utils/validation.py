"""Small validation helpers used at trusted boundaries."""

from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any


def require_keys(value: Mapping[str, Any], keys: Sequence[str], name: str) -> None:
    missing = sorted(set(keys) - set(value))
    if missing:
        raise ValueError(f"{name} missing required keys: {', '.join(missing)}")


def require_existing_path(path: Path, kind: str = "file") -> Path:
    if kind == "file" and not path.is_file():
        raise FileNotFoundError(f"required file not found: {path}")
    if kind == "directory" and not path.is_dir():
        raise FileNotFoundError(f"required directory not found: {path}")
    return path
