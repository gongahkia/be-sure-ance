from __future__ import annotations

import time
from dataclasses import dataclass, field

NO_ADVICE_LINE = "Not advice. Verify against carrier sources and licensed adviser workflow."
SAFE_FAILURE_MESSAGE = "Lookup unavailable. Try again later."
RATE_LIMIT_MESSAGE = "Rate limit reached. Try again shortly."
MAX_RESULTS = 5

FIELD_LABELS = {
    "coverage_tags": "Coverage",
    "panel_hospitals": "Panel hospitals",
    "waiting_periods": "Waiting periods",
    "claim_deadlines": "Claim deadlines",
    "claim_sla": "Claim SLA",
    "exclusions": "Exclusions",
    "brochure_metadata": "Brochure",
    "source_notes": "Source notes",
}

FIELD_ALIASES = {
    "coverage": "coverage_tags",
    "network": "panel_hospitals",
    "panel": "panel_hospitals",
    "hospital": "panel_hospitals",
    "hospitals": "panel_hospitals",
    "waiting": "waiting_periods",
    "deadline": "claim_deadlines",
    "deadlines": "claim_deadlines",
    "claim": "claim_sla",
    "claims": "claim_sla",
    "sla": "claim_sla",
    "exclusion": "exclusions",
    "exclusions": "exclusions",
    "brochure": "brochure_metadata",
    "source": "source_notes",
    "notes": "source_notes",
}


@dataclass
class LookupResult:
    insurer: str
    plan_slug: str
    plan_name: str
    field_name: str
    value: str
    source_url: str
    verified_at: str


@dataclass
class RateLimiter:
    max_requests: int = 12
    window_seconds: int = 60
    buckets: dict[str, list[float]] = field(default_factory=dict)

    def allow(self, key: str, now: float | None = None) -> bool:
        now = now if now is not None else time.time()
        bucket = [
            timestamp
            for timestamp in self.buckets.get(key, [])
            if now - timestamp < self.window_seconds
        ]
        if len(bucket) >= self.max_requests:
            self.buckets[key] = bucket
            return False
        bucket.append(now)
        self.buckets[key] = bucket
        return True


class PlanFactIndex:
    def __init__(self, plans: list[dict], facts: list[dict]):
        self.plan_names = {
            plan_key(row.get("insurer"), row.get("plan_slug")): row.get("plan_name") or ""
            for row in plans
        }
        self.facts = facts

    def lookup_panel_hospital(self, query: str, limit: int = MAX_RESULTS) -> list[LookupResult]:
        query_text = normalize_query(query)
        if not query_text:
            return []

        results = []
        for fact in self.facts:
            if fact.get("field_name") != "panel_hospitals":
                continue
            for item in fact_items(fact):
                value = item_label(item)
                haystack = normalize_query(f"{value} {item.get('source_label', '')}")
                if query_text not in haystack:
                    continue
                results.append(result_from_fact(fact, value, plan_name=self.plan_name_for(fact)))
                break
            if len(results) >= limit:
                break
        return results

    def lookup_plan_fact(self, query: str, limit: int = MAX_RESULTS) -> list[LookupResult]:
        plan_query, field_name = split_fact_query(query)
        if not plan_query:
            return []

        results = []
        normalized_plan_query = normalize_query(plan_query)
        for fact in self.facts:
            if field_name and fact.get("field_name") != field_name:
                continue
            plan_name = self.plan_name_for(fact)
            haystack = normalize_query(
                f"{fact.get('insurer', '')} {fact.get('plan_slug', '')} {plan_name}"
            )
            if normalized_plan_query not in haystack:
                continue
            results.append(result_from_fact(fact, fact_summary(fact), plan_name=plan_name))
            if len(results) >= limit:
                break
        return results

    def plan_name_for(self, fact: dict) -> str:
        return (
            self.plan_names.get(plan_key(fact.get("insurer"), fact.get("plan_slug")))
            or fact.get("plan_slug")
            or "Unknown plan"
        )


