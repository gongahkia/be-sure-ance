# ----- required imports -----

import hashlib
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

import requests
from dotenv import load_dotenv

from src.lib.brochure_versions import (
    build_change_alert,
    build_version_row,
    extract_brochure_text,
    version_change_status,
)
from src.lib.http_identity import BOT_USER_AGENT
from src.lib.local_data_store import LocalDataClient, default_data_dir
from src.lib.observability import initialize_observability
from src.lib.scraper_health import record_scraper_failure, record_scraper_success

# ------ functions ------


data_store = None
injected_client = None
_write_key = "local-data-store"
DEFAULT_BROCHURE_STORAGE_BUCKET = "plan-brochures"
BROCHURE_CAPTURE_FIELD = "brochure_metadata"
BROCHURE_REQUEST_TIMEOUT_SECONDS = 30
MAX_BROCHURE_BYTES = 20 * 1024 * 1024
BROCHURE_USER_AGENT = BOT_USER_AGENT


def initialize_data_store():
    initialize_observability("scraper")
    if dry_run_enabled():
        print("Dry run enabled; local data store not initialized.")
        return
    load_dotenv()
    global data_store, injected_client, _write_key
    data_store = LocalDataClient(default_data_dir())
    injected_client = None
    _write_key = "local-data-store"
    print(f"Local data store initialized at {data_store.data_dir}.")


def key_has_write_access(key):
    return bool(key)


def require_write_key():
    return True


def require_client():
    if injected_client is not None:
        return injected_client
    if data_store is None:
        initialize_data_store()
    if data_store is None:
        raise RuntimeError("Local data store is not initialized.")
    return data_store


def process_json_files(target_directory_filepath):
    json_files = [file for file in os.listdir(target_directory_filepath) if file.endswith(".json")]
    print(f"Files being processed: {json_files}")
    for json_file in json_files:
        table_name = os.path.splitext(json_file)[0]
        file_path = os.path.join(target_directory_filepath, json_file)
        with open(file_path, "r") as file:
            data = json.load(file)
        overwrite_table_data(table_name, data)


def dry_run_enabled(args=None):
    return "--dry-run" in (args if args is not None else sys.argv[1:])


def overwrite_table_data(table_name, data):
    overwrite_plans_for_insurer(table_name, data)


def overwrite_plans_for_insurer(insurer, rows):
    formatted_rows = format_plan_rows(insurer, rows)
    if dry_run_enabled():
        print(
            json.dumps(
                {
                    "dry_run": True,
                    "insurer": insurer,
                    "plan_row_count": len(formatted_rows),
                    "sample_plan_names": [
                        row["plan_name"] for row in formatted_rows[:5] if row.get("plan_name")
                    ],
                },
                indent=2,
                sort_keys=True,
            )
        )
        return

    require_write_key()
    clear_plans_for_insurer(insurer)
    if not formatted_rows:
        print(f"No plan rows to insert for {insurer}.")
        record_scraper_failure(insurer, "no plan rows produced")
        return

    response = (
        require_client()
        .table("plans")
        .upsert(formatted_rows, on_conflict="insurer,plan_slug")
        .execute()
    )
    if response.data is None:
        print(f"Error upserting plans for {insurer}: No data returned")
    else:
        print(f"Plans upserted successfully for {insurer}.")
        capture_brochures_for_plans(insurer, formatted_rows)
        record_scraper_success(insurer, len(formatted_rows))


def clear_plans_for_insurer(insurer):
    require_write_key()
    response = require_client().table("plans").delete().eq("insurer", insurer).execute()
    if response.data is None or response.data == []:
        print(f"Plans cleared for {insurer}: No data returned")
    else:
        print(f"Plans cleared for {insurer}: {response.data}")


def clear_table_data(table_name):
    require_write_key()
    response = require_client().table(table_name).delete().neq("id", 0).execute()
    if response.data is None or response.data == []:
        print(f"Data cleared from {table_name}: No data returned")
    else:
        print(f"Data cleared from {table_name}: {response.data}")


def overwrite_generic_table_data(table_name, data):
    if dry_run_enabled():
        print(
            json.dumps(
                {
                    "dry_run": True,
                    "row_count": len(data or []),
                    "table_name": table_name,
                },
                indent=2,
                sort_keys=True,
            )
        )
        return
    clear_table_data(table_name)
    if not data:
        print(f"No rows to insert into {table_name}.")
        return
    insert_generic_data(table_name, data)


