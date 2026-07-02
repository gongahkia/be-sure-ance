from __future__ import annotations

import argparse
import csv
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from supabase import create_client

SNAPSHOT_FIELDS = (
    "snapshot_date",
    "insurer",
    "plan_slug",
    "plan_name",
    "canonical_carrier_name",
    "carrier_mismatch_flags",
    "field_name",
    "field_status",
    "field_value_json",
    "source_url",
    "source_type",
    "scraped_at",
    "last_verified_at",
    "limitations",
)
DEFAULT_LIMITATIONS = (
    "Open dataset for qualitative research only; not advice, ranking, quote, or policy transaction."
)


def generated_snapshot_date(value: datetime | None = None) -> str:
    current = value or datetime.now(timezone.utc)
    return current.astimezone(timezone.utc).date().isoformat()


def default_snapshot_path(snapshot_date: str) -> Path:
    return Path("data") / f"be-sure-ance-snapshot-{snapshot_date}.csv"


def export_open_dataset(
    output_path: Path, snapshot_date: str, tables: dict[str, list[dict]]
) -> int:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    rows = build_snapshot_rows(tables, snapshot_date)
    with output_path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=SNAPSHOT_FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    return len(rows)


def build_snapshot_rows(tables: dict[str, list[dict]], snapshot_date: str) -> list[dict]:
    plans = {
        (plan.get("insurer"), plan.get("plan_slug")): plan
        for plan in tables.get("plans", [])
        if plan.get("insurer") and plan.get("plan_slug")
    }
    carriers = {
        row.get("carrier_key"): row
        for row in tables.get("carrier_canonical_names", [])
        if row.get("carrier_key")
    }
    rows = []
    for fact in tables.get("plan_facts", []):
        key = (fact.get("insurer"), fact.get("plan_slug"))
        plan = plans.get(key, {})
        carrier = carriers.get(fact.get("insurer"), {})
        field_value = fact.get("field_value") or {}
        rows.append(
            {
                "snapshot_date": snapshot_date,
                "insurer": fact.get("insurer") or "",
                "plan_slug": fact.get("plan_slug") or "",
                "plan_name": plan.get("plan_name") or "",
                "canonical_carrier_name": carrier.get("canonical_name") or "",
                "carrier_mismatch_flags": json_list(carrier.get("mismatch_flags") or []),
                "field_name": fact.get("field_name") or "",
                "field_status": field_value.get("status") or "",
                "field_value_json": json_value(field_value),
                "source_url": fact.get("source_url") or "",
                "source_type": fact.get("source_type") or "",
                "scraped_at": fact.get("scraped_at") or "",
                "last_verified_at": fact.get("last_verified_at") or "",
                "limitations": DEFAULT_LIMITATIONS,
            }
        )
    return sorted(
        rows,
        key=lambda row: (row["insurer"], row["plan_slug"], row["field_name"], row["source_url"]),
    )


def json_value(value) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def json_list(value) -> str:
    return json.dumps(list(value), ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def fetch_public_tables() -> dict[str, list[dict]]:
    load_dotenv()
    url = os.getenv("SUPABASE_URL") or os.getenv("VITE_SUPABASE_URL")
    key = (
        os.getenv("SUPABASE_ANON_KEY")
        or os.getenv("VITE_SUPABASE_ANON_KEY")
        or os.getenv("SUPABASE_SECRET_KEY")
        or os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    )
    if not url or not key:
        raise RuntimeError(
            "Open dataset export requires SUPABASE_URL plus SUPABASE_ANON_KEY "
            "or another read-capable Supabase key."
        )
    client = create_client(url, key)
    return {
        "plans": client.table("plans").select("*").execute().data or [],
        "plan_facts": client.table("plan_facts").select("*").execute().data or [],
        "carrier_canonical_names": client.table("carrier_canonical_names")
        .select("*")
        .execute()
        .data
        or [],
    }


def demo_tables() -> dict[str, list[dict]]:
    from src.backend.demo_data import demo_tables as load_demo_tables

    return load_demo_tables()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", help="Snapshot date in YYYY-MM-DD format.")
    parser.add_argument("--output", type=Path, help="CSV output path.")
    parser.add_argument("--demo", action="store_true", help="Use local seeded demo rows.")
    args = parser.parse_args()

    snapshot_date = args.date or generated_snapshot_date()
    output_path = args.output or default_snapshot_path(snapshot_date)
    tables = demo_tables() if args.demo else fetch_public_tables()
    row_count = export_open_dataset(output_path, snapshot_date, tables)
    print(
        json.dumps(
            {
                "snapshot_date": snapshot_date,
                "snapshot_path": str(output_path),
                "snapshot_row_count": row_count,
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
