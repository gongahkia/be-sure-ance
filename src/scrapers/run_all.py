from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from src.lib.scraper_health import record_scraper_failure, sync_scraper_registry_statuses
from src.scrapers.registry import EXPERIMENTAL_SCRAPERS, SUPPORTED_SCRAPERS

SCRAPER_DIR = Path(__file__).resolve().parent


def scraper_path(module_name: str) -> Path:
    return SCRAPER_DIR / f"{module_name}.py"


def list_scraper_scripts(include_experimental: bool = False):
    module_names = list(SUPPORTED_SCRAPERS)
    if include_experimental:
        module_names.extend(EXPERIMENTAL_SCRAPERS)
    return [
        scraper_path(module_name)
        for module_name in module_names
        if scraper_path(module_name).exists()
    ]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--only", help="Comma-separated list of scraper module stems to run.")
    parser.add_argument(
        "--include-experimental",
        action="store_true",
        help="Allow generic experimental scrapers to run when explicitly selected.",
    )
    parser.add_argument("--dry-run", action="store_true")
    args, scraper_args = parser.parse_known_args()

    only = {item.strip() for item in args.only.split(",")} if args.only else None
    selected_scripts = list_scraper_scripts(include_experimental=args.include_experimental)

    if only:
        known_scripts = list_scraper_scripts(include_experimental=True)
        known_names = {script.stem for script in known_scripts}
        unknown_names = sorted(only - known_names)
        if unknown_names:
            raise SystemExit(f"Unknown scrapers selected: {', '.join(unknown_names)}")

        experimental_names = sorted(only & set(EXPERIMENTAL_SCRAPERS))
        if experimental_names and not args.include_experimental:
            raise SystemExit(
                "Experimental scrapers require --include-experimental: "
                f"{', '.join(experimental_names)}"
            )

        selected_scripts = [script for script in selected_scripts if script.stem in only]

    scripts = selected_scripts

    if not scripts:
        raise SystemExit("No scrapers selected.")

    sync_scraper_registry_statuses(dry_run=args.dry_run)
    failures = []
    for script in scripts:
        command = [sys.executable, "-m", f"src.scrapers.{script.stem}"]
        if args.dry_run:
            command.append("--dry-run")
        command.extend(scraper_args)

        print(f"Running {script.stem} ...")
        result = subprocess.run(command, cwd=SCRAPER_DIR.parent.parent)
        if result.returncode != 0:
            record_scraper_failure(
                script.stem,
                f"scraper process exited with code {result.returncode}",
                dry_run=args.dry_run,
            )
            failures.append(script.stem)

    if failures:
        raise SystemExit(f"Scrapers failed: {', '.join(failures)}")


if __name__ == "__main__":
    main()