def format_plan_rows(insurer, rows, scraped_at=None):
    scraped_at = scraped_at or datetime.now(timezone.utc).isoformat()
    formatted_rows = []
    slug_counts = {}
    for row in flatten_rows(rows):
        if not isinstance(row, dict):
            raise TypeError(f"Expected row dict, got {type(row).__name__}")
        plan_name = normalize_text(row.get("plan_name"))
        if not plan_name:
            raise ValueError(f"Plan row for {insurer} is missing plan_name.")
        base_slug = slugify(row.get("plan_slug") or plan_name)
        slug_counts[base_slug] = slug_counts.get(base_slug, 0) + 1
        plan_slug = (
            base_slug if slug_counts[base_slug] == 1 else f"{base_slug}-{slug_counts[base_slug]}"
        )
        formatted_row = {
            "insurer": insurer,
            "plan_name": plan_name,
            "plan_slug": plan_slug,
            "plan_benefits": normalize_plan_benefits(row.get("plan_benefits", [])),
            "plan_description": row.get("plan_description"),
            "plan_overview": row.get("plan_overview"),
            "plan_url": row.get("plan_url"),
            "product_brochure_url": row.get("product_brochure_url"),
            "scraped_at": scraped_at,
        }
        formatted_rows.append(formatted_row)
    return formatted_rows


def normalize_text(value):
    if value is None:
        return ""
    return re.sub(r"\s+", " ", str(value)).strip()


def slugify(value):
    slug = re.sub(r"[^a-z0-9]+", "-", normalize_text(value).lower()).strip("-")
    return slug or "plan"


def normalize_plan_benefits(value):
    if not value:
        return []
    if isinstance(value, str):
        return [normalize_text(value)]
    if not isinstance(value, list | tuple):
        return [normalize_text(value)]

    benefits = []
    for item in value:
        if isinstance(item, list | tuple):
            for child in item:
                child_text = normalize_text(child)
                if child_text:
                    benefits.append(child_text)
        else:
            item_text = normalize_text(item)
            if item_text:
                benefits.append(item_text)
    return benefits


def insert_generic_data(table_name, data):
    require_write_key()
    response_insert = require_client().table(table_name).insert(data).execute()
    if response_insert.data is None:
        print(f"Error inserting data into {table_name}: No data returned")
    else:
        print(f"Data inserted successfully into {table_name}.")


def flatten_rows(data):
    rows = []
    for row in data or []:
        if isinstance(row, list):
            rows.extend(row)
        else:
            rows.append(row)
    return rows


def brochure_storage_bucket():
    return os.getenv("BROCHURE_STORAGE_BUCKET") or DEFAULT_BROCHURE_STORAGE_BUCKET


def is_allowed_brochure_url(url):
    if not url:
        return False
    parsed = urlparse(str(url))
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def sha256_bytes(content):
    return hashlib.sha256(content).hexdigest()


def build_brochure_storage_key(insurer, plan_slug, content_hash):
    return f"brochures/{slugify(insurer)}/{slugify(plan_slug)}/{content_hash}.pdf"


def download_brochure(url, session=None, request_timeout=BROCHURE_REQUEST_TIMEOUT_SECONDS):
    if not is_allowed_brochure_url(url):
        raise ValueError(f"Unsupported brochure URL: {url}")

    client = session or requests
    response = client.get(
        url,
        timeout=request_timeout,
        headers={"User-Agent": BROCHURE_USER_AGENT},
    )
    response.raise_for_status()

    content = response.content
    content_type = response.headers.get("content-type", "").split(";")[0].strip().lower()
    path = urlparse(url).path.lower()
    if "pdf" not in content_type and not path.endswith(".pdf"):
        raise ValueError(f"Brochure URL did not return a PDF: {url}")
    if not content:
        raise ValueError(f"Brochure download was empty: {url}")
    if len(content) > MAX_BROCHURE_BYTES:
        raise ValueError(f"Brochure exceeds {MAX_BROCHURE_BYTES} bytes: {url}")

    return {
        "content": content,
        "content_type": content_type or "application/pdf",
        "last_modified_at": response.headers.get("last-modified"),
    }


def upload_brochure_bytes(bucket, storage_key, content, content_type):
    return (
        require_client()
        .storage.from_(bucket)
        .upload(
            storage_key,
            content,
            file_options={
                "content-type": content_type or "application/pdf",
                "upsert": "true",
            },
        )
    )


