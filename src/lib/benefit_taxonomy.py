from __future__ import annotations

import re
from dataclasses import dataclass

TAXONOMY_VERSION = 1


@dataclass(frozen=True)
class TaxonomyRule:
    tag: str
    patterns: tuple[str, ...]


EXCLUSION_RULES = (
    TaxonomyRule("pre_existing_condition", (r"pre[-\s]?existing",)),
    TaxonomyRule("self_inflicted_injury", (r"self[-\s]?inflicted", r"suicide")),
    TaxonomyRule("war_or_terrorism", (r"\bwar\b", r"terror")),
    TaxonomyRule("pregnancy_or_childbirth", (r"pregnan", r"childbirth", r"maternity")),
    TaxonomyRule("cosmetic_treatment", (r"cosmetic", r"aesthetic")),
    TaxonomyRule("experimental_treatment", (r"experimental", r"investigational")),
    TaxonomyRule("congenital_condition", (r"congenital",)),
    TaxonomyRule("dental_or_vision", (r"dental", r"vision", r"optical", r"eye test")),
    TaxonomyRule("routine_or_screening", (r"routine", r"screening", r"health check")),
    TaxonomyRule("substance_or_alcohol", (r"alcohol", r"drug abuse", r"substance")),
    TaxonomyRule("hazardous_activity", (r"hazardous", r"dangerous sport", r"racing")),
    TaxonomyRule("overseas_treatment", (r"overseas", r"outside singapore")),
)

WAITING_PERIOD_RULES = (
    TaxonomyRule("specified_condition", (r"specified", r"specific illness", r"named condition")),
    TaxonomyRule("pre_existing_condition", (r"pre[-\s]?existing",)),
    TaxonomyRule("pregnancy_or_childbirth", (r"pregnan", r"childbirth", r"maternity")),
    TaxonomyRule("congenital_condition", (r"congenital",)),
    TaxonomyRule("dental_or_vision", (r"dental", r"vision", r"optical")),
    TaxonomyRule("psychiatric_or_mental_health", (r"psychiatric", r"mental health")),
    TaxonomyRule("organ_transplant", (r"organ transplant", r"transplant")),
)


def normalize_exclusion_item(label: str) -> dict:
    return tagged_item(
        label=label,
        details=label,
        rules=EXCLUSION_RULES,
    )


def normalize_waiting_period_item(condition: str, duration_days: int, raw_text: str) -> dict:
    item = tagged_item(
        label=condition,
        details=condition,
        rules=WAITING_PERIOD_RULES,
    )
    item.update(
        {
            "condition": condition,
            "duration_days": duration_days,
            "raw_text": raw_text,
        }
    )
    return item


def tagged_item(label: str, details: str, rules: tuple[TaxonomyRule, ...]) -> dict:
    tags = taxonomy_tags(label, rules)
    return {
        "label": label,
        "details": details,
        "tags": tags,
        "taxonomy_status": "tagged" if tags else "needs_review",
        "review_required": not bool(tags),
        "review_reason": "" if tags else "no_taxonomy_match",
    }


def taxonomy_tags(value: str, rules: tuple[TaxonomyRule, ...]) -> list[str]:
    tags = []
    for rule in rules:
        if any(re.search(pattern, value, flags=re.IGNORECASE) for pattern in rule.patterns):
            tags.append(rule.tag)
    return tags


def taxonomy_notes(items: list[dict]) -> list[str]:
    if any(item.get("review_required") for item in items):
        return ["Some items need manual taxonomy review."]
    return []
