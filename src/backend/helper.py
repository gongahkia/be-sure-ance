# ----- required imports -----

import base64
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
from supabase import create_client

from src.lib.http_identity import BOT_USER_AGENT

# ------ functions ------


supabase = None
_supabase_key = None
DEFAULT_BROCHURE_STORAGE_BUCKET = "plan-brochures"
BROCHURE_CAPTURE_FIELD = "brochure_metadata"
BROCHURE_REQUEST_TIMEOUT_SECONDS = 30
MAX_BROCHURE_BYTES = 20 * 1024 * 1024
BROCHURE_USER_AGENT = BOT_USER_AGENT


def initialize_supabase():
    if dry_run_enabled():
        print("Dry run enabled; Supabase client not initialized.")
        return
    load_dotenv()
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_SERVER_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_SECRET_KEY")
    if not SUPABASE_URL or not SUPABASE_SERVER_KEY:
        raise ValueError(
            "Supabase URL or server-side service/secret key is missing. Check your .env file."
        )
    global supabase, _supabase_key
    _supabase_key = SUPABASE_SERVER_KEY
    supabase = create_client(SUPABASE_URL, SUPABASE_SERVER_KEY)
    print("Supabase client initialized successfully.")


def key_has_write_access(key):
    if not key:
        return False
    if key.startswith("sb_secret_"):
        return True

    parts = key.split(".")
    if len(parts) < 2:
        return False

    try:
        padded_payload = parts[1] + "=" * (-len(parts[1]) % 4)
        payload = json.loads(base64.urlsafe_b64decode(padded_payload))
    except Exception:
        return False

    return payload.get("role") == "service_role"


def require_write_key():
    if not key_has_write_access(_supabase_key):
        raise PermissionError("Supabase writes require a server-side secret/service_role key.")


def require_client():
    if supabase is None:
        raise RuntimeError("Supabase client is not initialized.")
    return supabase


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
    if dry_run_enabled():
        print(f"Dry run enabled; skipping Supabase plan writes for {insurer}.")
        return

    require_write_key()
    formatted_rows = format_plan_rows(insurer, rows)
    clear_plans_for_insurer(insurer)
    if not formatted_rows:
        print(f"No plan rows to insert for {insurer}.")
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
        print(f"Dry run enabled; skipping Supabase writes for {table_name}.")
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
    initialize_supabase()
    target_directory = "./scraped"
    process_json_files(target_directory)
