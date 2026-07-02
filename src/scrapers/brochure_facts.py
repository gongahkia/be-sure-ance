from __future__ import annotations

import argparse
import io
import json
import re
from datetime import datetime, timezone

from pypdf import PdfReader

import src.backend.helper as helper
from src.backend.helper import initialize_data_store
from src.lib.benefit_taxonomy import (
    TAXONOMY_VERSION,
    normalize_exclusion_item,
    normalize_waiting_period_item,
    taxonomy_notes,
)
from src.lib.moh_institutions import (
    InstitutionRecord,
    load_institution_records_from_store,
    normalize_panel_hospital_items,
)

QUALITATIVE_FIELDS = (
    "panel_hospitals",
    "exclusions",
    "waiting_periods",
    "claim_deadlines",
    "claim_sla",
)


def normalize_whitespace(value: str | None) -> str:
    if not value:
        return ""
    return re.sub(r"\s+", " ", value).strip()


def extract_pdf_text_from_bytes(content: bytes, max_pages: int = 10) -> str:
    reader = PdfReader(io.BytesIO(content))
    pages = []
    for page in reader.pages[:max_pages]:
        pages.append(page.extract_text() or "")
    return normalize_whitespace("\n".join(pages))


def split_list_items(value: str) -> list[str]:
    parts = re.split(r";|,|\band\b", value)
    return [
        normalize_whitespace(part.strip(" .:-")) for part in parts if normalize_whitespace(part)
    ]


def section_text(text: str, heading_pattern: str, stop_pattern: str) -> str:
    match = re.search(
        rf"{heading_pattern}\s*[:\-]\s*(.*?)(?={stop_pattern}\s*[:\-]|$)",
        text,
        flags=re.IGNORECASE,
    )
    return normalize_whitespace(match.group(1)) if match else ""


def source_only_panel_item(name: str) -> dict:
    return {
        "name": name,
        "normalized_name": name,
        "source_label": "Panel hospital",
        "match_status": "not_checked",
        "match_confidence": None,
        "matched_alias": None,
        "canonical_id": None,
        "review_required": True,
    }


def parse_panel_hospitals(
    text: str,
    institution_records: list[InstitutionRecord] | None = None,
) -> dict | None:
    section = section_text(text, r"panel hospitals?", r"exclusions?|waiting periods?|claims?")
    items = []
    for name in split_list_items(section):
        has_facility_hint = re.search(
            r"\b(hospital|hosp|medical centre|clinic|centre)\b",
            name,
            re.IGNORECASE,
        )
        if not has_facility_hint and not institution_records:
            continue
        items.append({"name": name})
    if not items:
        return None
    if institution_records:
        normalized_items = normalize_panel_hospital_items(items, institution_records)
        notes = []
    else:
        normalized_items = [source_only_panel_item(item["name"]) for item in items]
        notes = ["MOH institution normalization not run."]
    return {
        "status": "known",
        "items": normalized_items,
        "raw_text": section,
        "notes": notes,
        "review_required": any(item.get("review_required") for item in normalized_items),
    }


def parse_exclusions(text: str) -> dict | None:
    section = section_text(text, r"exclusions?", r"waiting periods?|claims?|panel hospitals?")
    items = [normalize_exclusion_item(item) for item in split_list_items(section) if len(item) >= 4]
    if not items:
        return None
    return {
        "status": "known",
        "items": items,
        "raw_text": section,
        "notes": taxonomy_notes(items),
        "taxonomy_version": TAXONOMY_VERSION,
        "review_required": any(item.get("review_required") for item in items),
    }


def parse_waiting_periods(text: str) -> dict | None:
    items = []
    for match in re.finditer(
        r"(?P<days>\d{1,4})\s+days?\s+(?:waiting period\s+)?(?:for\s+)?(?P<condition>[^.;]+)",
        text,
        flags=re.IGNORECASE,
    ):
        raw_text = normalize_whitespace(match.group(0))
        if "waiting" not in raw_text.lower():
            continue
        condition = normalize_whitespace(match.group("condition"))
        items.append(
            normalize_waiting_period_item(
                condition=condition,
                duration_days=int(match.group("days")),
                raw_text=raw_text,
            )
        )
    if not items:
        return None
    return {
        "status": "known",
        "items": items,
        "raw_text": "; ".join(item["raw_text"] for item in items),
        "notes": taxonomy_notes(items),
        "taxonomy_version": TAXONOMY_VERSION,
        "review_required": any(item.get("review_required") for item in items),
    }


def parse_claim_deadlines(text: str) -> dict | None:
    items = []
    for match in re.finditer(
        r"submit\s+(?P<event>[^.]{0,80}?)\s*within\s+(?P<days>\d{1,4})\s+days?",
        text,
        flags=re.IGNORECASE,
    ):
        raw_text = normalize_whitespace(match.group(0))
        event = normalize_whitespace(match.group("event")) or "claim"
        items.append(
            {
                "event": event,
                "deadline_days": int(match.group("days")),
                "raw_text": raw_text,
            }
        )
    if not items:
        return None
    return {
        "status": "known",
        "items": items,
        "raw_text": "; ".join(item["raw_text"] for item in items),
        "notes": [],
    }


