"""Stable CLI process exit codes."""

from typing import Final

SUCCESS: Final[int] = 0
EXECUTION_ERROR: Final[int] = 1
USAGE_ERROR: Final[int] = 2

__all__ = [
    "EXECUTION_ERROR",
    "SUCCESS",
    "USAGE_ERROR",
]
