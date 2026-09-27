from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from pypagekit import (
    Asset,
    Assets,
    Component,
    Content,
    Page,
    Paragraph,
    Route,
    Site,
)
from pypagekit.build import BuildPlanner


@dataclass(frozen=True, slots=True)
class Greeting(Component):
    name: str

    def compose(self) -> Content:
        return Paragraph(f"Hello {self.name}")


def test_site_and_assets_produce_complete_in_memory_plan() -> None:
    home = Route("/", Page("Home", [Greeting("World")]))
    docs = Route("/docs", Page("Docs", [Paragraph("Documentation")]))
    logo = Asset(
        Path("static/logo.svg"),
        PurePosixPath("assets/logo.svg"),
    )

    plan = BuildPlanner().plan(
        Site([home, docs]),
        Assets([logo]),
    )

    assert plan.page_targets == (
        PurePosixPath("index.html"),
        PurePosixPath("docs/index.html"),
    )
    assert plan.asset_targets == (PurePosixPath("assets/logo.svg"),)
    assert "<p>Hello World</p>" in plan.pages[0].content
    assert "<p>Documentation</p>" in plan.pages[1].content
    assert plan.assets[0].asset.source == Path("static/logo.svg")


def test_build_plan_contains_no_output_root_or_write_operation() -> None:
    plan = BuildPlanner().plan(Site())

    assert not hasattr(plan, "output_root")
    assert not hasattr(plan, "write")
    assert not hasattr(plan, "execute")
