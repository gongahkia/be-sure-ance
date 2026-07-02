from __future__ import annotations

import argparse
import json
import re
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from urllib.parse import urlencode

import requests
from rapidfuzz import fuzz

import src.backend.helper as helper
from src.lib.http_identity import BOT_USER_AGENT

NEHR_DATASET_ID = "d_2864c425e22ddb89969585820629adf8"
NEHR_DATASET_URL = "https://data.gov.sg/datasets/d_2864c425e22ddb89969585820629adf8/view"
NEHR_API_URL = "https://data.gov.sg/api/action/datastore_search"
MATCH_THRESHOLD = 88
REVIEW_THRESHOLD = 72
FETCH_LIMIT = 500
PAGE_DELAY_SECONDS = 0.25
MAX_FETCH_ATTEMPTS = 5


@dataclass(frozen=True)
class InstitutionRecord:
    canonical_id: str
    canonical_name: str
    aliases: tuple[str, ...]
    organization_name: str | None
    effective_date: str | None
    source_record_id: str
    source_dataset_id: str = NEHR_DATASET_ID
    source_url: str = NEHR_DATASET_URL


def normalize_whitespace(value: str | None) -> str:
    if not value:
        return ""
    return re.sub(r"\s+", " ", str(value)).strip()


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", normalize_whitespace(value).lower()).strip("-")
    return slug or "institution"


def match_key(value: str) -> str:
    text = normalize_whitespace(value).lower()
    text = text.replace("&", " and ")
    text = re.sub(r"\b(pte|ltd|limited|private|the)\b\.?", " ", text)
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return normalize_whitespace(text)


def unique_preserving_order(values: list[str]) -> tuple[str, ...]:
    seen = set()
    output = []
    for value in values:
        normalized = normalize_whitespace(value)
        if not normalized:
            continue
        key = normalized.lower()
        if key in seen:
            continue
        seen.add(key)
        output.append(normalized)
    return tuple(output)


def split_parenthetical_institutions(value: str) -> tuple[str, list[str]]:
    normalized = normalize_whitespace(value)
    match = re.match(r"^(?P<parent>.*?)\s*\((?P<children>.*)\)\s*$", normalized)
    if not match:
        return normalized, []

    parent = normalize_whitespace(match.group("parent"))
    children = [
        normalize_whitespace(item)
        for item in re.split(r";|\n", match.group("children"))
        if normalize_whitespace(item)
    ]
    return parent, children


def aliases_for_name(name: str) -> list[str]:
    aliases = [name]
    acronym = "".join(word[0] for word in re.findall(r"[A-Za-z]+", name))
    if len(acronym) >= 2:
        aliases.append(acronym.upper())
    simplified = re.sub(r"\b(Pte\.?\s+Ltd\.?|Ltd\.?|Limited)\b", "", name, flags=re.IGNORECASE)
    simplified = normalize_whitespace(simplified.strip(" .,-"))
    if simplified and simplified != name:
        aliases.append(simplified)
    if "Mount " in name:
        aliases.append(name.replace("Mount ", "Mt "))
    if "Mt " in name:
        aliases.append(name.replace("Mt ", "Mount "))
    return aliases


def build_record(
    *,
    source_record_id: str,
    canonical_name: str,
    organization_name: str | None,
    effective_date: str | None,
    extra_aliases: list[str] | None = None,
) -> InstitutionRecord:
    aliases = aliases_for_name(canonical_name)
    if extra_aliases:
        aliases.extend(extra_aliases)
    return InstitutionRecord(
        canonical_id=f"nehr-{source_record_id}-{slugify(canonical_name)}",
        canonical_name=canonical_name,
        aliases=unique_preserving_order(aliases),
        organization_name=organization_name,
        effective_date=effective_date,
        source_record_id=source_record_id,
    )


def parse_institution_records(records: list[dict]) -> list[InstitutionRecord]:
    institutions: dict[str, InstitutionRecord] = {}
    for row in records:
        raw_name = normalize_whitespace(row.get("Organization_Institution"))
        if not raw_name:
            continue

        source_record_id = str(row.get("_id") or row.get("73142") or slugify(raw_name))
        effective_date = normalize_whitespace(row.get("Effective_Date")) or None
        parent, children = split_parenthetical_institutions(raw_name)
        parent_record = build_record(
            source_record_id=source_record_id,
            canonical_name=parent,
            organization_name=None,
            effective_date=effective_date,
        )
        institutions[parent_record.canonical_id] = parent_record

        for child in children:
            child_record = build_record(
                source_record_id=source_record_id,
                canonical_name=child,
                organization_name=parent,
                effective_date=effective_date,
            )
            institutions[child_record.canonical_id] = child_record

    return sorted(institutions.values(), key=lambda item: item.canonical_name.lower())


