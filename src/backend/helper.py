# ----- required imports -----

import os
import json
from dotenv import load_dotenv
from supabase import create_client, Client

# ------ functions ------


def initialize_supabase():
    load_dotenv()
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise ValueError("Supabase URL or Key is missing. Check your .env file.")
    global supabase
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    print("Supabase client initialized successfully.")


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
        table_exists = check_table_exists(table_name)
        if table_exists:
            overwrite_table_data(table_name, data)
        else:
            create_table(table_name)
            insert_data(table_name, data)


def check_table_exists(table_name):
    query = f"""
    SELECT EXISTS (
        SELECT 1
        FROM pg_tables
        WHERE tablename = '{table_name}'
    );
    """
    response = supabase.rpc("execute_sql", {"query": query}).execute()
    return response.data[0][0]


def create_table(table_name):
    sql_create_table = f"""
    CREATE TABLE IF NOT EXISTS {table_name} (
        id SERIAL PRIMARY KEY,
        plan_name TEXT,
        plan_benefits TEXT[],
        plan_description TEXT,
        plan_overview TEXT,
        plan_url TEXT,
        product_brochure_url TEXT
    );
    """
    response = supabase.rpc("execute_sql", {"query": sql_create_table}).execute()
    if response.error:
        print(f"Error creating table {table_name}: {response.error}")
    else:
        print(f"Table {table_name} created successfully.")


def overwrite_table_data(table_name, data):
    response_delete = supabase.table(table_name).delete().execute()
    if response_delete.error:
        print(f"Error clearing data from {table_name}: {response_delete.error}")
    insert_data(table_name, data)


def insert_data(table_name, data):
    formatted_data = [
        {
            "plan_name": row["plan_name"],
            "plan_benefits": row["plan_benefits"],
            "plan_description": row["plan_description"],
            "plan_overview": row["plan_overview"],
            "plan_url": row["plan_url"],
            "product_brochure_url": row["product_brochure_url"],
        }
        for row in data
    ]
    response_insert = supabase.table(table_name).insert(formatted_data).execute()
    if response_insert.error:
        print(f"Error inserting data into {table_name}: {response_insert.error}")
    else:
        print(f"Data inserted successfully into {table_name}.")


# ----- sample execution code -----

if __name__ == "__main__":
    initialize_supabase()
    target_directory = "./scraped"
    process_json_files(target_directory)
