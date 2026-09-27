"""Pure build planning from Site and Assets declarations."""

from pathlib import PurePosixPath

from pypagekit.domain import Assets, Route, Site
from pypagekit.exceptions import InvalidBuildContentError, InvalidBuildInputError
from pypagekit.rendering import HtmlRenderer, Renderer

from .model import (
    AssetBuildEntry,
    BuildPlan,
    PageBuildEntry,
    validate_build_targets,
)


def route_output_target(route: Route) -> PurePosixPath:
    """Map a logical route to its pretty static HTML output target."""

    if not isinstance(route, Route):
        raise TypeError("route_output_target() requires a Route object.")

    if route.is_root:
        return PurePosixPath("index.html")

    return PurePosixPath(*route.segments, "index.html")


class BuildPlanner:
    """Create deterministic in-memory build plans without filesystem I/O."""

    def __init__(self, *, renderer: Renderer | None = None) -> None:
        selected_renderer: Renderer = renderer or HtmlRenderer()
        render_method = getattr(selected_renderer, "render", None)
        if not callable(render_method):
            raise TypeError("Build planner renderer must provide a callable render() method.")

        self._renderer = selected_renderer

    @property
    def renderer(self) -> Renderer:
        """Renderer used to materialize page content inside the plan."""

        return self._renderer

    def plan(
        self,
        site: Site,
        assets: Assets | None = None,
    ) -> BuildPlan:
        """Create a complete deterministic build plan in memory."""

        if not isinstance(site, Site):
            raise InvalidBuildInputError("Build planner site must be a Site object.")
        if assets is not None and not isinstance(assets, Assets):
            raise InvalidBuildInputError(
                "Build planner assets must be an Assets object or None."
            )

        selected_assets = assets or Assets()
        page_targets = tuple(route_output_target(route) for route in site.routes)
        asset_targets = selected_assets.targets

        validate_build_targets(page_targets + asset_targets)

        pages: list[PageBuildEntry] = []
        for route, target in zip(site.routes, page_targets, strict=True):
            content = self._renderer.render(route.page)
            if not isinstance(content, str):
                raise InvalidBuildContentError(
                    f"Renderer returned {type(content).__name__} for route "
                    f"'{route.path}'; expected str."
                )
            pages.append(
                PageBuildEntry(
                    route=route,
                    target=target,
                    content=content,
                )
            )

        asset_entries = tuple(AssetBuildEntry(asset) for asset in selected_assets.items)

        return BuildPlan(
            pages=pages,
            assets=asset_entries,
        )
