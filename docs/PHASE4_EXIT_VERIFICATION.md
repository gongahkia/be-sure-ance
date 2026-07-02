# Phase 4 Exit Verification

Date: 2026-07-02
Branch: `main`
Head verified before this record: `154fc0f0f2c4347afa6a5c2294737e0e2feacf16`

## Status

Phase 4 is locally verified for OGP/GovTech portfolio readiness.

No push or deployment was performed. Remote GitHub Actions status for these local commits is not verified.

## Reviewer Orientation

README positioning, metrics, cost transparency, and limitations are visible:

- Positioning: public-good IFA pre-meeting research tool that complements compareFIRST and does not replace carrier brochures, licensed advisers, or regulated advisory workflows.
- No-advice boundary: no advice, quotes, recommendations, suitability rankings, premium estimates, or cost projections.
- Metrics: portfolio status records 10 supported scheduled carriers, 5,305 MOH institutions, 12 LIA claim metrics, open dataset artifact workflow, WCAG evidence, and unavailable production analytics/alerts.
- Cost posture: `$0/mo` target during portfolio validation on free-tier infrastructure; paid upgrades must be documented before launch.
- OGP/GovTech scope: ADR 0007 documents Postman.gov.sg, FormSG, and Go.gov.sg evaluation and defers integration until public-sector ownership, access, and governance are confirmed.

Open-source legibility is present:

- `LICENSE`: MIT license.
- `CONTRIBUTING.md`: contribution rules for scrapers, data contracts, compliance wording, and deployment assumptions.
- `CODE_OF_CONDUCT.md`: contributor conduct baseline.
- `docs/adr/README.md`: ADR index from regex-cost removal through OGP tooling deferral.

## Operational Evidence

Reviewer-facing operating docs exist:

- `docs/COMPLIANCE.md`: PDPA stance, MAS FAA/no-advice boundary, observability, scraping ethics, takedown handling, and lawyer-review launch gate.
- `docs/DATA_MODEL.md`: source-traceable `plan_facts`, `scraper_health`, brochure history, open dataset fields, and public/private data boundaries.
- `docs/SUCCESSION.md`: credential inventory locations, weekly operations, backup restore pointer, takedown flow, scraper failure flow, and shutdown path.
- `docs/BACKUP_RETENTION.md`: nightly logical dump artifact, 30-day retention, R2 mirror option, restore procedure, and no-secret local smoke test.
- `docs/TAKEDOWN_RUNBOOK.md`: source-removal steps, SLA, private intake fields, User-Agent, robots.txt, and takedown contact.

Status and observability evidence exists:

- `/status` is backed by the `scraper_health` table and hides raw errors from public clients.
- Sentry is optional for frontend and scraper paths; scrubbers redact Supabase keys, service-role tokens, Telegram tokens, Sentry DSNs, bearer tokens, and `sb_secret_*` values.
- GitHub workflows cover CI, weekly scraping, validation snapshots, open dataset publication, and nightly Supabase backup artifacts.

## Portfolio Evidence

WCAG evidence is recorded:

- `docs/ACCESSIBILITY.md` reports 0 Axe violations / Lighthouse 100 for `/`, `/matrix/panel-hospitals`, `/status`, and `/share/<uuid>`.
- Manual screen-reader testing remains a Phase 5 prelaunch requirement because automated tools cannot prove full WCAG conformance.

Open dataset path is present:

- `.github/workflows/publish-open-dataset.yml` exports weekly CC-BY-4.0 CSV artifacts with plan facts, source URLs, and verification dates.
- `tests/test_open_dataset.py` covers snapshot fields, source/date inclusion, CSV export, and exclusion of share/secret-like fields.

Case-study and storytelling path is started without inventing traction:

- `docs/case-studies/README.md` starts the `IFA panel-matrix pre-meeting workflow` case-study path and says not to invent testimonials.
- `docs/blog/why-we-ripped-out-regex-derived-premiums.md` explains the pivot away from regex-derived premiums and cost projections.
- `docs/talks/README.md` starts a civic-tech talk proposal around provenance, validation drift, `/status`, and no-advice boundaries.

## Local Verification

Focused Phase 4 evidence:

- `tests/test_accessibility_audit_docs.py`
- `tests/test_backup_and_ethics.py`
- `tests/test_compliance_doc.py`
- `tests/test_open_dataset.py`
- `tests/test_open_dataset_docs.py`
- `tests/test_open_source_docs.py`
- `tests/test_observability.py`
- `tests/test_ogp_tooling_scope.py`
- `tests/test_storytelling_artifacts.py`

Full local gates for this record:

- `/tmp/be-sure-ance-venv/bin/black --check src tests scripts`
- `/tmp/be-sure-ance-venv/bin/ruff check src tests scripts`
- `/tmp/be-sure-ance-venv/bin/python -m unittest discover -s tests`
- `npm run lint` in `src/be-sure-ance-app`
- `npm run format:check` in `src/be-sure-ance-app`
- `VITE_SUPABASE_URL=https://example.supabase.co VITE_SUPABASE_ANON_KEY=anon VITE_SITE_ORIGIN=https://example.com npm run build` in `src/be-sure-ance-app`
- `pre-commit run --all-files`
- `git diff --check`

Result: all commands passed locally; unittest discovery ran 281 tests.

## Residual Launch Gates

Phase 4 local readiness is satisfied. The only remaining public-launch blockers recorded here are Phase 5 deployment, remote CI/indexing/operations verification after push is allowed, and Singapore fintech/compliance lawyer sign-off.

The compliance sign-off must include confirmation that live scraper robots.txt handling matches `docs/COMPLIANCE.md` before public relaunch.
