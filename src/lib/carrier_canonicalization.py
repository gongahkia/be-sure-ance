from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from urllib.parse import quote, urljoin

import requests
from bs4 import BeautifulSoup
from rapidfuzz import fuzz

import src.backend.helper as helper
from src.lib.http_identity import BOT_USER_AGENT

MAS_FID_INSURANCE_URL = "https://eservices.mas.gov.sg/fid/institution?sector=Insurance"
LIA_MEMBER_COMPANIES_URL = "https://www.lia.org.sg/about-us/member-companies/"
MATCHED_STATUS = "matched"
NEEDS_REVIEW_STATUS = "needs_review"
UNMATCHED_STATUS = "unmatched"
MATCH_THRESHOLD = 92
REVIEW_THRESHOLD = 75

TRACKED_CARRIERS = {
    "aia": {
        "display_name": "AIA Singapore",
        "aliases": ("AIA Singapore Private Limited", "AIA Singapore", "AIA"),
    },
    "china_life": {
        "display_name": "China Life Singapore",
        "aliases": ("China Life Insurance (Singapore) Pte. Ltd.", "China Life Singapore"),
    },
    "chubb": {
        "display_name": "Chubb Singapore",
        "aliases": ("Chubb Insurance Singapore", "Chubb Singapore", "Chubb"),
    },
    "great_eastern": {
        "display_name": "Great Eastern Singapore",
        "aliases": (
            "The Great Eastern Life Assurance Company Limited",
            "Great Eastern Life Assurance",
            "Great Eastern Singapore",
        ),
    },
    "hsbc": {
        "display_name": "HSBC Life Singapore",
        "aliases": ("HSBC Life (Singapore) Pte. Ltd.", "HSBC Life Singapore", "HSBC"),
    },
    "iii": {
        "display_name": "India International Insurance Singapore",
        "aliases": (
            "India International Insurance Pte Ltd",
            "India International Insurance Singapore",
        ),
    },
    "singlife": {
        "display_name": "Singlife",
        "aliases": ("Singapore Life Ltd.", "Singlife", "Singapore Life"),
    },
    "sunlife": {
        "display_name": "Sun Life Singapore",
        "aliases": (
            "Sun Life Assurance Company of Canada Singapore Branch",
            "Sun Life Assurance Company of Canada, Singapore Branch",
            "Sun Life Singapore",
        ),
    },
    "tokio_marine": {
        "display_name": "Tokio Marine Singapore",
        "aliases": (
            "Tokio Marine Life Insurance Singapore Pte. Ltd.",
            "Tokio Marine Insurance Singapore Ltd",
            "Tokio Marine Singapore",
        ),
    },
    "uoi": {
        "display_name": "United Overseas Insurance",
        "aliases": ("United Overseas Insurance Limited", "UOI"),
    },
}


@dataclass(frozen=True)
class SourceCarrierRecord:
    name: str
    source_type: str
    source_url: str
    detail_url: str = ""
    licence_types: tuple[str, ...] = ()
    member_category: str = ""

    def as_source_row(self) -> dict:
        return {
            "name": self.name,
            "source_type": self.source_type,
            "source_url": self.source_url,
            "detail_url": self.detail_url,
            "licence_types": list(self.licence_types),
            "member_category": self.member_category,
        }


@dataclass(frozen=True)
class CarrierCanonicalRecord:
    carrier_key: str
    display_name: str
    canonical_name: str
    aliases: tuple[str, ...]
    mas_entity_name: str
    mas_detail_url: str
    mas_licence_types: tuple[str, ...]
    mas_match_status: str
    lia_member_name: str
    lia_member_url: str
    lia_member_category: str
    lia_match_status: str
    source_urls: tuple[str, ...]
    mismatch_flags: tuple[str, ...] = ()
    scraped_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def as_row(self) -> dict:
        return {
            "carrier_key": self.carrier_key,
            "display_name": self.display_name,
            "canonical_name": self.canonical_name,
            "aliases": list(self.aliases),
            "mas_entity_name": self.mas_entity_name,
            "mas_detail_url": self.mas_detail_url,
            "mas_licence_types": list(self.mas_licence_types),
            "mas_match_status": self.mas_match_status,
            "lia_member_name": self.lia_member_name,
            "lia_member_url": self.lia_member_url,
            "lia_member_category": self.lia_member_category,
            "lia_match_status": self.lia_match_status,
            "source_urls": list(self.source_urls),
            "mismatch_flags": list(self.mismatch_flags),
            "scraped_at": self.scraped_at,
            "last_verified_at": self.scraped_at,
        }


