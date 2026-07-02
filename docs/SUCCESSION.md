# Succession Runbook

Purpose: let another maintainer operate or safely wind down Be-sure-ance without exposing secrets in this repository.

## Ownership

Current maintainer: Gabriel Ong Zhe Mian.

Primary contact: `gabrielzmong@gmail.com`.

## Launch State

No production deployment is claimed during Phases 1-4. Phase 5 is the launch gate.

Before any public relaunch, confirm:

- Supabase RLS and read-only anon access are active.
- `execute_sql` remains dropped.
- No service-role key is present in frontend env.
- README, app copy, and `docs/COMPLIANCE.md` match the live behavior.
- A Singapore fintech/compliance lawyer has reviewed the live product.

## Credential Inventory Locations

Do not store actual secrets in this document.

Expected locations:

- Local development: maintainer-owned `.env` file copied from `.env.example`.
- GitHub Actions: repository or organisation secrets.
- Supabase: project dashboard for database, storage, anon key, and server-side secret/service-role key.
- Telegram beta: BotFather token stored only in local `.env` or GitHub/environment secrets.
- Sentry: project DSN and alert recipients in Sentry project settings and GitHub secrets.
- Hosting provider: Netlify restore is the selected Phase 5 path; Cloudflare Pages remains the fallback if Netlify is blocked.
- Object storage: Supabase Storage bucket settings or future R2 bucket settings.
- Backup database URL: GitHub Actions secret `SUPABASE_DB_URL`.
- Optional backup mirror: R2 endpoint, bucket, access key, and secret key in GitHub Actions secrets or variables.

Never commit:

- `SUPABASE_SECRET_KEY`
- `SUPABASE_SERVICE_ROLE_KEY`
- `TELEGRAM_BOT_TOKEN`
- `SENTRY_DSN`
- `SUPABASE_DB_URL`
- `R2_SECRET_ACCESS_KEY`
- hosting deploy tokens
- database passwords
- private legal/compliance notes

The public `VITE_SUPABASE_ANON_KEY` and optional `VITE_SENTRY_DSN` can be present in frontend build settings, but must not imply write access.

## Weekly Operations

1. Check GitHub Actions for `scrape-to-supabase`, `validate-scraper-snapshots`, `publish-open-dataset`, and CI.
2. Check `nightly-supabase-backup` for a fresh 30-day artifact and optional R2 copy.
3. Review `/status` for stale, failing, unsupported, or validation-failed carriers.
4. Triage `brochure_change_alerts` rows before dispatching any public alert.
5. Check Sentry for new frontend or scraper error groups if DSNs are configured.
6. Confirm open dataset artifacts were generated and do not include secret-like fields.

## Backup Restore

Use [Backup and retention](./BACKUP_RETENTION.md) for logical dump creation, retention, and restore steps.

Default retention is 30 days for GitHub Actions artifacts and any configured R2 lifecycle rule.

## Takedown Flow

1. Acknowledge credible carrier or rights-holder requests within 2 business days.
2. Suppress disputed source rows, plan facts, brochure objects, or alerts while reviewing.
3. Resolve or provide written status within 7 calendar days.
4. Keep private notes outside the repo with source URL, requestor, action, and date.

## Scraper Failure Flow

1. Check `/status` for last success, last failure, row count, and validation status.
2. Open validation artifacts from the latest GitHub Actions run.
3. Reproduce locally with `python -m src.scrapers.run_all --only <carrier> --dry-run` first.
4. If the source page changed, update parser fixtures and golden tests before changing production writes.
5. If a carrier blocks automation or requires authentication, mark the scraper unsupported or experimental instead of bypassing access controls.

## Data Model Changes

Before changing tables:

- Update `src/lib/create.sql`.
- Add or update a numbered migration under `src/lib/migrations/`.
- Update `docs/DATA_MODEL.md`.
- Add tests for RLS/public-read/service-role-write behavior.
- Verify frontend queries still avoid private columns.

## Incident Shutdown

If data is misleading, credentials leak, or scraping creates legal/compliance risk:

1. Disable scheduled workflows.
2. Remove deployment environment variables or pause hosting.
3. Rotate affected secrets in Supabase, GitHub, Sentry, Telegram, and hosting.
4. Remove or suppress affected rows.
5. Document the incident privately before public relaunch.

## Handover Checklist

- Repository access transferred or maintainer added.
- Supabase project ownership transferred or maintainer added.
- GitHub Actions secrets rotated by new maintainer.
- Hosting project transferred.
- Sentry project transferred.
- Telegram bot ownership transferred or bot disabled.
- Compliance/takedown contact updated in README and `docs/COMPLIANCE.md`.
- Phase 5 launch checklist rerun before any public URL is advertised.
