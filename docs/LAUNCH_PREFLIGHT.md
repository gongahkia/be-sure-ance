# Launch Pre-Flight Runbook

Current status: staging pre-flight automation is ready, but no public launch is approved.

Compliance lawyer sign-off status: blocked - not obtained as of 2026-07-02.

No public launch may proceed until the staging checks pass against the real `STAGING_ORIGIN`, the deployment runbook has a working production URL, and the compliance sign-off status changes to approved in private legal records.

## Staging Origin

Set one of:

- GitHub Actions variable `STAGING_ORIGIN`
- Manual workflow input `staging_origin`

The value must be an absolute staging origin such as `https://staging.example.com`.

## Smoke Routes

The `staging-preflight` workflow checks these routes:

- `/`
- `/matrix/panel-hospitals`
- `/status`
- `/share/11111111-2222-4333-8444-555555555555`
- `/sitemap.xml`
- `/robots.txt`

Run locally against staging:

```sh
python scripts/staging_preflight.py --origin "$STAGING_ORIGIN" --output output/staging-preflight/preflight.json
```

All routes must return a non-empty 2xx or 3xx response.

## Free-Tier Load Check

The default load check is intentionally small:

```sh
python scripts/staging_preflight.py \
  --origin "$STAGING_ORIGIN" \
  --load-path /status \
  --load-requests 24 \
  --load-concurrency 3 \
  --max-p95-ms 1500
```

This is a readiness smoke, not a stress test. Do not raise traffic beyond free-tier limits without a separate capacity plan.

## Lighthouse Gate

The `staging-preflight` workflow runs Lighthouse on:

- `/`
- `/matrix/panel-hospitals`
- `/status`
- `/share/11111111-2222-4333-8444-555555555555`

Required categories:

- Performance >= 90
- Accessibility >= 90
- Best Practices >= 90
- SEO >= 90

The workflow parses Lighthouse JSON with:

```sh
python scripts/lighthouse_score_gate.py output/staging-preflight/lighthouse-*.json --minimum 0.9
```

## Security Checklist

The staging pre-flight checks HTTP security headers on `/`:

- `Content-Security-Policy`
- `X-Content-Type-Options: nosniff`
- `Referrer-Policy`
- `Permissions-Policy`
- `Strict-Transport-Security` for HTTPS staging origins

Database lockdown must also be rerun before launch:

```sql
select proname from pg_proc where proname = 'execute_sql';
select table_name, privilege_type
from information_schema.role_table_grants
where grantee in ('anon', 'authenticated')
  and privilege_type in ('INSERT', 'UPDATE', 'DELETE', 'TRUNCATE', 'REFERENCES', 'TRIGGER');
select tablename, policyname, cmd, roles
from pg_policies
where schemaname = 'public';
```

Expected result:

- `execute_sql` is absent.
- `anon` and `authenticated` do not have write grants on public tables.
- Public read policies expose only display-safe rows and columns.

## Compliance Sign-Off

Before launch, obtain Singapore fintech/compliance lawyer review of:

- live user-facing copy and disclaimers
- scraper behavior, robots.txt handling, and source-owner takedown path
- Supabase RLS and public anon-read surface
- hosting logs, analytics, Sentry, and retention settings
- Telegram bot launch scope if enabled

Keep legal notes and sign-off evidence outside the repository. This repo should record only the status and date, not private legal advice.

## Evidence

Store workflow artifacts from `staging-preflight`:

- `preflight.json`
- `lighthouse-workspace.json`
- `lighthouse-matrix.json`
- `lighthouse-status.json`
- `lighthouse-share.json`

No public launch is approved while any pre-flight check fails or compliance sign-off remains blocked.