def fetch_text(url: str, session=None, timeout: int = 30) -> str:
    client = session or requests
    response = client.get(url, timeout=timeout, headers={"User-Agent": BOT_USER_AGENT})
    response.raise_for_status()
    return response.text


def parse_mas_fid_records(
    html: str, source_url: str = MAS_FID_INSURANCE_URL
) -> list[SourceCarrierRecord]:
    soup = BeautifulSoup(html, "html.parser")
    records = []
    for link in soup.find_all("a", href=True):
        href = link.get("href") or ""
        if "/fid/institution/detail/" not in href:
            continue
        name = normalize_whitespace(link.get_text(" ", strip=True))
        if not name:
            continue
        card = link.find_parent("div", class_="inner") or link.parent
        category = card.find("div", class_="category") if card else None
        licence_types = tuple(
            normalize_whitespace(item)
            for item in (category.get_text("|", strip=True).split("|") if category else [])
            if normalize_whitespace(item)
        )
        records.append(
            SourceCarrierRecord(
                name=name,
                source_type="mas_fid",
                source_url=source_url,
                detail_url=urljoin("https://eservices.mas.gov.sg", href),
                licence_types=licence_types,
            )
        )
    return dedupe_source_records(records)


def parse_lia_member_records(html: str, source_url: str = LIA_MEMBER_COMPANIES_URL):
    soup = BeautifulSoup(html, "html.parser")
    ordinary_header = soup.find(string=re.compile(r"Ordinary Members", re.IGNORECASE))
    if not ordinary_header:
        return []

    records = []
    category = "Ordinary Members"
    for node in ordinary_header.find_parent().find_all_next(["a", "h3"]):
        text = normalize_whitespace(node.get_text(" ", strip=True))
        if node.name == "h3":
            if re.search(r"Associate Members", text, re.IGNORECASE):
                break
            category = text or category
            continue
        href = node.get("href") or ""
        if not text or href.startswith("/"):
            continue
        records.append(
            SourceCarrierRecord(
                name=text,
                source_type="lia_member_directory",
                source_url=source_url,
                detail_url=href,
                member_category=category,
            )
        )
    return dedupe_source_records(records)


def fetch_mas_records_for_tracked_carriers(session=None) -> list[SourceCarrierRecord]:
    records = []
    for carrier in TRACKED_CARRIERS.values():
        query = quote(carrier["aliases"][0])
        source_url = f"{MAS_FID_INSURANCE_URL}&term={query}"
        try:
            records.extend(
                parse_mas_fid_records(fetch_text(source_url, session=session), source_url)
            )
        except Exception as error:
            print(f"carrier_canonicalization: MAS FID unavailable for {query}: {error}")
    return dedupe_source_records(records)


def build_canonical_records(
    mas_records: list[SourceCarrierRecord],
    lia_records: list[SourceCarrierRecord],
    scraped_at: str | None = None,
) -> list[CarrierCanonicalRecord]:
    scraped_at = scraped_at or datetime.now(timezone.utc).isoformat()
    canonical_records = []
    for carrier_key, carrier in TRACKED_CARRIERS.items():
        aliases = unique_preserving_order([carrier["display_name"], *carrier["aliases"]])
        mas_match = best_source_match(aliases, mas_records, "mas_fid")
        lia_match = best_source_match(aliases, lia_records, "lia_member_directory")
        mas_record, mas_status = mas_match
        lia_record, lia_status = lia_match
        canonical_name = (
            mas_record.name
            if mas_status == MATCHED_STATUS and mas_record
            else (
                lia_record.name
                if lia_status == MATCHED_STATUS and lia_record
                else carrier["display_name"]
            )
        )
        mismatch_flags = mismatch_flags_for(mas_record, mas_status, lia_record, lia_status)
        source_urls = unique_preserving_order(
            [
                MAS_FID_INSURANCE_URL,
                LIA_MEMBER_COMPANIES_URL,
                *(record.source_url for record in (mas_record, lia_record) if record),
            ]
        )
        canonical_records.append(
            CarrierCanonicalRecord(
                carrier_key=carrier_key,
                display_name=carrier["display_name"],
                canonical_name=canonical_name,
                aliases=tuple(aliases),
                mas_entity_name=mas_record.name if mas_record else "",
                mas_detail_url=mas_record.detail_url if mas_record else "",
                mas_licence_types=mas_record.licence_types if mas_record else (),
                mas_match_status=mas_status,
                lia_member_name=lia_record.name if lia_record else "",
                lia_member_url=lia_record.detail_url if lia_record else "",
                lia_member_category=lia_record.member_category if lia_record else "",
                lia_match_status=lia_status,
                source_urls=tuple(source_urls),
                mismatch_flags=tuple(mismatch_flags),
                scraped_at=scraped_at,
            )
        )
    return canonical_records


