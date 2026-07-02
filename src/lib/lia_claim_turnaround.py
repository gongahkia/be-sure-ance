from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timezone

LIA_MAKING_CLAIM_URL = "https://www.lia.org.sg/consumers/making-a-claim/"
LIA_2024_RESULTS_URL = (
    "https://www.lia.org.sg/media/4458/20250213_lia-4q2024-results_media-release.pdf"
)
LIA_2025_RESULTS_URL = (
    "https://www.lia.org.sg/media/4789/20260211_lia-4q2025-results_media-release.pdf"
)
INDUSTRY_CARRIER_KEY = "industry"
INDUSTRY_CARRIER_NAME = "LIA Singapore industry aggregate"
NO_CARRIER_RANKING_LIMITATION = (
    "LIA source is industry aggregate; it does not publish carrier-level turnaround rankings."
)
NO_GUARANTEE_LIMITATION = (
    "Handling timelines are public process statements, not suitability signals or claim guarantees."
)

NUMBER_WORDS = {
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
    "eleven": 11,
    "twelve": 12,
}

CARRIER_ALIASES = {
    "aia": ("aia", "aia singapore", "aia singapore private limited"),
    "great_eastern": ("great eastern", "great eastern life", "the great eastern life assurance"),
    "hsbc": ("hsbc", "hsbc insurance", "hsbc life singapore"),
    "income": ("income", "ntuc income", "income insurance"),
    "manulife": ("manulife", "manulife singapore"),
    "prudential": ("prudential", "prudential assurance"),
    "singlife": ("singlife", "aviva"),
    "tokio_marine": ("tokio marine", "tokio marine life"),
    "etiqa": ("etiqa",),
    "fwd": ("fwd",),
    "raffles_health": ("raffles health", "raffles health insurance"),
}


@dataclass(frozen=True)
class ClaimTurnaroundMetric:
    carrier_key: str
    carrier_name: str
    metric_key: str
    metric_label: str
    metric_value: dict
    metric_unit: str
    source_year: int
    source_url: str
    source_type: str
    rank: int | None = None
    limitations: list[str] = field(default_factory=list)
    scraped_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def as_row(self) -> dict:
        return {
            "carrier_key": self.carrier_key,
            "carrier_name": self.carrier_name,
            "metric_key": self.metric_key,
            "metric_label": self.metric_label,
            "metric_value": self.metric_value,
            "metric_unit": self.metric_unit,
            "rank": self.rank,
            "source_year": self.source_year,
            "source_url": self.source_url,
            "source_type": self.source_type,
            "limitations": self.limitations,
            "scraped_at": self.scraped_at,
            "last_verified_at": self.scraped_at,
        }


def parse_claim_handling_standards(
    text: str,
    source_url: str = LIA_MAKING_CLAIM_URL,
    source_year: int | None = None,
    scraped_at: str | None = None,
) -> list[ClaimTurnaroundMetric]:
    source_year = source_year or datetime.now(timezone.utc).year
    normalized = normalize_whitespace(text)
    specs = [
        (
            "notice_deadline",
            "Claim notice deadline",
            r"notice in writing of the claim within (?P<amount>\d+|[a-z]+) days? of the event",
            "days",
            "notice to insurer",
        ),
        (
            "acknowledge_notice",
            "Claim notice acknowledgement",
            r"acknowledge receipt of your notice of claim within (?P<amount>\d+|[a-z]+) days?",
            "days",
            "acknowledgement after notice",
        ),
        (
            "request_information",
            "Additional information request",
            r"Within (?P<amount>\d+|[a-z]+) days? of receiving the notice of claim, they will let you know whether they need any more information",
            "days",
            "additional information request",
        ),
        (
            "claim_decision",
            "Claim decision after full information",
            r"Within (?P<amount>\d+|[a-z]+) days? of receiving full information for claim assessment, they will let you know of their decision",
            "days",
            "accept or reject decision",
        ),
        (
            "straightforward_payment",
            "Straightforward claim payment",
            r"straightforward cases, the insurer will pay a claim within (?P<amount>\d+|[a-z]+) days? of receiving all of the required documents",
            "days",
            "straightforward cases after required documents",
        ),
        (
            "death_claim_interest",
            "Death claim interest threshold",
            r"pay interest if they pay a claim more than (?P<amount>\d+|[a-z]+) months? from the date they received your written notice",
            "months",
            "death claim interest threshold",
        ),
    ]

    metrics = []
    for metric_key, label, pattern, unit, basis in specs:
        match = re.search(pattern, normalized, flags=re.IGNORECASE)
        if not match:
            continue
        amount = parse_number(match.group("amount"))
        if amount is None:
            continue
        metrics.append(
            industry_metric(
                metric_key=metric_key,
                metric_label=label,
                value={unit: amount, "basis": basis},
                metric_unit=unit,
                source_year=source_year,
                source_url=source_url,
                source_type="lia_consumer_guide",
                raw_text=sentence_for_match(normalized, match),
                scraped_at=scraped_at,
            )
        )
    return metrics


