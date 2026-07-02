# Backup And Retention

## Scope

The `nightly-supabase-backup` workflow creates a Supabase Postgres logical dump once per night and stores it as a GitHub Actions artifact with 30-day retention.

If R2 credentials are configured, the same artifact is copied to the configured R2 bucket path:

```text
s3://<R2_BACKUP_BUCKET>/be-sure-ance/supabase-logical-dumps/
```

No production deployment is required for the backup workflow.

## Required Secrets

Do not commit these values.

- `SUPABASE_DB_URL`: Supabase Postgres connection string for `pg_dump`.

Optional R2 copy:

- `R2_ENDPOINT_URL`
- `R2_BACKUP_BUCKET`
- `R2_ACCESS_KEY_ID`
- `R2_SECRET_ACCESS_KEY`

## Artifact Contents

Each run writes:

- `be-sure-ance-supabase-logical-dump-<timestamp>.dump`
- `be-sure-ance-supabase-logical-dump-<timestamp>.manifest.json`

The dump uses:

```sh
pg_dump --format=custom --no-owner --no-privileges
```

The manifest records artifact name, timestamp, mode, and retention days. It must not contain credentials.

## Restore Procedure

Restore only into a clean staging database unless an incident commander explicitly approves production restore.

1. Download the GitHub Actions artifact or R2 object.
2. Set a private local restore URL:

   ```sh
   export RESTORE_DATABASE_URL='<staging-postgres-url>'
   ```

3. Restore:

   ```sh
   pg_restore --clean --if-exists --no-owner --no-privileges \
     --dbname "$RESTORE_DATABASE_URL" \
     be-sure-ance-supabase-logical-dump-<timestamp>.dump
   ```

4. Run schema and smoke checks:

   ```sh
   python -m unittest discover -s tests -p "test_*.py"
   ```

5. Verify public reads still use anon SELECT-only RLS and writes still require server-side credentials.

## Retention Policy

- GitHub Actions artifacts: 30 days.
- R2 backup copies: configure lifecycle expiry to 30 days.
- Local downloaded dumps: delete after restore verification unless they are needed for an active incident.

## Local Smoke Test

The script has a no-secret demo mode for testing artifact creation:

```sh
python scripts/supabase_logical_dump.py --demo --output-dir /tmp/be-sure-ance-backup-smoke
```

This creates a small demo dump and manifest without connecting to Supabase.
