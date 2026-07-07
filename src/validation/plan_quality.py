from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable
from urllib.parse import urlparse

TEXT_FIELDS = ("plan_name", "plan_description", "plan_overview")
REQUIRED_FIELDS = ("insurer", "plan_slug", "plan_name", "plan_url")
MAX_TEXT_LENGTHS = {
    "plan_name": 160,
    "plan_description": 500,
    "plan_overview": 1800,
}
MAX_ERROR_MESSAGES = 20

CHROME_TEXT_PATTERNS = (
    "home products for individuals",
    "for individuals and families singapore coverage",
    "for businesses and employers singapore",
    "forms and downloads",
    "resource centre",
    "resource library",
    "covid-19 resource library",
    "insurance education",
    "social media facebook instagram linkedin",
    "facebook instagram linkedin",
    "blog webinar",
    "contact us x contact us",
    "about us blog",
    "privacy statement",
    "terms and conditions",
    "subscribe to our mailing list",
)

CATEGORY_NAME_PATTERNS = (
    "best health insurance plans",
    "health insurance plans in singapore",
    "be the boss that provides",
    "provide financial security",
    "protect you and your family",
    "find the right insurance",
    "finding the right insurance",
)

UNSUPPORTED_PLAN_URL_PATHS = (
    "/claim",
    "/claims",
    "/contact",
    "/resource-centre",
    "/resource-center",
    "/resource",
    "/forms",
    "/downloads",
    "/blog",
    "/webinar",
    "/privacy",
    "/terms",
    "/sitemap",
    "/careers",
    "/newsroom",
)


@dataclass(frozen=True)
class PlanQualityFinding:
    code: str
    insurer: str
    plan_slug: str
    plan_name: str
    field: str
    message: str

    def format(self) -> str:
        label = self.plan_slug or self.plan_name or "<unknown>"
        return f"{self.insurer or '<missing>'}/{label}: {self.message}"


def validate_plan_rows(
    plans: Iterable[dict],
    exceptions: Iterable[dict] | None = None,
) -> list[PlanQualityFinding]:
    rows = [row for row in plans if isinstance(row, dict)]
    findings: list[PlanQualityFinding] = []
    seen_keys: dict[tuple[str, str], dict] = {}
    exception_keys = _exception_keys(exceptions or ())

    for row in rows:
        findings.extend(_row_findings(row))
        key = (_text(row.get("insurer")), _text(row.get("plan_slug")))
        if all(key):
            if key in seen_keys:
                findings.append(
                    _finding(
                        row,
                        "duplicate_identity",
                        "plan_slug",
                        "duplicate (insurer, plan_slug) identity",
                    )
                )
            else:
                seen_keys[key] = row

    return [
        finding
        for finding in findings
        if (finding.insurer, finding.plan_slug, finding.field, finding.code) not in exception_keys
    ]


def validation_error_messages(
    plans: Iterable[dict],
    exceptions: Iterable[dict] | None = None,
) -> list[str]:
    return [
        f"semantic plan quality failed: {finding.format()}"
        for finding in validate_plan_rows(plans, exceptions=exceptions)[:MAX_ERROR_MESSAGES]
    ]


def semantic_quality_report(
    plans: Iterable[dict], exceptions: Iterable[dict] | None = None
) -> dict:
    rows = [row for row in plans if isinstance(row, dict)]
    findings = validate_plan_rows(rows, exceptions=exceptions)
    carriers = sorted({_text(row.get("insurer")) for row in rows if _text(row.get("insurer"))})
    failed_carriers = sorted({finding.insurer for finding in findings if finding.insurer})

    return {
        "status": "failed" if findings else "passed",
        "total_targets": len(carriers),
        "passed": max(len(carriers) - len(failed_carriers), 0),
        "failed": len(failed_carriers),
        "errors": 0,
        "no_baseline": 0,
        "total_rows": len(rows),
        "failed_rows": len({(f.insurer, f.plan_slug, f.plan_name) for f in findings}),
        "notes": [finding.format()[:500] for finding in findings[:5]],
    }


def _row_findings(row: dict) -> list[PlanQualityFinding]:
    findings: list[PlanQualityFinding] = []
    for field in REQUIRED_FIELDS:
        if not _text(row.get(field)):
            findings.append(_finding(row, "missing_required_field", field, f"missing {field}"))

    for field in TEXT_FIELDS:
        text = _text(row.get(field))
        if not text:
            continue
        normalized = _normalize(text)
        max_length = MAX_TEXT_LENGTHS[field]
        if len(text) > max_length:
            findings.append(
                _finding(
                    row,
                    "overlong_text",
                    field,
                    f"{field} length {len(text)} exceeds {max_length}",
                )
            )
        for pattern in CHROME_TEXT_PATTERNS:
            if pattern in normalized:
                findings.append(
                    _finding(row, "page_chrome_text", field, f"{field} contains page chrome")
                )
                break

    plan_name = _normalize(row.get("plan_name"))
    for pattern in CATEGORY_NAME_PATTERNS:
        if pattern in plan_name:
            findings.append(
                _finding(
                    row,
                    "category_or_hero_name",
                    "plan_name",
                    "plan_name looks like category or hero copy",
                )
            )
            break

    plan_url = _text(row.get("plan_url"))
    if plan_url:
        path = urlparse(plan_url).path.lower()
        for unsupported_path in UNSUPPORTED_PLAN_URL_PATHS:
            if path == unsupported_path or path.startswith(f"{unsupported_path}/"):
                findings.append(
                    _finding(
                        row,
                        "unsupported_plan_url",
                        "plan_url",
                        "plan_url points to non-product content",
                    )
                )
                break

    return findings


def _exception_keys(exceptions: Iterable[dict]) -> set[tuple[str, str, str, str]]:
    keys = set()
    for exception in exceptions:
        if not _text(exception.get("source_url")):
            continue
        keys.add(
            (
                _text(exception.get("insurer")),
                _text(exception.get("plan_slug")),
                _text(exception.get("field")),
                _text(exception.get("code")),
            )
        )
    return keys


def _finding(row: dict, code: str, field: str, message: str) -> PlanQualityFinding:
    return PlanQualityFinding(
        code=code,
        insurer=_text(row.get("insurer")),
        plan_slug=_text(row.get("plan_slug")),
        plan_name=_text(row.get("plan_name")),
        field=field,
        message=message,
    )


def _text(value) -> str:
    return str(value or "").strip()


def _normalize(value) -> str:
    return " ".join(_text(value).lower().split())
