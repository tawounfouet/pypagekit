"""Internal helpers for consistent public deprecation warnings."""

import warnings


def warn_deprecated(
    public_path: str,
    *,
    since: str,
    replacement: str,
    removal: str,
    stacklevel: int = 2,
) -> None:
    """Emit a deterministic DeprecationWarning for a public compatibility alias."""

    for label, value in (
        ("public_path", public_path),
        ("since", since),
        ("replacement", replacement),
        ("removal", removal),
    ):
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"Deprecation {label} must be a non-empty string.")

    if not isinstance(stacklevel, int) or stacklevel < 1:
        raise ValueError("Deprecation stacklevel must be a positive integer.")

    warnings.warn(
        (
            f"{public_path} is deprecated since {since}; "
            f"use {replacement} instead. Removal: {removal}."
        ),
        DeprecationWarning,
        stacklevel=stacklevel,
    )


__all__ = ["warn_deprecated"]
