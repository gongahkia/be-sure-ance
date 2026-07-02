from __future__ import annotations

import json
import os
import re
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any

DEFAULT_DATA_DIR = Path("src/be-sure-ance-app/public/data")


@dataclass
class LocalDataResponse:
    data: Any


class LocalStorageBucket:
    def __init__(self, root: Path, bucket: str):
        self.root = root
        self.bucket = bucket

    def upload(self, key: str, content: bytes, file_options: dict | None = None):
        path = self.root / self.bucket / safe_storage_key(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        return LocalDataResponse({"path": key, "bucket": self.bucket})

    def download(self, key: str) -> bytes:
        return (self.root / self.bucket / safe_storage_key(key)).read_bytes()


class LocalStorage:
    def __init__(self, root: Path):
        self.root = root

    def from_(self, bucket: str) -> LocalStorageBucket:
        return LocalStorageBucket(self.root, bucket)


class LocalDataClient:
    def __init__(self, data_dir: Path | str | None = None):
        self.data_dir = Path(data_dir or default_data_dir())
        self.tables_dir = self.data_dir / "tables"
        self.storage = LocalStorage(self.data_dir / "storage")
        self.tables_dir.mkdir(parents=True, exist_ok=True)

    def table(self, table_name: str) -> "LocalTableQuery":
        return LocalTableQuery(self, table_name)

    def table_path(self, table_name: str) -> Path:
        if not re.fullmatch(r"[a-zA-Z0-9_]+", table_name):
            raise ValueError(f"Unsupported table name: {table_name}")
        return self.tables_dir / f"{table_name}.json"

    def read_table(self, table_name: str) -> list[dict]:
        path = self.table_path(table_name)
        if not path.exists():
            return []
        payload = json.loads(path.read_text())
        if not isinstance(payload, list):
            raise ValueError(f"Expected list payload in {path}")
        return [row for row in payload if isinstance(row, dict)]

    def write_table(self, table_name: str, rows: list[dict]) -> None:
        path = self.table_path(table_name)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(rows, indent=2, sort_keys=True, ensure_ascii=False) + "\n")

    def reset(self) -> None:
        if self.data_dir.exists():
            shutil.rmtree(self.data_dir)
        self.tables_dir.mkdir(parents=True, exist_ok=True)


class LocalTableQuery:
    def __init__(self, client: LocalDataClient, table_name: str):
        self.client = client
        self.table_name = table_name
        self.filters: list[tuple[str, str, Any]] = []
        self.selected_columns: list[str] | None = None
        self.order_column = ""
        self.order_desc = False
        self.limit_count: int | None = None
        self.operation = "select"
        self.payload: Any = None
        self.on_conflict = ""

    def select(self, columns: str = "*"):
        self.operation = "select"
        if columns and columns != "*":
            self.selected_columns = [
                column.strip() for column in columns.split(",") if column.strip()
            ]
        return self

    def eq(self, column: str, value: Any):
        self.filters.append(("eq", column, value))
        return self

    def neq(self, column: str, value: Any):
        self.filters.append(("neq", column, value))
        return self

    def order(self, column: str, desc: bool = False):
        self.order_column = column
        self.order_desc = desc
        return self

    def limit(self, count: int):
        self.limit_count = count
        return self

    def delete(self):
        self.operation = "delete"
        return self

    def insert(self, rows):
        self.operation = "insert"
        self.payload = rows
        return self

    def update(self, values: dict):
        self.operation = "update"
        self.payload = values
        return self

    def upsert(self, rows, on_conflict: str | None = None):
        self.operation = "upsert"
        self.payload = rows
        self.on_conflict = on_conflict or ""
        return self

    def execute(self) -> LocalDataResponse:
        rows = self.client.read_table(self.table_name)
        if self.operation == "select":
            return LocalDataResponse(self.apply_read_projection(rows))
        if self.operation == "delete":
            kept = [row for row in rows if not self.matches(row)]
            deleted = [row for row in rows if self.matches(row)]
            self.client.write_table(self.table_name, kept)
            return LocalDataResponse(deleted)
        if self.operation == "insert":
            new_rows = normalize_rows(self.payload)
            self.client.write_table(self.table_name, [*rows, *new_rows])
            return LocalDataResponse(new_rows)
        if self.operation == "update":
            updated = []
            merged = []
            for row in rows:
                if self.matches(row):
                    next_row = {**row, **dict(self.payload or {})}
                    updated.append(next_row)
                    merged.append(next_row)
                else:
                    merged.append(row)
            self.client.write_table(self.table_name, merged)
            return LocalDataResponse(updated)
        if self.operation == "upsert":
            return LocalDataResponse(self.execute_upsert(rows))
        raise ValueError(f"Unsupported local data operation: {self.operation}")

    def execute_upsert(self, rows: list[dict]) -> list[dict]:
        new_rows = normalize_rows(self.payload)
        conflict_columns = [item.strip() for item in self.on_conflict.split(",") if item.strip()]
        if not conflict_columns:
            conflict_columns = ["id"] if any("id" in row for row in new_rows) else []
        merged = list(rows)
        for new_row in new_rows:
            index = find_conflict_index(merged, new_row, conflict_columns)
            if index is None:
                merged.append(new_row)
            else:
                merged[index] = {**merged[index], **new_row}
        self.client.write_table(self.table_name, merged)
        return new_rows

    def apply_read_projection(self, rows: list[dict]) -> list[dict]:
        selected = [row for row in rows if self.matches(row)]
        if self.order_column:
            selected = sorted(
                selected,
                key=lambda row: sort_value(row.get(self.order_column)),
                reverse=self.order_desc,
            )
        if self.limit_count is not None:
            selected = selected[: self.limit_count]
        if self.selected_columns is not None:
            selected = [
                {column: row.get(column) for column in self.selected_columns} for row in selected
            ]
        return selected

    def matches(self, row: dict) -> bool:
        for operator, column, value in self.filters:
            if operator == "eq" and row.get(column) != value:
                return False
            if operator == "neq" and row.get(column) == value:
                return False
        return True


def default_data_dir() -> Path:
    return Path(os.getenv("BE_SURE_ANCE_DATA_DIR") or DEFAULT_DATA_DIR)


def normalize_rows(rows) -> list[dict]:
    if rows is None:
        return []
    if isinstance(rows, dict):
        rows = [rows]
    return [dict(row) for row in rows]


def find_conflict_index(rows: list[dict], new_row: dict, columns: list[str]) -> int | None:
    if not columns:
        return None
    for index, row in enumerate(rows):
        if all(row.get(column) == new_row.get(column) for column in columns):
            return index
    return None


def sort_value(value):
    if value is None:
        return ""
    return str(value)


def safe_storage_key(key: str) -> Path:
    clean_parts = [part for part in str(key).split("/") if part and part not in {".", ".."}]
    if not clean_parts:
        raise ValueError("Storage key must not be empty.")
    return Path(*clean_parts)
