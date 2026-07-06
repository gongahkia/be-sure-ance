from __future__ import annotations

import argparse
import json
from pathlib import Path

DEFAULT_APP_DATA_PATH = Path("src/be-sure-ance-app/public/data/app-data.json")
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
DEMO_MARKERS = (
    "https://example.com/demo-source",
    "healthshield-gold-max-demo",
    "supremehealth-demo",
    "local-demo-no-bucket",
)


def load_payload(path: Path) -> dict:
    return json.loads(path.read_text())


def validation_errors(
    payload: dict,
    min_plans: int = 10,
    min_carriers: int = 3,
    min_plan_facts: int = 1,
    min_comparison_facts: int = 1,
) -> list[str]:
    if not isinstance(payload, dict):
        return ["payload must be a JSON object"]

    tables = payload.get("tables")
    if not isinstance(tables, dict):
        return ["payload.tables must be an object"]

    errors = []
    for table in APP_TABLES:
        if not isinstance(tables.get(table), list):
            errors.append(f"payload.tables.{table} must be a list")

    if errors:
        return errors

    plans = tables["plans"]
    plan_facts = tables["plan_facts"]
    comparison_facts = tables["plan_comparison_facts"]
    carriers = {plan.get("insurer") for plan in plans if plan.get("insurer")}

    if len(plans) < min_plans:
        errors.append(f"expected at least {min_plans} plans, found {len(plans)}")
    if len(carriers) < min_carriers:
        errors.append(f"expected at least {min_carriers} carriers, found {len(carriers)}")
    if len(plan_facts) < min_plan_facts:
        errors.append(f"expected at least {min_plan_facts} plan facts, found {len(plan_facts)}")
    if len(comparison_facts) < min_comparison_facts:
        errors.append(
            f"expected at least {min_comparison_facts} comparison facts, found {len(comparison_facts)}"
        )
    if contains_demo_marker(payload):
        errors.append("payload contains seeded demo markers")

    return errors


def contains_demo_marker(value) -> bool:
    if isinstance(value, str):
        return any(marker in value for marker in DEMO_MARKERS)
    if isinstance(value, dict):
        return any(contains_demo_marker(item) for item in value.values())
    if isinstance(value, list):
        return any(contains_demo_marker(item) for item in value)
    return False


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--path", type=Path, default=DEFAULT_APP_DATA_PATH)
    parser.add_argument("--min-plans", type=int, default=10)
    parser.add_argument("--min-carriers", type=int, default=3)
    parser.add_argument("--min-plan-facts", type=int, default=1)
    parser.add_argument("--min-comparison-facts", type=int, default=1)
    args = parser.parse_args()

    errors = validation_errors(
        load_payload(args.path),
        min_plans=args.min_plans,
        min_carriers=args.min_carriers,
        min_plan_facts=args.min_plan_facts,
        min_comparison_facts=args.min_comparison_facts,
    )
    if errors:
        for error in errors:
            print(f"static_app_data validation failed: {error}")
        return 1

    print(f"static_app_data validation passed: {args.path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
