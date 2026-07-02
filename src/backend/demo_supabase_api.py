from __future__ import annotations

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware

from src.backend.demo_data import demo_tables

app = FastAPI(title="Be-sure-ance local Supabase demo")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "PATCH", "OPTIONS"],
    allow_headers=["*"],
)

TABLES = demo_tables()


@app.get("/rest/v1/{table_name}")
def select_rows(table_name: str, request: Request):
    rows = filtered_rows(table_name, request)
    limit = request.query_params.get("limit")
    if limit and limit.isdigit():
        rows = rows[: int(limit)]
    return rows


@app.post("/rest/v1/{table_name}")
async def insert_rows(table_name: str, request: Request):
    table = require_table(table_name)
    payload = await request.json()
    rows = payload if isinstance(payload, list) else [payload]
    table.extend(rows)
    return rows


@app.patch("/rest/v1/{table_name}")
async def update_rows(table_name: str, request: Request):
    table = require_table(table_name)
    payload = await request.json()
    updated_rows = []
    for index, row in enumerate(table):
        if row_matches(row, request):
            table[index] = {**row, **payload}
            updated_rows.append(table[index])
    return updated_rows


def filtered_rows(table_name: str, request: Request):
    return [row for row in require_table(table_name) if row_matches(row, request)]


def require_table(table_name: str):
    if table_name not in TABLES:
        raise HTTPException(status_code=404, detail=f"Unknown demo table: {table_name}")
    return TABLES[table_name]


def row_matches(row: dict, request: Request) -> bool:
    for key, value in request.query_params.multi_items():
        if key in {"select", "limit", "offset", "order"}:
            continue
        if value.startswith("eq.") and str(row.get(key)) != value[3:]:
            return False
    return True
