"""Internal fresh-process project planner used by pypagekit serve --watch."""

from __future__ import annotations

import json
import runpy
import sys
import traceback
from contextlib import redirect_stdout
from pathlib import Path
from typing import Any

from pypagekit import Assets, Site
from pypagekit.build import BuildPlan, BuildPlanner


def _serialize_plan(plan: BuildPlan) -> dict[str, Any]:
    pages = [
        {
            "route": entry.route.path,
            "target": entry.target.as_posix(),
            "content": entry.content,
        }
        for entry in plan.pages
    ]

    assets = []
    for entry in plan.assets:
        source = entry.asset.source
        if not source.is_absolute():
            source = (Path.cwd() / source).absolute()
        assets.append(
            {
                "source": str(source),
                "target": entry.target.as_posix(),
            }
        )

    return {
        "pages": pages,
        "assets": assets,
    }


def main(argv: list[str] | None = None) -> int:
    """Load one project entry point, build a plan, and emit JSON to stdout."""

    arguments = sys.argv[1:] if argv is None else argv
    if len(arguments) != 1:
        print("Expected exactly one project entry path.", file=sys.stderr)
        return 2

    entry = Path(arguments[0])

    try:
        with redirect_stdout(sys.stderr):
            namespace = runpy.run_path(
                str(entry),
                run_name="__pypagekit_watch_project__",
            )

        site = namespace.get("site")
        if not isinstance(site, Site):
            raise TypeError(
                "Watch entry must expose a module-level 'site' value containing a Site."
            )

        assets = namespace.get("assets")
        if assets is not None and not isinstance(assets, Assets):
            raise TypeError(
                "Watch entry module-level 'assets' value must be Assets or omitted."
            )

        plan = BuildPlanner().plan(site, assets)
        json.dump(_serialize_plan(plan), sys.stdout, ensure_ascii=False)
        return 0
    except Exception:
        traceback.print_exc(file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