def parse_claim_sla(text: str) -> dict | None:
    match = re.search(
        r"claims?\s+(?:are\s+)?processed\s+within\s+(?P<days>\d{1,4})\s+working\s+days?",
        text,
        flags=re.IGNORECASE,
    )
    if not match:
        return None
    raw_text = normalize_whitespace(match.group(0))
    return {
        "status": "known",
        "value": {
            "duration_days": int(match.group("days")),
            "basis": "published target",
        },
        "raw_text": raw_text,
        "notes": [],
    }


def parse_brochure_text(
    text: str,
    institution_records: list[InstitutionRecord] | None = None,
) -> dict[str, dict]:
    normalized = normalize_whitespace(text)
    parsed = {
        "panel_hospitals": parse_panel_hospitals(normalized, institution_records),
        "exclusions": parse_exclusions(normalized),
        "waiting_periods": parse_waiting_periods(normalized),
        "claim_deadlines": parse_claim_deadlines(normalized),
        "claim_sla": parse_claim_sla(normalized),
    }
    return {field: value for field, value in parsed.items() if value}


def build_fact_rows(
    insurer: str,
    plan_slug: str,
    source_url: str,
    parsed_facts: dict[str, dict],
    captured_at: str | None = None,
) -> list[dict]:
    captured_at = captured_at or datetime.now(timezone.utc).isoformat()
    return [
        {
            "insurer": insurer,
            "plan_slug": plan_slug,
            "field_name": field_name,
            "field_value": field_value,
            "source_url": source_url,
            "source_type": "brochure_pdf",
            "scraped_at": captured_at,
            "last_verified_at": captured_at,
        }
        for field_name, field_value in parsed_facts.items()
        if field_name in QUALITATIVE_FIELDS
    ]


def fetch_brochure_metadata_rows(insurers: list[str] | None = None) -> list[dict]:
    response = (
        helper.require_client()
        .table("plan_facts")
        .select("*")
        .eq("field_name", helper.BROCHURE_CAPTURE_FIELD)
        .execute()
    )
    rows = response.data or []
    if insurers:
        allowed = set(insurers)
        rows = [row for row in rows if row.get("insurer") in allowed]
    return rows


def download_stored_brochure(metadata_row: dict) -> bytes:
    metadata = (metadata_row.get("field_value") or {}).get("value") or {}
    bucket = metadata["storage_bucket"]
    storage_key = metadata["storage_key"]
    return helper.require_client().storage.from_(bucket).download(storage_key)


def parse_brochure_metadata_row(
    metadata_row: dict,
    institution_records: list[InstitutionRecord] | None = None,
) -> list[dict]:
    content = download_stored_brochure(metadata_row)
    text = extract_pdf_text_from_bytes(content)
    parsed = parse_brochure_text(text, institution_records=institution_records)
    field_value = metadata_row.get("field_value") or {}
    metadata = field_value.get("value") or {}
    source_url = metadata_row.get("source_url") or metadata.get("url")
    captured_at = datetime.now(timezone.utc).isoformat()
    return build_fact_rows(
        insurer=metadata_row["insurer"],
        plan_slug=metadata_row["plan_slug"],
        source_url=source_url,
        parsed_facts=parsed,
        captured_at=captured_at,
    )


def parse_stored_brochures(insurers: list[str] | None = None, max_brochures: int | None = None):
    rows = fetch_brochure_metadata_rows(insurers=insurers)
    if max_brochures is not None:
        rows = rows[:max_brochures]

    try:
        institution_records = load_institution_records_from_store()
    except Exception as error:
        institution_records = []
        print(f"MOH institution normalization unavailable: {error}")

    parsed_rows = []
    for row in rows:
        try:
            parsed_rows.extend(parse_brochure_metadata_row(row, institution_records))
        except Exception as error:
            print(
                "Brochure parse failed for " f"{row.get('insurer')}/{row.get('plan_slug')}: {error}"
            )
    return parsed_rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--insurers", help="Comma-separated insurer keys.")
    parser.add_argument("--max-brochures", type=int)
    args = parser.parse_args()

    insurers = (
        [item.strip() for item in args.insurers.split(",") if item.strip()]
        if args.insurers
        else None
    )

    initialize_data_store()
    if args.dry_run and helper.data_store is None:
        print(json.dumps({"plan_fact_count": 0}, indent=2, sort_keys=True))
        return

    rows = parse_stored_brochures(insurers=insurers, max_brochures=args.max_brochures)
    print(json.dumps({"plan_fact_count": len(rows)}, indent=2, sort_keys=True))

    if args.dry_run:
        return

    for row in rows:
        helper.upsert_plan_fact(row)


if __name__ == "__main__":
    main()
