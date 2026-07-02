from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from src.backend.demo_data import demo_tables
from src.lib.local_data_store import LocalDataClient, default_data_dir

APP_TABLES = (
    "plans",
    "plan_comparison_facts",
    "plan_facts",
    "specialist_resources",
    "claim_turnaround_metrics",
    "mas_regulatory_events",
    "brochure_change_alerts",
    "carrier_canonical_names",
    "scraper_health",
)
DEFAULT_OUTPUT_PATH = Path("src/be-sure-ance-app/public/data/app-data.json")


def generated_at() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def load_local_tables(data_dir: Path | str | None = None) -> dict[str, list[dict]]:
    client = LocalDataClient(data_dir or default_data_dir())
    return {table: client.read_table(table) for table in APP_TABLES}


def build_app_data_payload(tables: dict[str, list[dict]], generated_at_value: str | None = None):
    payload = {
        "generated_at": generated_at_value or generated_at(),
        "tables": {table: list(tables.get(table, [])) for table in APP_TABLES},
    }
    for table in APP_TABLES:
        payload[table] = payload["tables"][table]
    return payload


def write_app_data(
    output_path: Path,
    tables: dict[str, list[dict]],
    generated_at_value: str | None = None,
) -> int:
    payload = build_app_data_payload(tables, generated_at_value=generated_at_value)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n")
    return sum(len(payload["tables"][table]) for table in APP_TABLES)


def run_scraper_pipeline(data_dir: Path):
    env = {**os.environ, "BE_SURE_ANCE_DATA_DIR": str(data_dir)}
    commands = [
        [sys.executable, "-m", "src.scrapers.run_all"],
        [sys.executable, "-m", "src.scrapers.moh_institutions"],
        [sys.executable, "-m", "src.scrapers.lia_claim_turnaround"],
        [sys.executable, "-m", "src.scrapers.mas_regulatory"],
        [sys.executable, "-m", "src.scrapers.carrier_canonicalization"],
        [sys.executable, "-m", "src.scrapers.brochure_facts"],
        [sys.executable, "-m", "src.scrapers.panel_resources"],
        [sys.executable, "-m", "src.scrapers.comparison_facts"],
    ]
    for command in commands:
        subprocess.run(command, check=True, env=env)


def non_empty_tables(tables: dict[str, list[dict]]) -> bool:
    return any(tables.get(table) for table in ("plans", "plan_facts", "plan_comparison_facts"))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--data-dir", type=Path, default=default_data_dir())
    parser.add_argument("--demo", action="store_true", help="Export seeded demo data only.")
    parser.add_argument("--run-scrapers", action="store_true", help="Run scrapers before export.")
    parser.add_argument(
        "--fallback-demo",
        action="store_true",
        help="Use seeded demo rows if scraper/local rows are unavailable or fail.",
    )
    args = parser.parse_args()

    tables = {}
    if args.demo:
        tables = demo_tables()
    else:
        try:
            if args.run_scrapers:
                LocalDataClient(args.data_dir).reset()
                run_scraper_pipeline(args.data_dir)
            tables = load_local_tables(args.data_dir)
        except Exception as error:
            if not args.fallback_demo:
                raise
            print(f"static_app_data: scraper pipeline failed; using demo fallback: {error}")
            tables = demo_tables()

    if args.fallback_demo and not non_empty_tables(tables):
        print("static_app_data: no local rows found; using demo fallback")
        tables = demo_tables()

    row_count = write_app_data(args.output, tables)
    print(
        json.dumps(
            {
                "app_data_path": str(args.output),
                "app_data_row_count": row_count,
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
