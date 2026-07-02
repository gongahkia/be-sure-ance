# ----- required imports -----

import base64
import os
import json
import sys
from dotenv import load_dotenv
from supabase import create_client

# ------ functions ------


supabase = None
_supabase_key = None


def initialize_supabase():
    if dry_run_enabled():
        print("Dry run enabled; Supabase client not initialized.")
        return
    load_dotenv()
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_SERVER_KEY = (
        os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        or os.getenv("SUPABASE_SECRET_KEY")
    )
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
        raise PermissionError(
            "Supabase writes require a server-side secret/service_role key."
        )


def require_client():
    if supabase is None:
        raise RuntimeError("Supabase client is not initialized.")
    return supabase


def process_json_files(target_directory_filepath):
    json_files = [
        file for file in os.listdir(target_directory_filepath) if file.endswith(".json")
    ]
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
    if dry_run_enabled():
        print(f"Dry run enabled; skipping Supabase writes for {table_name}.")
        return
    clear_table_data(table_name)
    if not data:
        print(f"No rows to insert into {table_name}.")
        return
    insert_data(table_name, data)


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


def insert_data(table_name, data):
    require_write_key()
    formatted_data = []
    for row in flatten_rows(data):
        if not isinstance(row, dict):
            raise TypeError(f"Expected row dict, got {type(row).__name__}")
        plan_benefits = row.get("plan_benefits", [])
        if isinstance(plan_benefits, str):
            plan_benefits = [plan_benefits]
        formatted_row = {
            "plan_name": row.get("plan_name"),
            "plan_benefits": plan_benefits,
            "plan_description": row.get("plan_description"),
            "plan_overview": row.get("plan_overview"),
            "plan_url": row.get("plan_url"),
            "product_brochure_url": row.get("product_brochure_url"),
        }
        formatted_data.append(formatted_row)

    response_insert = require_client().table(table_name).insert(formatted_data).execute()
    if response_insert.data is None:
        print(f"Error inserting data into {table_name}: No data returned")
    else:
        print(f"Data inserted successfully into {table_name}.")


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


# ----- sample execution code -----

if __name__ == "__main__":
    initialize_supabase()
    target_directory = "./scraped"
    process_json_files(target_directory)