def best_source_match(
    aliases: list[str], records: list[SourceCarrierRecord], source_type: str
) -> tuple[SourceCarrierRecord | None, str]:
    candidates = [record for record in records if record.source_type == source_type]
    best_record = None
    best_score = 0
    best_alias = ""
    best_exact = False
    for record in candidates:
        record_key = match_key(record.name)
        for alias in aliases:
            exact = exact_key(alias) == exact_key(record.name)
            score = 100 if exact else fuzz.token_set_ratio(match_key(alias), record_key)
            if score > best_score or (score == best_score and exact and not best_exact):
                best_record = record
                best_score = score
                best_alias = alias
                best_exact = exact

    if not best_record:
        return None, UNMATCHED_STATUS
    if best_score >= MATCH_THRESHOLD:
        if not best_exact and len(match_key(best_alias)) <= 6:
            return best_record, NEEDS_REVIEW_STATUS
        return best_record, MATCHED_STATUS
    if best_score >= REVIEW_THRESHOLD:
        return best_record, NEEDS_REVIEW_STATUS
    return None, UNMATCHED_STATUS


def mismatch_flags_for(
    mas_record: SourceCarrierRecord | None,
    mas_status: str,
    lia_record: SourceCarrierRecord | None,
    lia_status: str,
) -> list[str]:
    flags = []
    if mas_status != MATCHED_STATUS:
        flags.append(f"mas_{mas_status}")
    if lia_status != MATCHED_STATUS:
        flags.append(f"lia_{lia_status}")
    if mas_record and lia_record:
        score = fuzz.token_set_ratio(match_key(mas_record.name), match_key(lia_record.name))
        if score < REVIEW_THRESHOLD:
            flags.append("mas_lia_name_mismatch")
    return flags


def dedupe_source_records(records: list[SourceCarrierRecord]) -> list[SourceCarrierRecord]:
    seen = set()
    deduped = []
    for record in records:
        key = (record.source_type, record.name, record.detail_url)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(record)
    return deduped


def normalize_whitespace(value: str | None) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def match_key(value: str) -> str:
    normalized = normalize_whitespace(value).lower().replace("&", "and")
    normalized = re.sub(
        r"\b(pte|ltd|limited|private|company|co|singapore|branch)\b", " ", normalized
    )
    return re.sub(r"[^a-z0-9]+", " ", normalized).strip()


def exact_key(value: str) -> str:
    normalized = normalize_whitespace(value).lower().replace("&", "and")
    return re.sub(r"[^a-z0-9]+", " ", normalized).strip()


def unique_preserving_order(values) -> list[str]:
    seen = set()
    unique = []
    for value in values:
        text = normalize_whitespace(value)
        key = text.lower()
        if not text or key in seen:
            continue
        seen.add(key)
        unique.append(text)
    return unique


def ingest_canonical_records(rows: list[dict]):
    helper.require_write_key()
    helper.require_client().table("carrier_canonical_names").upsert(
        rows, on_conflict="carrier_key"
    ).execute()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    helper.initialize_supabase()
    lia_records = parse_lia_member_records(fetch_text(LIA_MEMBER_COMPANIES_URL))
    mas_records = fetch_mas_records_for_tracked_carriers()
    rows = [record.as_row() for record in build_canonical_records(mas_records, lia_records)]
    print(
        json.dumps(
            {
                "carrier_canonical_record_count": len(rows),
                "matched_mas_count": sum(row["mas_match_status"] == MATCHED_STATUS for row in rows),
                "matched_lia_count": sum(row["lia_match_status"] == MATCHED_STATUS for row in rows),
                "mismatch_flag_count": sum(bool(row["mismatch_flags"]) for row in rows),
            },
            indent=2,
            sort_keys=True,
        )
    )
    if not args.dry_run:
        ingest_canonical_records(rows)


if __name__ == "__main__":
    main()
