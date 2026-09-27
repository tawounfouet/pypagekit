from pypagekit import Node, Page, Route, Site
from pypagekit.build import BuildPlanner
from pypagekit.extensions import ExtensionDescriptor, RendererExtension, RendererRegistry


class TitleRenderer:
    def render(self, node: Node) -> str:
        if isinstance(node, Page):
            return f"title:{node.title}"
        return f"node:{type(node).__name__}"


def test_registered_renderer_flows_through_existing_build_planner() -> None:
    registry = RendererRegistry(
        (
            RendererExtension(
                ExtensionDescriptor(
                    "acme.renderer.title",
                    "Title Renderer",
                    "1.0.0",
                ),
                TitleRenderer,
            ),
        )
    )
    renderer = registry.create("acme.renderer.title")
    site = Site((Route("/", Page("Home")),))

    plan = BuildPlanner(renderer=renderer).plan(site)

    assert plan.pages[0].content == "title:Home"
