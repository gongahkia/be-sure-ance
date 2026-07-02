from __future__ import annotations

import argparse
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path

RETENTION_DAYS = 30


def timestamp_slug(now: datetime | None = None) -> str:
    now = now or datetime.now(timezone.utc)
    return now.strftime("%Y-%m-%dT%H-%M-%SZ")


def artifact_paths(output_dir: Path, stamp: str) -> tuple[Path, Path]:
    prefix = f"be-sure-ance-supabase-logical-dump-{stamp}"
    return output_dir / f"{prefix}.dump", output_dir / f"{prefix}.manifest.json"


def create_demo_dump(output_dir: Path, stamp: str | None = None) -> tuple[Path, Path]:
    stamp = stamp or timestamp_slug()
    dump_path, manifest_path = artifact_paths(output_dir, stamp)
    output_dir.mkdir(parents=True, exist_ok=True)
    dump_path.write_text(
        "\n".join(
            (
                "-- demo logical dump artifact",
                "-- generated without database credentials",
                "CREATE SCHEMA IF NOT EXISTS public;",
                "CREATE TABLE IF NOT EXISTS public.backup_smoke_test (id integer);",
                "",
            )
        )
    )
    write_manifest(manifest_path, dump_path, stamp, mode="demo")
    return dump_path, manifest_path


def create_pg_dump(
    output_dir: Path, database_url: str, stamp: str | None = None
) -> tuple[Path, Path]:
    if not database_url:
        raise ValueError("SUPABASE_DB_URL is required unless --demo is used.")

    stamp = stamp or timestamp_slug()
    dump_path, manifest_path = artifact_paths(output_dir, stamp)
    output_dir.mkdir(parents=True, exist_ok=True)
    command = [
        "pg_dump",
        "--format=custom",
        "--no-owner",
        "--no-privileges",
        "--file",
        str(dump_path),
        database_url,
    ]
    subprocess.run(command, check=True, capture_output=True, text=True)
    write_manifest(manifest_path, dump_path, stamp, mode="pg_dump")
    return dump_path, manifest_path


def write_manifest(manifest_path: Path, dump_path: Path, stamp: str, mode: str) -> None:
    manifest = {
        "project": "be-sure-ance",
        "artifact": dump_path.name,
        "generated_at": stamp,
        "mode": mode,
        "retention_days": RETENTION_DAYS,
        "contains_application_pii": False,
        "contains_secrets": False,
        "restore_command": 'pg_restore --clean --if-exists --no-owner --no-privileges --dbname "$RESTORE_DATABASE_URL" <artifact>',
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=Path(".backup-output"))
    parser.add_argument("--database-url", default=os.getenv("SUPABASE_DB_URL", ""))
    parser.add_argument("--stamp", default="")
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Create a local smoke-test artifact without database credentials.",
    )
    args = parser.parse_args()

    if args.demo:
        dump_path, manifest_path = create_demo_dump(args.output_dir, stamp=args.stamp or None)
    else:
        dump_path, manifest_path = create_pg_dump(
            args.output_dir,
            args.database_url,
            stamp=args.stamp or None,
        )

    print(f"backup_artifact={dump_path}")
    print(f"backup_manifest={manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
