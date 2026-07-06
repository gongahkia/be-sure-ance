# Succession Runbook

Purpose: let another maintainer operate or safely wind down Be-sure-ance without exposing secrets in this repository.

## Ownership

Current maintainer: Gabriel Ong Zhe Mian.

Primary contact: `gabrielzmong@gmail.com`.

## Launch State

No production deployment is claimed during Phases 1-4. Phase 5 is the launch gate.

Before any public relaunch, confirm:

- Static app data is generated from the build pipeline.
- No backend secret is present in frontend env.
- README, app copy, and `docs/COMPLIANCE.md` match the live behavior.
- A Singapore fintech/compliance lawyer has reviewed the live product.

## Credential Inventory Locations

Do not store actual secrets in this document.

Expected locations:

- Local development: maintainer-owned `.env` file copied from `.env.example`.
- GitHub Actions: repository or organisation secrets.
- Telegram beta: BotFather token stored only in local `.env` or GitHub/environment secrets.
- Sentry: project DSN and alert recipients in Sentry project settings and GitHub secrets.
- Hosting provider: Netlify restore is the selected Phase 5 path; Cloudflare Pages remains the fallback if Netlify is blocked.
- Netlify scheduled refresh: build hook URL stored only as a GitHub Actions secret.
- Static app data: generated, validated, and committed by `refresh-static-data`; consumed by Netlify builds.

Never commit:

- `TELEGRAM_BOT_TOKEN`
- `SENTRY_DSN`
- `NETLIFY_BUILD_HOOK_URL`
- hosting deploy tokens
- database passwords
- private legal/compliance notes

Only public `VITE_*` values can be present in frontend build settings.

## Weekly Operations

Use [Post-launch operations cadence](./OPERATIONS.md) for weekly, monthly, and quarterly review issue templates.

1. Check GitHub Actions for `refresh-static-data`, `validate-scraper-snapshots`, `publish-open-dataset`, and CI.
2. Check the latest `refresh-static-data` run for static data generation and validation status.
3. Review `/status` for stale, failing, unsupported, or validation-failed carriers.
4. Triage `brochure_change_alerts` rows before dispatching any public alert.
5. Check Sentry for new frontend or scraper error groups if DSNs are configured.
6. Confirm open dataset artifacts were generated and do not include secret-like fields.

## Takedown Flow

1. Acknowledge credible carrier or rights-holder requests within 2 business days.
2. Suppress disputed source rows, plan facts, brochure objects, or alerts while reviewing.
3. Resolve or provide written status within 7 calendar days.
4. Keep private notes outside the repo with source URL, requestor, action, and date.

## Scraper Failure Flow

1. Check `/status` for last success, last failure, row count, and validation status.
2. Open validation artifacts from the latest GitHub Actions run.
3. Reproduce locally with `python3 -m src.scrapers.run_all --only <carrier> --dry-run` first.
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
3. Rotate affected secrets in GitHub, Sentry, Telegram, and hosting.
4. Remove or suppress affected rows.
5. Document the incident privately before public relaunch.

## Handover Checklist

- Repository access transferred or maintainer added.
- GitHub Actions secrets rotated by new maintainer.
- Hosting project transferred.
- Sentry project transferred.
- Telegram bot ownership transferred or bot disabled.
- Compliance/takedown contact updated in README and `docs/COMPLIANCE.md`.
- Phase 5 launch checklist rerun before any public URL is advertised.