def parse_annual_claim_payouts(
    text: str,
    source_url: str,
    source_year: int | None = None,
    scraped_at: str | None = None,
) -> list[ClaimTurnaroundMetric]:
    normalized = normalize_whitespace(text)
    year = source_year or extract_year(normalized)
    if not year:
        return []

    specs = [
        (
            "industry_claims_maturity_payouts",
            "Claims and maturity payouts",
            r"In\s+(?P<year>20\d{2}),[^.]*?paid S\$(?P<amount>\d+(?:\.\d+)?) billion to policyholders and beneficiaries",
            "claims and maturity payouts",
        ),
        (
            "industry_maturity_payouts",
            "Maturity payouts",
            r"(?:S\$(?P<amount_a>\d+(?:\.\d+)?) billion was for policies that matured|paid out[^.]*?S\$(?P<amount_b>\d+(?:\.\d+)?) billion for policies that matured)",
            "policies that matured",
        ),
        (
            "industry_death_tpd_ci_claims",
            "Death, TPD, and CI claims",
            r"S\$(?P<amount_a>\d+(?:\.\d+)?) billion (?:was|was paid out|paid out)?[^.]{0,80}?for death, total and permanent disability and critical illness claims|A total of S\$(?P<amount_b>\d+(?:\.\d+)?) billion was paid out for death, total and permanent disability and critical illness claims",
            "death, total and permanent disability, and critical illness claims",
        ),
    ]

    metrics = []
    for metric_key, label, pattern, basis in specs:
        match = re.search(pattern, normalized, flags=re.IGNORECASE)
        if not match:
            continue
        amount = next(
            (
                float(value)
                for key, value in match.groupdict().items()
                if key.startswith("amount")
                if value and re.match(r"\d+(?:\.\d+)?$", value)
            ),
            None,
        )
        if amount is None:
            continue
        metrics.append(
            industry_metric(
                metric_key=metric_key,
                metric_label=label,
                value={"amount_sgd_billion": amount, "basis": basis},
                metric_unit="sgd_billion",
                source_year=year,
                source_url=source_url,
                source_type="lia_annual_results_pdf",
                raw_text=sentence_for_match(normalized, match),
                scraped_at=scraped_at,
            )
        )
    return metrics


def industry_metric(
    metric_key: str,
    metric_label: str,
    value: dict,
    metric_unit: str,
    source_year: int,
    source_url: str,
    source_type: str,
    raw_text: str,
    scraped_at: str | None = None,
) -> ClaimTurnaroundMetric:
    return ClaimTurnaroundMetric(
        carrier_key=INDUSTRY_CARRIER_KEY,
        carrier_name=INDUSTRY_CARRIER_NAME,
        metric_key=metric_key,
        metric_label=metric_label,
        metric_value={
            "status": "known",
            "value": value,
            "raw_text": raw_text,
        },
        metric_unit=metric_unit,
        rank=None,
        source_year=source_year,
        source_url=source_url,
        source_type=source_type,
        limitations=[NO_CARRIER_RANKING_LIMITATION, NO_GUARANTEE_LIMITATION],
        scraped_at=scraped_at or datetime.now(timezone.utc).isoformat(),
    )


def normalize_carrier_name(value: str) -> tuple[str, str]:
    normalized = normalize_whitespace(value).lower()
    for carrier_key, aliases in CARRIER_ALIASES.items():
        if any(alias in normalized for alias in aliases):
            return carrier_key, carrier_display_name(carrier_key)
    return slugify(normalized), normalize_whitespace(value)


def carrier_display_name(carrier_key: str) -> str:
    return {
        "aia": "AIA Singapore",
        "great_eastern": "Great Eastern Singapore",
        "hsbc": "HSBC Life Singapore",
        "income": "Income Insurance",
        "manulife": "Manulife Singapore",
        "prudential": "Prudential Singapore",
        "singlife": "Singlife",
        "tokio_marine": "Tokio Marine Life Singapore",
        "etiqa": "Etiqa Singapore",
        "fwd": "FWD Singapore",
        "raffles_health": "Raffles Health Insurance",
    }.get(carrier_key, carrier_key)


def normalize_whitespace(value: str) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def parse_number(value: str) -> int | None:
    normalized = normalize_whitespace(value).lower()
    if normalized.isdigit():
        return int(normalized)
    return NUMBER_WORDS.get(normalized)


def extract_year(text: str) -> int | None:
    match = re.search(r"\b(20\d{2})\b", text)
    return int(match.group(1)) if match else None


def sentence_for_match(text: str, match: re.Match) -> str:
    start = text.rfind(".", 0, match.start()) + 1
    end = text.find(".", match.end())
    if end == -1:
        end = len(text)
    return normalize_whitespace(text[start:end])


def slugify(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", normalize_whitespace(value).lower()).strip("-")
