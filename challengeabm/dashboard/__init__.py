"""Interactive dashboard package for ChallengeABM."""

from __future__ import annotations


def run_dashboard(*args, **kwargs):
    from .server import run_dashboard as _run_dashboard

    return _run_dashboard(*args, **kwargs)


def main(*args, **kwargs):
    from .server import main as _main

    return _main(*args, **kwargs)


__all__ = ["main", "run_dashboard"]
