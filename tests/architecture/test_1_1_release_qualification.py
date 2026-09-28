import hashlib
import json
import re
import tomllib
from pathlib import Path

from pypagekit import __version__
from pypagekit.extensions import PYPAGEKIT_EXTENSION_API_VERSION
from pypagekit.project import pypagekit_requirement

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
CONTRACT_1_0_PATH = REPOSITORY_ROOT / "API_CONTRACT_1_0.json"
CONTRACT_1_1_PATH = REPOSITORY_ROOT / "API_CONTRACT_1_1.json"

CONTRACT_1_0_GIT_BLOB_SHA = "d417cf778b0a767c3c0016633ec0d7f3c69e191a"
CONTRACT_1_1_GIT_BLOB_SHA = "b9c752264ab623e570e70ea19433a60806e2df78"


def _load_toml(name: str) -> dict[str, object]:
    with (REPOSITORY_ROOT / name).open("rb") as stream:
        return tomllib.load(stream)


def _git_blob_sha(path: Path) -> str:
    data = path.read_bytes()
    payload = f"blob {len(data)}\0".encode() + data
    return hashlib.sha1(payload).hexdigest()


def test_release_version_is_exactly_1_1_0() -> None:
    assert __version__ == "1.1.0"


def test_frozen_1_0_contract_file_is_byte_for_byte_unchanged() -> None:
    assert _git_blob_sha(CONTRACT_1_0_PATH) == CONTRACT_1_0_GIT_BLOB_SHA


def test_frozen_1_1_contract_file_is_byte_for_byte_unchanged() -> None:
    assert _git_blob_sha(CONTRACT_1_1_PATH) == CONTRACT_1_1_GIT_BLOB_SHA


def test_release_metadata_tracks_exact_stable_version() -> None:
    public_api = _load_toml("PUBLIC_API.toml")
    compatibility = _load_toml("COMPATIBILITY.toml")
    deprecations = _load_toml("DEPRECATIONS.toml")

    assert public_api["package_version"] == "1.1.0"
    assert compatibility["package_version"] == "1.1.0"
    assert deprecations["package_version"] == "1.1.0"


def test_1_1_release_freeze_decisions_remain_recorded() -> None:
    compatibility = _load_toml("COMPATIBILITY.toml")
    freeze = compatibility["release_1_1_freeze"]

    assert isinstance(freeze, dict)
    assert freeze["frozen"] is True
    assert freeze["baseline"] == "API_CONTRACT_1_1.json"
    assert freeze["target_release"] == "1.1.0"
    assert freeze["release_candidate"] == "1.1.0rc1"
    assert freeze["compatibility_floor"] == "API_CONTRACT_1_0.json"
    assert freeze["extension_api_version"] == "0.7"
    assert freeze["python_cli_facade_frozen"] is False
    assert freeze["shell_cli_frozen"] is True


def test_1_1_contract_targets_stable_release() -> None:
    contract = json.loads(CONTRACT_1_1_PATH.read_text(encoding="utf-8"))

    assert contract["target_release"] == "1.1.0"
    assert contract["active_deprecations"] == []


def test_extension_api_line_remains_independent_from_package_release() -> None:
    assert PYPAGEKIT_EXTENSION_API_VERSION == "0.7"


def test_generated_projects_track_stable_1_1_release_line() -> None:
    match = re.match(r"^(?P<major>\d+)\.(?P<minor>\d+)", __version__)
    assert match is not None

    major = int(match.group("major"))
    minor = int(match.group("minor"))

    assert pypagekit_requirement() == "pypagekit>=1.1.0,<1.2"
    assert pypagekit_requirement() == f"pypagekit>={__version__},<{major}.{minor + 1}"


def test_distribution_metadata_remains_stable_and_python_3_11_plus() -> None:
    project = _load_toml("pyproject.toml")["project"]

    assert isinstance(project, dict)
    classifiers = project["classifiers"]
    assert isinstance(classifiers, list)
    assert "Development Status :: 5 - Production/Stable" in classifiers
    assert project["requires-python"] == ">=3.11"
