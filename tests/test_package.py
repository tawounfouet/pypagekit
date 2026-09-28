from pathlib import Path, PurePosixPath

from pypagekit import (
    Asset,
    Assets,
    Attributes,
    Component,
    ComponentRef,
    Container,
    Content,
    Fragment,
    Heading,
    Image,
    Layout,
    LayoutRegion,
    Link,
    Navigation,
    NavigationItem,
    Node,
    Page,
    Paragraph,
    Route,
    Site,
    Sitemap,
    SitemapEntry,
    Slot,
    SlotBindings,
    SlottedComponent,
    Text,
    __version__,
)
from pypagekit.build import (
    AssetBuildEntry,
    BuildFingerprint,
    BuildManifest,
    BuildManifestDiff,
    BuildManifestEntry,
    BuildPlan,
    BuildPlanner,
    BuildPlannerProtocol,
    FilesystemWriter,
    FilesystemWriteResult,
    IncrementalFilesystemWriteResult,
    IncrementalStaticSiteGenerationResult,
    PageBuildEntry,
    StaticSiteGenerationResult,
    StaticSiteGenerator,
    build_manifest,
    diff_build_manifests,
    route_output_target,
)
from pypagekit.components import Card, ComponentRegistry, ComponentRuntime, Hero, Section
from pypagekit.development import (
    DevelopmentServer,
    DevelopmentServerConfig,
    DevelopmentServerInfo,
    DevelopmentWatcher,
    DevelopmentWatchError,
    InvalidWatchRootError,
    WatchChange,
    WatchChangeBatch,
    WatchChangeKind,
    WatchPathKind,
    WatchSnapshot,
    WatchSnapshotEntry,
    WatchSnapshotError,
    diff_watch_snapshots,
)
from pypagekit.domain import Action, Media
from pypagekit.exceptions import (
    AssetSourceOutputConflictError,
    BuildError,
    BuildManifestError,
    BuildManifestSourceError,
    BuildRenderError,
    BuildTargetCollisionError,
    ComponentError,
    ComponentRegistryError,
    DuplicateAssetTargetError,
    DuplicateComponentContributionError,
    DuplicateComponentRegistrationError,
    DuplicateExtensionRegistrationError,
    ExistingOutputError,
    ExtensionError,
    ExtensionFactoryError,
    FilesystemOutputError,
    FilesystemRollbackError,
    FilesystemWriteError,
    IncrementalOutputDriftError,
    InvalidAssetError,
    InvalidAssetSourceForOutputError,
    InvalidAttributeError,
    InvalidBuildContentError,
    InvalidBuildFingerprintError,
    InvalidBuildInputError,
    InvalidBuildManifestError,
    InvalidBuildPlanError,
    InvalidBuildPlannerExtensionError,
    InvalidBuildTargetError,
    InvalidComponentNameError,
    InvalidExtensionDescriptorError,
    InvalidExtensionIdError,
    InvalidLayoutError,
    InvalidNavigationError,
    InvalidOutputRootError,
    InvalidPluginEntryPointError,
    InvalidPluginLifecycleTransitionError,
    InvalidRegisteredComponentError,
    InvalidRendererExtensionError,
    InvalidRouteError,
    InvalidSiteError,
    InvalidSlotError,
    MissingComponentRegistryError,
    OutputPathConflictError,
    OutputSymlinkError,
    PluginActivationError,
    PluginDiscoveryError,
    PluginEntryPointLoadError,
    PluginLifecycleError,
    PluginProviderError,
    RenderingError,
    SecurityError,
    SerializationError,
    UnknownComponentError,
    UnknownExtensionError,
    UnknownPluginError,
    UnresolvedSlotError,
    UnsafeUrlError,
    UnsupportedNodeError,
)
from pypagekit.extensions import (
    BUILD_PLANNER_ENTRY_POINT_GROUP,
    BUILD_PLANNER_EXTENSION_ID,
    BUILTIN_COMPONENTS_EXTENSION_ID,
    COMPONENT_ENTRY_POINT_GROUP,
    HTML_RENDERER_EXTENSION_ID,
    PYPAGEKIT_EXTENSION_API_VERSION,
    RENDERER_ENTRY_POINT_GROUP,
    BuildPlannerExtension,
    BuildPlannerRegistry,
    ComponentExtension,
    ComponentExtensionRegistry,
    EntryPointDiscovery,
    ExtensionDescriptor,
    PluginDiscoveryResult,
    PluginKind,
    PluginLifecycle,
    PluginState,
    PluginStatus,
    RendererExtension,
    RendererRegistry,
    default_build_planner_registry,
    default_component_extension_registry,
    default_renderer_registry,
)
from pypagekit.project import (
    ProjectFile,
    ProjectPlan,
    ProjectScaffolder,
    ProjectScaffoldRollbackError,
    ProjectScaffoldWriteError,
)
from pypagekit.rendering import HtmlRenderer, Renderer


