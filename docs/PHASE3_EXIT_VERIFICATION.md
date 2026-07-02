# Phase 3 Exit Verification

Date: 2026-07-02
Branch: `main`
Head verified before this record: `7d71febe20f3b0355a5779b7015f4da4c1a456ad`

## Status

Phase 3 is locally verified as demo-ready for the starter combo and data/workflow moats.

No push or deployment was performed. Remote GitHub Actions status for these local commits is not verified.

## Starter Combo Evidence

- Panel matrix: `/matrix/panel-hospitals` is routed in `App.vue`; `PanelHospitalMatrix.vue` renders plan/hospital coverage from source-traceable plan facts; MOH institution normalization is backed by `moh_institutions`.
- PDF brief: `src/backend/pdf_brief.py` builds a qualitative, source-backed PDF for one to three plans; `BriefExportPanel.vue` sends selected public plan payloads plus session-only agent branding; the backend response is `Cache-Control: no-store`.
- Per-plan static pages: `npm run build` runs Vite plus `scripts/generate-static-pages.mjs`, which emits `/plan/<insurer>/<plan-slug>/index.html`, `sitemap.xml`, and `robots.txt` when real Supabase public env is available.

## Expansion Moats

Shipped:

- Claim turnaround evidence board from LIA source rows.
- Exclusion and waiting-period taxonomy tags.
- MAS regulatory event feed by carrier.
- Brochure version history and deduped change alerts.
- Saved comparison sets with no-PII `/share/<uuid>` links.
- Telegram lookup bot beta for `/panel` and `/fact`.

Explicitly deferred:

- Chrome MV3 sidebar extension. ADR: `docs/adr/0001-defer-chrome-extension-sidebar.md`.

This exceeds the Phase 3 requirement for at least three expansion moats shipped or explicitly deferred.

## Local Verification

Focused fixture run:

```sh
/tmp/be-sure-ance-venv/bin/python -m unittest tests.scrapers.test_aia_golden tests.test_brochure_facts tests.test_moh_institutions tests.test_lia_claim_turnaround tests.test_mas_regulatory tests.test_panel_hospital_matrix_frontend tests.test_pdf_brief tests.test_static_plan_pages
```

Result: 45 tests passed.

Dry-run ingests:

```sh
/tmp/be-sure-ance-venv/bin/python -m src.scrapers.moh_institutions --dry-run
```

Result: `moh_institution_count: 5305`.

```sh
/tmp/be-sure-ance-venv/bin/python -m src.scrapers.lia_claim_turnaround --dry-run
```

Result: `claim_turnaround_metric_count: 12`.

```sh
/tmp/be-sure-ance-venv/bin/python -m src.scrapers.mas_regulatory --dry-run
```

Result: `mas_regulatory_event_count: 0`; MAS source returned unavailable from this environment.

Full local gates:

- `/tmp/be-sure-ance-venv/bin/black --check src tests`
- `/tmp/be-sure-ance-venv/bin/ruff check src tests`
- `/tmp/be-sure-ance-venv/bin/python -m unittest discover -s tests`
- `npm run lint` in `src/be-sure-ance-app`
- `npm run format:check` in `src/be-sure-ance-app`
- `npm run build` in `src/be-sure-ance-app`
- `/tmp/be-sure-ance-venv/bin/pre-commit run --all-files`
- `git diff --check`

## No-PII And No-Advice Checks

- PDF brief generation does not persist client or agent details.
- Share links store only `insurer`, `plan_slug`, UUID, and aggregate view counts.
- Telegram bot lookup does not persist chat IDs, usernames, phone numbers, or message text.
- MAS regulatory matches marked `needs_review` are displayed as possible matches, not definitive findings.
- Claim metrics are source evidence, not suitability rankings.
- App, PDF, share, and bot surfaces include no-advice wording or no-advice compliance boundaries.
- Runtime quantitative cost projections remain absent from frontend and scraper code.

## Known Limitations

- Public deployment is still blocked until Phase 5.
- Remote CI is not verified until commits are pushed.
- Local static-page build used placeholder Supabase env and reported `static_pages: skipped_supabase_placeholder_env`; full page generation requires real public Supabase env.
- MAS live source was unavailable from this environment during dry-run, so the local MAS count was zero.
- Telegram bot is beta and requires deployment of a backend worker with `TELEGRAM_BOT_TOKEN`.
- Chrome extension work is deferred by ADR and does not block Phase 3.
- Validation-differ baselines remain a Phase 4/5 hardening item, not Phase 3 exit evidence.

## Conclusion

Phase 3 starter combo and expansion-moat requirements are locally satisfied. Do not treat this as production launch approval; Phase 5 remains the deployment gate.
