from __future__ import annotations

import argparse
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from src.lib.observability import capture_scraper_exception, initialize_observability
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


def run_scraper(script: Path, scraper_args: list[str], dry_run: bool):
    command = [sys.executable, "-m", f"src.scrapers.{script.stem}"]
    if dry_run:
        command.append("--dry-run")
    command.extend(scraper_args)
    print(f"Running {script.stem} ...")
    return script.stem, command, subprocess.run(command, cwd=SCRAPER_DIR.parent.parent)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--only", help="Comma-separated list of scraper module stems to run.")
    parser.add_argument(
        "--workers",
        type=int,
        default=4,
        help="Maximum number of isolated scraper processes to run concurrently.",
    )
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
    if args.workers < 1:
        raise SystemExit("--workers must be at least 1.")

    initialize_observability("scraper")
    sync_scraper_registry_statuses(dry_run=args.dry_run)
    failures = []
    with ThreadPoolExecutor(max_workers=min(args.workers, len(scripts))) as executor:
        futures = {
            executor.submit(run_scraper, script, scraper_args, args.dry_run): script
            for script in scripts
        }
        for future in as_completed(futures):
            script = futures[future]
            try:
                scraper_name, command, result = future.result()
            except Exception as error:
                scraper_name = script.stem
                command = [sys.executable, "-m", f"src.scrapers.{scraper_name}"]
                result = None
                error_message = str(error)
            else:
                error_message = (
                    f"scraper process exited with code {result.returncode}"
                    if result.returncode != 0
                    else ""
                )

            if error_message:
                capture_scraper_exception(
                    scraper_name,
                    RuntimeError(error_message),
                    context={"command": " ".join(command)},
                )
                record_scraper_failure(
                    scraper_name,
                    error_message,
                    dry_run=args.dry_run,
                )
                failures.append(scraper_name)

    if failures:
        raise SystemExit(f"Scrapers failed: {', '.join(failures)}")


if __name__ == "__main__":
    main()
