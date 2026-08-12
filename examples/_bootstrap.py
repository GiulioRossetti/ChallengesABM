"""Utilities shared by the example scripts."""

from __future__ import annotations

import sys
from pathlib import Path


def bootstrap_project_root() -> None:
    """Ensure the project root is importable when running a script directly."""

    project_root = Path(__file__).resolve().parents[1]
    project_root_str = str(project_root)
    if project_root_str not in sys.path:
        sys.path.insert(0, project_root_str)
