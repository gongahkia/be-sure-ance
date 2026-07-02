from __future__ import annotations

import re
import sys
from collections import defaultdict
from datetime import datetime, timezone

from src.lib.local_data_store import LocalDataClient, default_data_dir
from src.scrapers.registry import EXPERIMENTAL_SCRAPERS, SUPPORTED_SCRAPERS

SECRET_PATTERNS = (
    re.compile(r"Bearer\s+[A-Za-z0-9._-]+", re.IGNORECASE),
    re.compile(r"eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+"),
)
MAX_ERROR_LENGTH = 500


def dry_run_enabled(args=None):
    return "--dry-run" in (args if args is not None else sys.argv[1:])


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def display_name(carrier_key):
    if carrier_key == "iii":
        return "India International Insurance"
    return str(carrier_key).replace("_", " ").title()


def support_status_for(carrier_key):
    return "supported" if carrier_key in SUPPORTED_SCRAPERS else "unsupported"


def sanitized_error(value):
    text = str(value or "")
    for pattern in SECRET_PATTERNS:
        text = pattern.sub("[redacted]", text)
    return text[:MAX_ERROR_LENGTH]


def health_client():
    return LocalDataClient(default_data_dir())


def upsert_health_rows(rows, dry_run=None):
    should_skip = dry_run if dry_run is not None else dry_run_enabled()
    if should_skip:
        return None
    if not rows:
        return None
    client = health_client()
    try:
        return client.table("scraper_health").upsert(rows, on_conflict="carrier_key").execute()
    except Exception as exc:
        print(f"[scraper-health] status persistence skipped: {exc}")
        return None


def sync_scraper_registry_statuses(dry_run=None):
    timestamp = utc_now()
    supported_rows = [
        {
            "carrier_key": carrier_key,
            "display_name": display_name(carrier_key),
            "support_status": "supported",
            "updated_at": timestamp,
        }
        for carrier_key in SUPPORTED_SCRAPERS
    ]
    unsupported_rows = [
        {
            "carrier_key": carrier_key,
            "display_name": display_name(carrier_key),
            "support_status": "unsupported",
            "row_count": 0,
            "validation_status": "unsupported",
            "updated_at": timestamp,
        }
        for carrier_key in EXPERIMENTAL_SCRAPERS
    ]
    return upsert_health_rows([*supported_rows, *unsupported_rows], dry_run=dry_run)


def record_scraper_success(carrier_key, row_count, dry_run=None):
    timestamp = utc_now()
    return upsert_health_rows(
        [
            {
                "carrier_key": carrier_key,
                "display_name": display_name(carrier_key),
                "support_status": support_status_for(carrier_key),
                "last_success_at": timestamp,
                "last_run_at": timestamp,
                "last_error": None,
                "row_count": int(row_count or 0),
                "updated_at": timestamp,
            }
        ],
        dry_run=dry_run,
    )


def record_scraper_failure(carrier_key, error, dry_run=None):
    timestamp = utc_now()
    return upsert_health_rows(
        [
            {
                "carrier_key": carrier_key,
                "display_name": display_name(carrier_key),
                "support_status": support_status_for(carrier_key),
                "last_failure_at": timestamp,
                "last_run_at": timestamp,
                "last_error": sanitized_error(error),
                "updated_at": timestamp,
            }
        ],
        dry_run=dry_run,
    )


def record_validation_report(report, dry_run=None):
    timestamp = report.get("generated_at") or utc_now()
    grouped_results = defaultdict(list)
    for result in report.get("results", []):
        grouped_results[result.get("insurer")].append(result)

    rows = []
    for carrier_key, results in grouped_results.items():
        if not carrier_key:
            continue
        summary = summarize_validation_results(results)
        rows.append(
            {
                "carrier_key": carrier_key,
                "display_name": display_name(carrier_key),
                "support_status": support_status_for(carrier_key),
                "validation_status": summary["status"],
                "validation_checked_at": timestamp,
                "validation_summary": summary,
                "updated_at": timestamp,
            }
        )

    sync_scraper_registry_statuses(dry_run=dry_run)
    return upsert_health_rows(rows, dry_run=dry_run)


def summarize_validation_results(results):
    statuses = [result.get("status", "error") for result in results]
    if "error" in statuses:
        status = "error"
    elif "failed" in statuses:
        status = "failed"
    elif "no_baseline" in statuses:
        status = "no_baseline"
    else:
        status = "passed"

    notes = []
    for result in results:
        notes.extend(result.get("failures", []) or result.get("errors", []) or [])

    return {
        "status": status,
        "total_targets": len(results),
        "passed": statuses.count("passed"),
        "failed": statuses.count("failed"),
        "errors": statuses.count("error"),
        "no_baseline": statuses.count("no_baseline"),
        "notes": [sanitized_error(note) for note in notes[:5]],
    }
