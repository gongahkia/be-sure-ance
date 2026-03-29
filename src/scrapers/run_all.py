from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


SCRAPER_DIR = Path(__file__).resolve().parent
EXCLUDED_FILES = {"__init__.py", "_generic_domain.py", "run_all.py"}


def list_scraper_scripts():
    return sorted(
        path
        for path in SCRAPER_DIR.glob("*.py")
        if path.name not in EXCLUDED_FILES
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--only", help="Comma-separated list of scraper module stems to run.")
    parser.add_argument("--dry-run", action="store_true")
    args, scraper_args = parser.parse_known_args()

    only = {item.strip() for item in args.only.split(",")} if args.only else None
    scripts = [
        script for script in list_scraper_scripts() if only is None or script.stem in only
    ]

    if not scripts:
        raise SystemExit("No scrapers selected.")

    failures = []
    for script in scripts:
        command = [sys.executable, "-m", f"src.scrapers.{script.stem}"]
        if args.dry_run:
            command.append("--dry-run")
        command.extend(scraper_args)

        print(f"Running {script.stem} ...")
        result = subprocess.run(command, cwd=SCRAPER_DIR.parent.parent)
        if result.returncode != 0:
            failures.append(script.stem)

    if failures:
        raise SystemExit(f"Scrapers failed: {', '.join(failures)}")


if __name__ == "__main__":
    main()
