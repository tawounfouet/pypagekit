import hashlib
import tomllib
from pathlib import Path

from pypagekit import __version__
from pypagekit.extensions import PYPAGEKIT_EXTENSION_API_VERSION
from pypagekit.project import pypagekit_requirement

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
FROZEN_CONTRACT_PATH = REPOSITORY_ROOT / "API_CONTRACT_1_0.json"
FROZEN_CONTRACT_GIT_BLOB_SHA = "d417cf778b0a767c3c0016633ec0d7f3c69e191a"


def _load_toml(name: str) -> dict[str, object]:
    with (REPOSITORY_ROOT / name).open("rb") as stream:
        return tomllib.load(stream)


def _git_blob_sha(path: Path) -> str:
    data = path.read_bytes()
    payload = f"blob {len(data)}\0".encode() + data
    return hashlib.sha1(payload).hexdigest()


def test_release_version_is_exactly_1_0_0() -> None:
    assert __version__ == "1.0.0"


def test_lot_36_contract_file_is_byte_for_byte_unchanged() -> None:
    assert _git_blob_sha(FROZEN_CONTRACT_PATH) == FROZEN_CONTRACT_GIT_BLOB_SHA


def test_release_metadata_tracks_1_0_0() -> None:
    public_api = _load_toml("PUBLIC_API.toml")
    compatibility = _load_toml("COMPATIBILITY.toml")
    deprecations = _load_toml("DEPRECATIONS.toml")

    assert public_api["package_version"] == __version__
    assert compatibility["package_version"] == __version__
    assert deprecations["package_version"] == __version__


def test_release_keeps_frozen_compatibility_decisions() -> None:
    compatibility = _load_toml("COMPATIBILITY.toml")
    contract_freeze = compatibility["contract_freeze"]

    assert isinstance(contract_freeze, dict)
    assert contract_freeze["frozen"] is True
    assert contract_freeze["baseline"] == "API_CONTRACT_1_0.json"
    assert contract_freeze["target_release"] == "1.0.0"
    assert contract_freeze["release_candidate"] == "0.9.0rc1"
    assert contract_freeze["extension_api_version"] == "0.7"
    assert contract_freeze["python_cli_facade_frozen"] is False
    assert contract_freeze["shell_cli_frozen"] is True
    assert PYPAGEKIT_EXTENSION_API_VERSION == "0.7"


def test_release_has_no_active_public_deprecations() -> None:
    deprecations = _load_toml("DEPRECATIONS.toml")

    assert deprecations["deprecations"] == []


def test_generated_projects_target_the_1_0_minor_line() -> None:
    assert pypagekit_requirement() == "pypagekit>=1.0.0,<1.1"


def test_distribution_metadata_declares_stable_status() -> None:
    project = _load_toml("pyproject.toml")["project"]

    assert isinstance(project, dict)
    classifiers = project["classifiers"]
    assert isinstance(classifiers, list)
    assert "Development Status :: 5 - Production/Stable" in classifiers
    assert project["requires-python"] == ">=3.11"
