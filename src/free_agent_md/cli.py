from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from .settings import load_settings
from .update import load_catalog, render_existing, run_update
from .validate import validate_catalog


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="free-agent-md")
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="repository root")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("update", help="collect, validate, and atomically publish a new catalog")
    subparsers.add_parser("dry-run", help="run collection and validation without modifying files")
    subparsers.add_parser("render", help="regenerate README, archive, and repository indexes")
    subparsers.add_parser("validate", help="validate the catalog and local snapshots")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    root: Path = args.root.resolve()
    if args.command in {"update", "dry-run"}:
        catalog = run_update(
            root,
            token=os.getenv("GITHUB_TOKEN"),
            dry_run=args.command == "dry-run",
        )
        summary = catalog.stats.model_dump()
        summary["mode"] = args.command
        if args.command == "dry-run":
            summary["estimated_api_requests"] = summary["api_requests"]
        print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
        return 0
    if args.command == "render":
        catalog = render_existing(root)
        print(f"rendered {len(catalog.repositories)} active repositories")
        return 0

    settings = load_settings(root)
    repository = os.getenv("GITHUB_REPOSITORY")
    if repository:
        settings = settings.model_copy(update={"repository": repository})
    errors = validate_catalog(root, load_catalog(root), settings)
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    print("catalog is valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
