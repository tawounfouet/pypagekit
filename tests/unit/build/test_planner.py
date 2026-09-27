from pathlib import Path, PurePosixPath

import pytest

from pypagekit import Asset, Assets, Page, Paragraph, Route, Site
from pypagekit.build import BuildPlanner, route_output_target
from pypagekit.exceptions import (
    BuildRenderError,
    BuildTargetCollisionError,
    InvalidBuildContentError,
    InvalidBuildInputError,
    InvalidBuildTargetError,
    UnsafeUrlError,
)


def test_route_output_target_maps_root_to_index() -> None:
    assert route_output_target(Route("/", Page("Home"))) == PurePosixPath(
        "index.html"
    )


def test_route_output_target_maps_pretty_nested_paths() -> None:
    route = Route("/docs/getting-started", Page("Docs"))

    assert route_output_target(route) == PurePosixPath(
        "docs/getting-started/index.html"
    )


def test_build_planner_can_plan_empty_site() -> None:
    plan = BuildPlanner().plan(Site())

    assert plan.pages == ()
    assert plan.assets == ()


def test_build_planner_renders_pages_in_route_order() -> None:
    home = Route("/", Page("Home", [Paragraph("Welcome")]))
    about = Route("/about", Page("About", [Paragraph("About")]))
    plan = BuildPlanner().plan(Site([home, about]))

    assert plan.page_targets == (
        PurePosixPath("index.html"),
        PurePosixPath("about/index.html"),
    )
    assert plan.pages[0].route is home
    assert "<title>Home</title>" in plan.pages[0].content
    assert "<p>Welcome</p>" in plan.pages[0].content
    assert plan.pages[1].route is about
    assert "<title>About</title>" in plan.pages[1].content


def test_build_planner_adds_assets_after_pages() -> None:
    logo = Asset(Path("static/logo.png"), PurePosixPath("assets/logo.png"))
    plan = BuildPlanner().plan(
        Site([Route("/", Page("Home"))]),
        Assets([logo]),
    )

    assert plan.targets == (
        PurePosixPath("index.html"),
        PurePosixPath("assets/logo.png"),
    )
    assert plan.assets[0].asset is logo


class PrefixRenderer:
    def render(self, node: object) -> str:
        title = getattr(node, "title", "unknown")
        return f"rendered:{title}"


def test_build_planner_accepts_custom_renderer() -> None:
    renderer = PrefixRenderer()
    planner = BuildPlanner(renderer=renderer)  # type: ignore[arg-type]

    plan = planner.plan(Site([Route("/", Page("Home"))]))

    assert planner.renderer is renderer
    assert plan.pages[0].content == "rendered:Home"


class InvalidRenderer:
    render = None


def test_build_planner_rejects_renderer_without_callable_render() -> None:
    with pytest.raises(TypeError, match=r"callable render\(\)"):
        BuildPlanner(renderer=InvalidRenderer())  # type: ignore[arg-type]


class NonStringRenderer:
    def render(self, node: object) -> str:
        return 42  # type: ignore[return-value]


def test_build_planner_rejects_non_string_renderer_output() -> None:
    planner = BuildPlanner(renderer=NonStringRenderer())  # type: ignore[arg-type]

    with pytest.raises(InvalidBuildContentError, match="expected str"):
        planner.plan(Site([Route("/", Page("Home"))]))


class ExplodingRenderer:
    def render(self, node: object) -> str:
        raise AssertionError("renderer must not run before collision validation")


def test_build_planner_detects_collision_before_rendering() -> None:
    planner = BuildPlanner(renderer=ExplodingRenderer())  # type: ignore[arg-type]
    site = Site([Route("/", Page("Home"))])
    assets = Assets(
        [Asset(Path("source.txt"), PurePosixPath("index.html"))]
    )

    with pytest.raises(BuildTargetCollisionError):
        planner.plan(site, assets)


def test_build_planner_detects_page_page_file_directory_collision() -> None:
    site = Site(
        [
            Route("/docs", Page("Docs")),
            Route("/docs/index.html", Page("Nested")),
        ]
    )

    with pytest.raises(BuildTargetCollisionError):
        BuildPlanner().plan(site)


def test_build_planner_rejects_non_portable_route_output_target() -> None:
    site = Site([Route("/docs:api", Page("Docs"))])

    with pytest.raises(InvalidBuildTargetError):
        BuildPlanner().plan(site)


def test_build_planner_rejects_invalid_site_input() -> None:
    with pytest.raises(InvalidBuildInputError, match="Site"):
        BuildPlanner().plan(Page("Not a site"))  # type: ignore[arg-type]


def test_build_planner_rejects_invalid_assets_input() -> None:
    with pytest.raises(InvalidBuildInputError, match="Assets"):
        BuildPlanner().plan(Site(), [])  # type: ignore[arg-type]



class UnexpectedFailureRenderer:
    def render(self, node: object) -> str:
        del node
        raise RuntimeError("renderer exploded")


def test_build_planner_wraps_unexpected_renderer_failure_with_route_context() -> None:
    planner = BuildPlanner(renderer=UnexpectedFailureRenderer())  # type: ignore[arg-type]

    with pytest.raises(BuildRenderError, match="/docs") as exc_info:
        planner.plan(Site([Route("/docs", Page("Docs"))]))

    assert isinstance(exc_info.value.__cause__, RuntimeError)


class FrameworkFailureRenderer:
    def render(self, node: object) -> str:
        del node
        raise UnsafeUrlError("unsafe")


def test_build_planner_preserves_known_pypagekit_renderer_errors() -> None:
    planner = BuildPlanner(renderer=FrameworkFailureRenderer())  # type: ignore[arg-type]

    with pytest.raises(UnsafeUrlError, match="unsafe"):
        planner.plan(Site([Route("/", Page("Home"))]))