def test_package_imports() -> None:
    assert __version__
    asset = Asset(Path("logo.png"), PurePosixPath("assets/logo.png"))
    assert isinstance(asset, Asset)
    assert isinstance(Assets([asset]), Assets)
    assert isinstance(BuildPlan(), BuildPlan)
    fingerprint = BuildFingerprint.from_bytes(b"")
    manifest_entry = BuildManifestEntry(
        PurePosixPath("index.html"),
        "page",
        fingerprint,
    )
    manifest = BuildManifest([manifest_entry])
    assert isinstance(manifest, BuildManifest)
    empty_manifest = build_manifest(BuildPlan())
    assert isinstance(empty_manifest, BuildManifest)
    diff = diff_build_manifests(empty_manifest, empty_manifest)
    assert isinstance(diff, BuildManifestDiff)
    incremental_write_result = IncrementalFilesystemWriteResult(
        Path("dist"),
        empty_manifest,
        diff,
        (),
        (),
        (),
        (),
    )
    assert isinstance(incremental_write_result, IncrementalFilesystemWriteResult)
    assert isinstance(
        IncrementalStaticSiteGenerationResult(
            BuildPlan(),
            incremental_write_result,
        ),
        IncrementalStaticSiteGenerationResult,
    )
    planner: BuildPlannerProtocol = BuildPlanner()
    assert isinstance(planner, BuildPlanner)
    assert isinstance(FilesystemWriter(), FilesystemWriter)
    assert isinstance(StaticSiteGenerator(), StaticSiteGenerator)
    project_file = ProjectFile(PurePosixPath("site.py"), "print('hello')\n")
    assert isinstance(project_file, ProjectFile)
    assert isinstance(
        ProjectPlan(Path("demo"), "demo", [project_file]),
        ProjectPlan,
    )
    assert isinstance(ProjectScaffolder(), ProjectScaffolder)
    development_root = Path(".")
    assert isinstance(
        DevelopmentServerConfig(development_root),
        DevelopmentServerConfig,
    )
    assert isinstance(
        DevelopmentServerInfo(development_root, "127.0.0.1", 8000),
        DevelopmentServerInfo,
    )
    assert isinstance(DevelopmentServer(), DevelopmentServer)
    watch_root = Path(".").resolve()
    watcher = DevelopmentWatcher(watch_root)
    empty_watch = WatchSnapshot(watch_root)
    assert isinstance(watcher, DevelopmentWatcher)
    assert isinstance(empty_watch, WatchSnapshot)
    watch_entry = WatchSnapshotEntry(
        PurePosixPath("site.py"),
        WatchPathKind.FILE,
        "0" * 64,
    )
    changed_watch = WatchSnapshot(watch_root, [watch_entry])
    watch_batch = diff_watch_snapshots(empty_watch, changed_watch)
    assert isinstance(watch_batch, WatchChangeBatch)
    assert isinstance(watch_batch.changes[0], WatchChange)
    assert watch_batch.changes[0].kind is WatchChangeKind.CREATED
    assert issubclass(InvalidWatchRootError, DevelopmentWatchError)
    assert issubclass(WatchSnapshotError, DevelopmentWatchError)
    write_result = FilesystemWriteResult(Path("dist"), (), ())
    assert isinstance(write_result, FilesystemWriteResult)
    assert isinstance(
        StaticSiteGenerationResult(BuildPlan(), write_result),
        StaticSiteGenerationResult,
    )
    assert isinstance(AssetBuildEntry(asset), AssetBuildEntry)
    assert issubclass(Content, Node)
    assert issubclass(Page, Node)
    root_route = Route("/", Page("Root"))
    page_entry = PageBuildEntry(root_route, PurePosixPath("index.html"), "<html></html>")
    assert isinstance(page_entry, PageBuildEntry)
    assert route_output_target(root_route) == PurePosixPath("index.html")
    assert isinstance(root_route, Route)
    assert isinstance(Site([root_route]), Site)
    assert isinstance(Sitemap([root_route]), Sitemap)
    assert isinstance(SitemapEntry(root_route), SitemapEntry)
    assert issubclass(Component, Content)
    assert issubclass(ComponentRef, Content)
    assert issubclass(Layout, Component)
    assert issubclass(LayoutRegion, Content)
    assert isinstance(Navigation(), Navigation)
    assert isinstance(NavigationItem("Root", Route("/", Page("Root"))), NavigationItem)
    assert issubclass(Fragment, Content)
    assert issubclass(Slot, Content)
    assert issubclass(SlottedComponent, Component)
    assert isinstance(SlotBindings(), SlotBindings)
    assert issubclass(Text, Content)
    assert issubclass(Heading, Content)
    assert issubclass(Paragraph, Content)
    assert issubclass(Container, Content)
    assert issubclass(Action, Content)
    assert issubclass(Link, Action)
    assert issubclass(Media, Content)
    assert issubclass(Image, Media)
    assert isinstance(Attributes(), Attributes)
    assert isinstance(ComponentRuntime(), ComponentRuntime)
    assert isinstance(ComponentRegistry(), ComponentRegistry)
    descriptor = ExtensionDescriptor("acme.renderer.demo", "Demo Renderer", "1.0.0")
    extension = RendererExtension(descriptor, HtmlRenderer)
    assert isinstance(RendererRegistry((extension,)), RendererRegistry)
    assert default_renderer_registry().ids == (HTML_RENDERER_EXTENSION_ID,)
    build_extension = BuildPlannerExtension(
        ExtensionDescriptor("acme.build.demo", "Demo Planner", "1.0.0"),
        BuildPlanner,
    )
    assert isinstance(BuildPlannerRegistry((build_extension,)), BuildPlannerRegistry)
    assert default_build_planner_registry().ids == (BUILD_PLANNER_EXTENSION_ID,)
    component_extension = ComponentExtension(
        ExtensionDescriptor("acme.components.demo", "Demo Components", "1.0.0"),
        {"section": Section},
    )
    assert isinstance(
        ComponentExtensionRegistry((component_extension,)),
        ComponentExtensionRegistry,
    )
    assert default_component_extension_registry().ids == (BUILTIN_COMPONENTS_EXTENSION_ID,)
    assert BUILD_PLANNER_ENTRY_POINT_GROUP == "pypagekit.build_planners"
    assert COMPONENT_ENTRY_POINT_GROUP == "pypagekit.components"
    assert RENDERER_ENTRY_POINT_GROUP == "pypagekit.renderers"
    discovery_result = EntryPointDiscovery(source=lambda group: ()).discover()
    assert isinstance(discovery_result, PluginDiscoveryResult)
    lifecycle = PluginLifecycle.from_discovery(discovery_result).qualify().activate()
    assert isinstance(lifecycle, PluginLifecycle)
    assert PYPAGEKIT_EXTENSION_API_VERSION == "0.7"
    assert PluginKind.RENDERER.value == "renderer"
    assert PluginState.ACTIVE.value == "active"
    assert isinstance(
        PluginStatus(
            "acme.renderer.demo",
            PluginKind.RENDERER,
            PluginState.DISCOVERED,
        ),
        PluginStatus,
    )
    assert issubclass(Section, Component)
    assert issubclass(Card, Component)
    assert issubclass(Hero, Component)
    assert issubclass(DuplicateAssetTargetError, InvalidAssetError)
    assert issubclass(DuplicateComponentContributionError, ExtensionError)
    assert issubclass(AssetSourceOutputConflictError, FilesystemOutputError)
    assert issubclass(BuildManifestError, BuildError)
    assert issubclass(BuildManifestSourceError, BuildManifestError)
    assert issubclass(BuildRenderError, BuildError)
    assert issubclass(BuildTargetCollisionError, BuildError)
    assert issubclass(ExistingOutputError, FilesystemOutputError)
    assert issubclass(FilesystemOutputError, BuildError)
    assert issubclass(FilesystemRollbackError, FilesystemWriteError)
    assert issubclass(FilesystemWriteError, FilesystemOutputError)
    assert issubclass(InvalidBuildContentError, BuildError)
    assert issubclass(InvalidBuildFingerprintError, BuildManifestError)
    assert issubclass(InvalidBuildManifestError, BuildManifestError)
    assert issubclass(InvalidBuildPlannerExtensionError, ExtensionError)
    assert issubclass(InvalidBuildInputError, BuildError)
    assert issubclass(InvalidBuildPlanError, BuildError)
    assert issubclass(InvalidAssetSourceForOutputError, FilesystemOutputError)
    assert issubclass(InvalidBuildTargetError, BuildError)
    assert issubclass(IncrementalOutputDriftError, FilesystemOutputError)
    assert issubclass(InvalidOutputRootError, FilesystemOutputError)
    assert issubclass(OutputPathConflictError, FilesystemOutputError)
    assert issubclass(OutputSymlinkError, FilesystemOutputError)
    assert issubclass(ComponentError, Exception)
    assert issubclass(ComponentRegistryError, ComponentError)
    assert issubclass(DuplicateComponentRegistrationError, ComponentRegistryError)
    assert issubclass(ExtensionError, Exception)
    assert issubclass(ExtensionFactoryError, ExtensionError)
    assert issubclass(DuplicateExtensionRegistrationError, ExtensionError)
    assert issubclass(InvalidExtensionDescriptorError, ExtensionError)
    assert issubclass(InvalidExtensionIdError, InvalidExtensionDescriptorError)
    assert issubclass(InvalidRendererExtensionError, ExtensionError)
    assert issubclass(PluginDiscoveryError, ExtensionError)
    assert issubclass(InvalidPluginEntryPointError, PluginDiscoveryError)
    assert issubclass(InvalidPluginLifecycleTransitionError, PluginLifecycleError)
    assert issubclass(PluginActivationError, PluginLifecycleError)
    assert issubclass(PluginEntryPointLoadError, PluginDiscoveryError)
    assert issubclass(PluginLifecycleError, ExtensionError)
    assert issubclass(PluginProviderError, PluginDiscoveryError)
    assert issubclass(UnknownPluginError, PluginActivationError)
    assert issubclass(UnknownExtensionError, ExtensionError)
    assert issubclass(InvalidComponentNameError, ComponentRegistryError)
    assert issubclass(InvalidRegisteredComponentError, ComponentRegistryError)
    assert issubclass(InvalidRouteError, Exception)
    assert issubclass(InvalidSiteError, Exception)
    assert issubclass(MissingComponentRegistryError, ComponentRegistryError)
    assert issubclass(UnknownComponentError, ComponentRegistryError)
    assert issubclass(InvalidLayoutError, Exception)
    assert issubclass(InvalidNavigationError, Exception)
    assert issubclass(InvalidSlotError, Exception)
    assert issubclass(UnresolvedSlotError, InvalidSlotError)
    assert issubclass(SerializationError, RenderingError)
    assert issubclass(SecurityError, RenderingError)
    assert issubclass(UnsafeUrlError, SecurityError)
    assert issubclass(InvalidAttributeError, Exception)
    assert issubclass(UnsupportedNodeError, RenderingError)
    assert issubclass(ProjectScaffoldRollbackError, ProjectScaffoldWriteError)

    renderer: Renderer = HtmlRenderer()
    assert isinstance(renderer, HtmlRenderer)


def test_current_version() -> None:
    assert __version__ == "1.1.0b1"
