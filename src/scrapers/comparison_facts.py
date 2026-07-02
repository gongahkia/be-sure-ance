from __future__ import annotations

import argparse
import json
import re

import src.backend.helper as helper
from src.backend.helper import initialize_supabase, overwrite_generic_table_data


SUPPORTED_INSURERS = (
    "aia",
    "uoi",
    "china_life",
    "chubb",
    "tokio_marine",
    "sunlife",
    "singlife",
    "great_eastern",
    "hsbc",
    "iii",
)
PLAN_KEYWORDS = (
    ("accident", ("accident", "personal accident")),
    ("hospitalization", ("hospital", "inpatient", "ward", "admission")),
    ("life", ("life", "death", "terminal illness")),
    ("critical_illness", ("critical illness", "ci")),
    ("outpatient", ("outpatient", "clinic", "general practitioner")),
    ("emergency", ("emergency", "ambulance", "evacuation")),
)
RESOURCE_TAGS = (
    ("provider_directory", "provider directory"),
    ("brochure_available", "brochure available"),
)


def normalize_whitespace(value: str | None) -> str:
    if not value:
        return ""
    return re.sub(r"\s+", " ", value).strip()


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "plan"


def fetch_rows(table_name: str) -> list[dict]:
    response = helper.supabase.table(table_name).select("*").execute()
    return response.data or []


def first_sentences(text: str, limit: int = 2) -> str:
    segments = [segment.strip() for segment in re.split(r"[.\n]+", text) if segment.strip()]
    return ". ".join(segments[:limit])


def derive_coverage_tags(text: str, specialist_resource_count: int, brochure_available: bool) -> list[str]:
    lowered = text.lower()
    tags = [
        key for key, keywords in PLAN_KEYWORDS if any(keyword in lowered for keyword in keywords)
    ]
    if specialist_resource_count > 0:
        tags.append(RESOURCE_TAGS[0][0])
    if brochure_available:
        tags.append(RESOURCE_TAGS[1][0])
    return tags


def build_comparison_notes(plan: dict, specialist_resource_count: int) -> str:
    summary = first_sentences(
        normalize_whitespace(
            " ".join(
                [
                    plan.get("plan_description", ""),
                    plan.get("plan_overview", ""),
                    " ".join(plan.get("plan_benefits") or []),
                ]
            )
        )
    )
    if specialist_resource_count > 0:
        return f"{summary}. Includes linked panel or specialist resources."
    return summary


def build_fact_row(insurer: str, plan: dict, specialist_resource_count: int) -> dict:
    text = normalize_whitespace(
        " ".join(
            [
                plan.get("plan_name", ""),
                plan.get("plan_description", ""),
                plan.get("plan_overview", ""),
                " ".join(plan.get("plan_benefits") or []),
            ]
        )
    )
    coverage_tags = derive_coverage_tags(
        text=text,
        specialist_resource_count=specialist_resource_count,
        brochure_available=bool(plan.get("product_brochure_url")),
    )

    return {
        "insurer": insurer,
        "plan_name": plan["plan_name"],
        "plan_slug": slugify(plan["plan_name"]),
        "panel_network_size": None,
        "claim_sla_days": None,
        "exclusions": [],
        "waiting_period_days": None,
        "coverage_tags": coverage_tags,
        "brochure_hash": None,
        "brochure_last_changed_at": None,
        "comparison_notes": build_comparison_notes(plan, specialist_resource_count),
        "source_url": plan.get("product_brochure_url") or plan.get("plan_url"),
    }


def build_specialist_resource_counts() -> dict[tuple[str, str], int]:
    response = helper.supabase.table("specialist_resources").select("insurer, plan_name").execute()
    rows = response.data or []
    counts: dict[tuple[str, str], int] = {}
    for row in rows:
        key = (row["insurer"], row["plan_name"])
        counts[key] = counts.get(key, 0) + 1
    return counts


def build_comparison_rows(insurers: list[str], max_plans: int | None) -> list[dict]:
    specialist_counts = build_specialist_resource_counts()
    rows = []
    for insurer in insurers:
        plans = fetch_rows(insurer)
        if max_plans is not None:
            plans = plans[:max_plans]
        for plan in plans:
            plan_name = plan.get("plan_name")
            if not plan_name:
                continue
            count = specialist_counts.get((insurer, plan_name), 0)
            rows.append(build_fact_row(insurer, plan, count))
    return rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--insurers", help="Comma-separated supported insurer table names.")
    parser.add_argument("--max-plans", type=int)
    args = parser.parse_args()

    insurers = (
        [item.strip() for item in args.insurers.split(",") if item.strip()]
        if args.insurers
        else list(SUPPORTED_INSURERS)
    )

    initialize_supabase()
    rows = build_comparison_rows(insurers=insurers, max_plans=args.max_plans)

    summary = {
        "comparison_row_count": len(rows),
        "insurers": insurers,
    }
    print(json.dumps(summary, indent=2, sort_keys=True))

    if args.dry_run:
        return

    overwrite_generic_table_data("plan_comparison_facts", rows)


if __name__ == "__main__":
    main()
