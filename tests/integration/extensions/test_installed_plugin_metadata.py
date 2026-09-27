import sys
from pathlib import Path

from pypagekit import Text
from pypagekit.extensions import EntryPointDiscovery, PluginLifecycle


def test_installed_entry_point_is_loaded_only_on_explicit_discovery(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module_name = "acme_pypagekit_metadata_plugin"
    module_path = tmp_path / f"{module_name}.py"
    module_path.write_text(
        """
from pypagekit.extensions import ExtensionDescriptor, RendererExtension


class MetadataRenderer:
    def render(self, node):
        return f"metadata:{type(node).__name__}"


def provide_renderer():
    return RendererExtension(
        ExtensionDescriptor(
            "acme.renderer.metadata",
            "Metadata Renderer",
            "1.0.0",
            api_version="0.7",
        ),
        MetadataRenderer,
    )
""".lstrip(),
        encoding="utf-8",
    )

    dist_info = tmp_path / "acme_pypagekit_metadata_plugin-1.0.0.dist-info"
    dist_info.mkdir()
    (dist_info / "METADATA").write_text(
        """
Metadata-Version: 2.1
Name: acme-pypagekit-metadata-plugin
Version: 1.0.0
""".lstrip(),
        encoding="utf-8",
    )
    (dist_info / "entry_points.txt").write_text(
        """
[pypagekit.renderers]
acme.renderer.metadata = acme_pypagekit_metadata_plugin:provide_renderer
""".lstrip(),
        encoding="utf-8",
    )

    monkeypatch.syspath_prepend(str(tmp_path))
    sys.modules.pop(module_name, None)

    discovery = EntryPointDiscovery()

    assert module_name not in sys.modules

    result = discovery.discover()

    assert module_name in sys.modules
    lifecycle = PluginLifecycle.from_discovery(result).qualify()

    assert lifecycle.is_conformant
    assert lifecycle.active_ids == ()

    active = lifecycle.activate()
    renderer = active.active_plugins.renderers.create("acme.renderer.metadata")

    assert active.active_ids == ("acme.renderer.metadata",)
    assert renderer.render(Text("hello")) == "metadata:Text"
