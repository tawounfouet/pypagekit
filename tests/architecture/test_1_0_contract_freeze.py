import json
from pathlib import Path

import pytest

from tools.api_contract_snapshot import build_snapshot, render_snapshot

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = REPOSITORY_ROOT / "API_CONTRACT_1_0.json"


def test_frozen_1_0_contract_matches_runtime_exactly() -> None:
    expected = CONTRACT_PATH.read_text(encoding="utf-8")
    actual = render_snapshot()

    if actual != expected:
        pytest.fail(
            "1.0 contract baseline mismatch.\n"
            "CONTRACT_SNAPSHOT_BEGIN\n"
            f"{actual}"
            "CONTRACT_SNAPSHOT_END"
        )


def test_contract_snapshot_is_canonical_json() -> None:
    content = CONTRACT_PATH.read_text(encoding="utf-8")
    parsed = json.loads(content)

    assert content == json.dumps(
        parsed,
        indent=2,
        sort_keys=True,
        ensure_ascii=False,
    ) + "\n"


def test_contract_snapshot_targets_1_0() -> None:
    snapshot = build_snapshot()

    assert snapshot["schema_version"] == 1
    assert snapshot["target_release"] == "1.0.0"
    assert snapshot["active_deprecations"] == []


def test_python_cli_facade_remains_explicitly_provisional() -> None:
    snapshot = build_snapshot()
    provisional = snapshot["provisional_facades"]

    assert provisional == {
        "pypagekit.cli": {
            "exports": ["app", "main"],
            "frozen": False,
        }
    }