def answer_panel_query(index: PlanFactIndex, query: str) -> str:
    results = index.lookup_panel_hospital(query)
    if not results:
        return with_no_advice("No panel-hospital match found.")
    lines = [f"Panel lookup: {query.strip()}"]
    lines.extend(format_result(result) for result in results)
    return with_no_advice("\n".join(lines))


def answer_fact_query(index: PlanFactIndex, query: str) -> str:
    results = index.lookup_plan_fact(query)
    if not results:
        return with_no_advice("No plan fact match found.")
    lines = [f"Plan fact lookup: {query.strip()}"]
    lines.extend(format_result(result) for result in results)
    return with_no_advice("\n".join(lines))


def safe_answer(
    command: str,
    query: str,
    index: PlanFactIndex,
    chat_key: str,
    limiter: RateLimiter,
) -> str:
    if not limiter.allow(chat_key):
        return RATE_LIMIT_MESSAGE
    try:
        if command == "panel":
            return answer_panel_query(index, query)
        if command == "fact":
            return answer_fact_query(index, query)
        return help_text()
    except Exception:
        return SAFE_FAILURE_MESSAGE


def help_text() -> str:
    return with_no_advice(
        "Commands:\n"
        "/panel <hospital name>\n"
        "/fact <plan name or slug> [coverage|panel|waiting|claim|exclusions|brochure]"
    )


def format_result(result: LookupResult) -> str:
    return (
        f"- {result.plan_name} ({result.insurer}/{result.plan_slug})\n"
        f"  {FIELD_LABELS.get(result.field_name, result.field_name)}: {result.value}\n"
        f"  Source: {result.source_url or 'missing'}\n"
        f"  Verified: {result.verified_at or 'missing'}"
    )


def with_no_advice(message: str) -> str:
    return f"{message}\n{NO_ADVICE_LINE}"


def split_fact_query(query: str) -> tuple[str, str | None]:
    parts = query.strip().split()
    if not parts:
        return "", None
    possible_field = FIELD_ALIASES.get(parts[-1].lower())
    if possible_field and len(parts) > 1:
        return " ".join(parts[:-1]), possible_field
    return query.strip(), None


def result_from_fact(fact: dict, value: str, plan_name: str | None = None) -> LookupResult:
    return LookupResult(
        insurer=fact.get("insurer") or "unknown",
        plan_slug=fact.get("plan_slug") or "unknown",
        plan_name=plan_name or fact.get("plan_name") or fact.get("plan_slug") or "Unknown plan",
        field_name=fact.get("field_name") or "unknown",
        value=value or "Unknown",
        source_url=fact.get("source_url") or "",
        verified_at=fact.get("last_verified_at") or "",
    )


def fact_summary(fact: dict) -> str:
    field_value = fact.get("field_value") or {}
    status = field_value.get("status")
    if status and status != "known":
        return status
    if fact.get("field_name") == "claim_sla":
        value = field_value.get("value") or {}
        if value.get("duration_days") is not None:
            basis = f" ({value.get('basis')})" if value.get("basis") else ""
            return f"{value['duration_days']} days{basis}"
    if fact.get("field_name") == "brochure_metadata":
        value = field_value.get("value") or {}
        if value.get("sha256"):
            return f"Captured hash {str(value['sha256'])[:12]}"
    items = fact_items(fact)
    labels = [item_label(item) for item in items]
    return ", ".join(label for label in labels if label) or "Unknown"


def fact_items(fact: dict) -> list:
    field_value = fact.get("field_value") or {}
    items = field_value.get("items") or []
    return items if isinstance(items, list) else []


def item_label(item) -> str:
    if isinstance(item, str):
        return item
    if not isinstance(item, dict):
        return ""
    return (
        item.get("normalized_name")
        or item.get("name")
        or item.get("label")
        or item.get("condition")
        or item.get("event")
        or item.get("details")
        or item.get("raw_text")
        or ""
    )


def normalize_query(value: str) -> str:
    return " ".join(str(value or "").lower().split())


def plan_key(insurer, plan_slug) -> str:
    return f"{insurer or ''}::{plan_slug or ''}"