def request_nehr_page(client, url: str):
    for attempt in range(MAX_FETCH_ATTEMPTS):
        response = client.get(url, timeout=30, headers={"User-Agent": BOT_USER_AGENT})
        if getattr(response, "status_code", 200) != 429:
            response.raise_for_status()
            return response

        retry_after = response.headers.get("retry-after") if hasattr(response, "headers") else None
        sleep_seconds = float(retry_after) if retry_after else min(2**attempt, 30)
        time.sleep(sleep_seconds)

    response.raise_for_status()
    return response


def fetch_nehr_records(
    session=None,
    limit: int = FETCH_LIMIT,
    page_delay_seconds: float = PAGE_DELAY_SECONDS,
) -> list[dict]:
    client = session or requests
    rows = []
    offset = 0
    while True:
        url = f"{NEHR_API_URL}?{urlencode({'resource_id': NEHR_DATASET_ID, 'limit': limit, 'offset': offset})}"
        response = request_nehr_page(client, url)
        payload = response.json()
        result = payload.get("result") or {}
        batch = result.get("records") or []
        rows.extend(batch)
        if not batch or len(rows) >= int(result.get("total") or len(rows)):
            return rows
        offset += len(batch)
        if page_delay_seconds > 0:
            time.sleep(page_delay_seconds)


def fetch_institution_records(session=None) -> list[InstitutionRecord]:
    return parse_institution_records(fetch_nehr_records(session=session))


def record_to_row(record: InstitutionRecord, scraped_at: str | None = None) -> dict:
    scraped_at = scraped_at or datetime.now(timezone.utc).isoformat()
    return {
        "canonical_id": record.canonical_id,
        "canonical_name": record.canonical_name,
        "aliases": list(record.aliases),
        "organization_name": record.organization_name,
        "effective_date": record.effective_date,
        "source_dataset_id": record.source_dataset_id,
        "source_record_id": record.source_record_id,
        "source_url": record.source_url,
        "scraped_at": scraped_at,
    }


def upsert_institution_records(records: list[InstitutionRecord]) -> None:
    helper.require_write_key()
    rows = [record_to_row(record) for record in records]
    if not rows:
        print("No MOH institution records to upsert.")
        return
    helper.require_client().table("moh_institutions").upsert(
        rows, on_conflict="canonical_id"
    ).execute()
    print(f"MOH institution records upserted: {len(rows)}")


def load_institution_records_from_supabase() -> list[InstitutionRecord]:
    rows = helper.require_client().table("moh_institutions").select("*").execute().data or []
    return [
        InstitutionRecord(
            canonical_id=row["canonical_id"],
            canonical_name=row["canonical_name"],
            aliases=tuple(row.get("aliases") or []),
            organization_name=row.get("organization_name"),
            effective_date=row.get("effective_date"),
            source_record_id=str(row.get("source_record_id") or ""),
            source_dataset_id=row.get("source_dataset_id") or NEHR_DATASET_ID,
            source_url=row.get("source_url") or NEHR_DATASET_URL,
        )
        for row in rows
    ]


def normalize_panel_name(name: str, records: list[InstitutionRecord]) -> dict:
    raw_name = normalize_whitespace(name)
    best_record = None
    best_alias = ""
    best_score = 0
    best_candidates: list[InstitutionRecord] = []
    for record in records:
        for alias in record.aliases:
            score = fuzz.token_set_ratio(match_key(raw_name), match_key(alias))
            if score > best_score:
                best_record = record
                best_alias = alias
                best_score = int(round(score))
                best_candidates = [record]
            elif int(round(score)) == best_score:
                best_candidates.append(record)

    if not best_record or best_score < REVIEW_THRESHOLD:
        return {
            "name": raw_name,
            "normalized_name": raw_name,
            "match_status": "unmatched",
            "match_confidence": 0,
            "matched_alias": None,
            "canonical_id": None,
            "source_label": "Panel hospital",
            "review_required": True,
        }

    candidate_ids = sorted({record.canonical_id for record in best_candidates})
    is_ambiguous = best_score >= MATCH_THRESHOLD and len(candidate_ids) > 1
    match_status = (
        "matched" if best_score >= MATCH_THRESHOLD and not is_ambiguous else "needs_review"
    )
    normalized_name = best_record.canonical_name if match_status == "matched" else raw_name
    return {
        "name": raw_name,
        "normalized_name": normalized_name,
        "match_status": match_status,
        "match_confidence": best_score,
        "matched_alias": best_alias,
        "canonical_id": best_record.canonical_id if match_status == "matched" else None,
        "suggested_normalized_name": best_record.canonical_name,
        "suggested_canonical_id": best_record.canonical_id,
        "candidate_canonical_ids": candidate_ids,
        "source_label": "Panel hospital",
        "review_required": match_status != "matched",
    }


def normalize_panel_hospital_items(
    items: list[dict], records: list[InstitutionRecord]
) -> list[dict]:
    return [normalize_panel_name(item.get("name", ""), records) for item in items]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    helper.initialize_supabase()
    records = fetch_institution_records()
    print(json.dumps({"moh_institution_count": len(records)}, indent=2, sort_keys=True))
    if args.dry_run:
        return
    upsert_institution_records(records)


if __name__ == "__main__":
    main()
