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
AMOUNT_PATTERN = re.compile(r"(?:S\$|SGD|\$)\s?(\d{1,3}(?:,\d{3})*(?:\.\d{1,2})?)", re.I)
PERCENT_PATTERN = re.compile(r"(\d{1,2}(?:\.\d+)?)\s*%")
PLAN_KEYWORDS = (
    ("accident", ("accident", "personal accident")),
    ("hospitalization", ("hospital", "inpatient", "ward", "admission")),
    ("life", ("life", "death", "terminal illness")),
    ("critical_illness", ("critical illness", "ci")),
    ("outpatient", ("outpatient", "clinic", "general practitioner")),
    ("emergency", ("emergency", "ambulance", "evacuation")),
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


def money_values(sentence: str) -> list[float]:
    values = []
    for match in AMOUNT_PATTERN.findall(sentence):
        try:
            values.append(float(match.replace(",", "")))
        except ValueError:
            continue
    return values


def percentage_values(sentence: str) -> list[float]:
    values = []
    for match in PERCENT_PATTERN.findall(sentence):
        try:
            values.append(float(match))
        except ValueError:
            continue
    return values


def derive_premium_facts(text: str) -> dict:
    annual_candidates = []
    monthly_candidates = []
    fallback_candidates = []

    for sentence in re.split(r"[\n.]+", text):
        lowered = sentence.lower()
        amounts = money_values(sentence)
        if not amounts:
            continue

        if any(keyword in lowered for keyword in ("annual", "annually", "year", "yearly")):
            annual_candidates.extend(amounts)
        if any(keyword in lowered for keyword in ("monthly", "month")):
            monthly_candidates.extend(amounts)
        fallback_candidates.extend(amounts)

    annual_premium_min = min(annual_candidates) if annual_candidates else None
    monthly_premium_min = min(monthly_candidates) if monthly_candidates else None

    if annual_premium_min is None and monthly_premium_min is not None:
        annual_premium_min = round(monthly_premium_min * 12, 2)
    if monthly_premium_min is None and annual_premium_min is not None:
        monthly_premium_min = round(annual_premium_min / 12, 2)

    return {
        "currency": "SGD",
        "annual_premium_min": annual_premium_min,
        "monthly_premium_min": monthly_premium_min,
        "fallback_detected_amount": min(fallback_candidates) if fallback_candidates else None,
    }


def derive_cost_sharing(text: str) -> dict:
    deductible_candidates = []
    coinsurance_candidates = []

    for sentence in re.split(r"[\n.]+", text):
        lowered = sentence.lower()
        if "deductible" in lowered:
            deductible_candidates.extend(money_values(sentence))
        if any(keyword in lowered for keyword in ("co-insurance", "coinsurance", "copay", "co-pay")):
            coinsurance_candidates.extend(percentage_values(sentence))

    return {
        "deductible_amount": min(deductible_candidates) if deductible_candidates else 0,
        "coinsurance_percent": min(coinsurance_candidates) if coinsurance_candidates else 0,
        "out_of_pocket_cap": None,
    }


def derive_coverage_flags(text: str, specialist_resource_count: int, brochure_available: bool) -> dict:
    lowered = text.lower()
    flags = {
        key: any(keyword in lowered for keyword in keywords) for key, keywords in PLAN_KEYWORDS
    }
    flags["specialist_network"] = specialist_resource_count > 0
    flags["brochure_available"] = brochure_available
    return flags


def build_scenario_assumptions(premium_facts: dict, cost_sharing: dict) -> dict:
    return {
        "currency": "SGD",
        "claim_amounts": {
            "hospitalization": 5000,
            "outpatient": 400,
            "accident": 2500,
            "critical_illness": 12000,
        },
        "calculation_method": (
            "estimated annual cost = annual premium + deductible + "
            "(claim amount * coinsurance percent)"
        ),
        "premium_fallback_note": (
            "Uses annual premium when detected, otherwise falls back to 0 in the calculator."
            if premium_facts["annual_premium_min"] is None
            else "Uses detected annual premium."
        ),
        "deductible_note": (
            "Uses detected deductible when present, otherwise 0."
            if cost_sharing["deductible_amount"] == 0
            else "Uses detected deductible."
        ),
    }


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
    premium_facts = derive_premium_facts(text)
    cost_sharing = derive_cost_sharing(text)
    coverage_flags = derive_coverage_flags(
        text=text,
        specialist_resource_count=specialist_resource_count,
        brochure_available=bool(plan.get("product_brochure_url")),
    )
    scenario_assumptions = build_scenario_assumptions(premium_facts, cost_sharing)

    return {
        "insurer": insurer,
        "plan_name": plan["plan_name"],
        "plan_slug": slugify(plan["plan_name"]),
        "premium_facts": premium_facts,
        "cost_sharing": cost_sharing,
        "coverage_flags": coverage_flags,
        "scenario_assumptions": scenario_assumptions,
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
