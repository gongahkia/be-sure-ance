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
        overwrite_table_data(table_name, data)


def overwrite_table_data(table_name, data):
    query = f"DELETE FROM {table_name};"
    try:
        response = supabase.rpc("execute_sql", {"query": query}).execute()
        if response.error:
            print(f"Error clearing data from {table_name}: {response.error}")
    except Exception as e:
        print(f"An error occurred while clearing data from {table_name}: {e}")
    insert_data(table_name, data)


def insert_data(table_name, data):
    formatted_data = [
        {
            "plan_name": row[0]["plan_name"],
            "plan_benefits": row[0]["plan_benefits"],
            "plan_description": row[0]["plan_description"],
            "plan_overview": row[0]["plan_overview"],
            "plan_url": row[0]["plan_url"],
            "product_brochure_url": row[0]["product_brochure_url"],
        }
        for row in data
    ]
    print(formatted_data)
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