def build_brochure_metadata_fact(insurer, plan, download, captured_at):
    content = download["content"]
    content_hash = sha256_bytes(content)
    bucket = brochure_storage_bucket()
    storage_key = build_brochure_storage_key(insurer, plan["plan_slug"], content_hash)
    source_url = plan["product_brochure_url"]

    field_value = {
        "status": "known",
        "value": {
            "url": source_url,
            "sha256": content_hash,
            "storage_bucket": bucket,
            "storage_key": storage_key,
            "size_bytes": len(content),
            "content_type": download["content_type"],
            "fetched_at": captured_at,
            "last_modified_at": download["last_modified_at"],
        },
        "raw_text": Path(urlparse(source_url).path).name or "brochure.pdf",
        "notes": [],
    }
    return {
        "insurer": insurer,
        "plan_slug": plan["plan_slug"],
        "field_name": BROCHURE_CAPTURE_FIELD,
        "field_value": field_value,
        "source_url": source_url,
        "source_type": "brochure_pdf",
        "scraped_at": captured_at,
        "last_verified_at": captured_at,
    }


def upsert_plan_fact(row):
    require_write_key()
    response = (
        require_client()
        .table("plan_facts")
        .upsert([row], on_conflict="insurer,plan_slug,field_name")
        .execute()
    )
    if response.data is None:
        print(f"Plan fact upsert returned no data for {row['insurer']}/{row['plan_slug']}.")
    return response


def fetch_latest_brochure_version(insurer, plan_slug, source_url):
    response = (
        require_client()
        .table("brochure_version_history")
        .select("*")
        .eq("insurer", insurer)
        .eq("plan_slug", plan_slug)
        .eq("source_url", source_url)
        .order("captured_at", desc=True)
        .limit(1)
        .execute()
    )
    rows = response.data or []
    return rows[0] if rows else None


def update_brochure_version_seen(version_id, captured_at):
    return (
        require_client()
        .table("brochure_version_history")
        .update({"last_seen_at": captured_at})
        .eq("id", version_id)
        .execute()
    )


def upsert_brochure_version(row):
    return (
        require_client()
        .table("brochure_version_history")
        .upsert([row], on_conflict="insurer,plan_slug,source_url,sha256")
        .execute()
    )


def upsert_brochure_change_alert(row):
    return (
        require_client()
        .table("brochure_change_alerts")
        .upsert(
            [row],
            on_conflict="insurer,plan_slug,source_url,previous_sha256,current_sha256",
        )
        .execute()
    )


def record_brochure_version(insurer, plan, fact_row, content, captured_at):
    metadata = fact_row["field_value"]["value"]
    plan = {
        **plan,
        "plan_name": plan.get("plan_name") or fact_row["plan_slug"],
    }
    previous_version = fetch_latest_brochure_version(
        insurer,
        plan["plan_slug"],
        metadata["url"],
    )
    current_version = build_version_row(
        insurer=insurer,
        plan=plan,
        metadata=metadata,
        captured_at=captured_at,
        extracted_text=extract_brochure_text(content),
    )
    status = version_change_status(previous_version, metadata["sha256"])
    if status == "unchanged":
        if previous_version.get("id") is not None:
            update_brochure_version_seen(previous_version["id"], captured_at)
        return {"status": status, "version": previous_version, "alert": None}

    upsert_brochure_version(current_version)
    alert = None
    if status == "changed":
        alert = build_change_alert(previous_version, current_version, detected_at=captured_at)
        upsert_brochure_change_alert(alert)
    return {"status": status, "version": current_version, "alert": alert}


def capture_brochure_for_plan(insurer, plan, session=None, captured_at=None):
    source_url = plan.get("product_brochure_url")
    if not source_url:
        return None
    captured_at = captured_at or datetime.now(timezone.utc).isoformat()

    try:
        require_write_key()
        download = download_brochure(source_url, session=session)
        fact_row = build_brochure_metadata_fact(insurer, plan, download, captured_at)
        metadata = fact_row["field_value"]["value"]
        upload_brochure_bytes(
            metadata["storage_bucket"],
            metadata["storage_key"],
            download["content"],
            metadata["content_type"],
        )
        upsert_plan_fact(fact_row)
        try:
            record_brochure_version(insurer, plan, fact_row, download["content"], captured_at)
        except Exception as error:
            print(f"Brochure version tracking skipped for {insurer}/{plan['plan_slug']}: {error}")
        print(f"Brochure captured for {insurer}/{plan['plan_slug']}: {metadata['sha256']}")
        return fact_row
    except Exception as error:
        print(f"Brochure capture skipped for {insurer}/{plan.get('plan_slug')}: {error}")
        return None


def capture_brochures_for_plans(insurer, plans, session=None):
    captured = []
    for plan in plans:
        result = capture_brochure_for_plan(insurer, plan, session=session)
        if result:
            captured.append(result)
    return captured


# ----- sample execution code -----

if __name__ == "__main__":
    initialize_data_store()
    target_directory = "./scraped"
    process_json_files(target_directory)
