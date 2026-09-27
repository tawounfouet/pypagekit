import warnings

import pytest

from pypagekit._deprecation import warn_deprecated


def test_warn_deprecated_emits_standard_warning_with_migration_context() -> None:
    with warnings.catch_warnings(record=True) as captured:
        warnings.simplefilter("always")

        warn_deprecated(
            "pypagekit.example.OldName",
            since="1.2.0",
            replacement="pypagekit.example.NewName",
            removal="2.0.0",
        )

    assert len(captured) == 1
    warning = captured[0]
    assert warning.category is DeprecationWarning
    assert str(warning.message) == (
        "pypagekit.example.OldName is deprecated since 1.2.0; "
        "use pypagekit.example.NewName instead. Removal: 2.0.0."
    )


@pytest.mark.parametrize(
    ("field", "kwargs"),
    [
        (
            "public_path",
            {
                "public_path": "",
                "since": "1.2.0",
                "replacement": "new",
                "removal": "2.0.0",
            },
        ),
        (
            "since",
            {
                "public_path": "old",
                "since": "",
                "replacement": "new",
                "removal": "2.0.0",
            },
        ),
        (
            "replacement",
            {
                "public_path": "old",
                "since": "1.2.0",
                "replacement": "",
                "removal": "2.0.0",
            },
        ),
        (
            "removal",
            {
                "public_path": "old",
                "since": "1.2.0",
                "replacement": "new",
                "removal": "",
            },
        ),
    ],
)
def test_warn_deprecated_rejects_missing_context(
    field: str,
    kwargs: dict[str, str],
) -> None:
    with pytest.raises(ValueError, match=field):
        warn_deprecated(**kwargs)


def test_warn_deprecated_rejects_invalid_stacklevel() -> None:
    with pytest.raises(ValueError, match="stacklevel"):
        warn_deprecated(
            "old",
            since="1.2.0",
            replacement="new",
            removal="2.0.0",
            stacklevel=0,
        )
