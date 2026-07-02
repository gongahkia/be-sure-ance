# Phase 2 Exit Verification

Date: 2026-07-02
Branch: `main`
Head: `5c76f5591a6cc3248e05d0e80b4bc3f05d18376e`

## Status

Phase 2 pivot checks are locally verified for the source-traceable data model, qualitative frontend, provenance UI, README positioning, compliance posture, scraper hardening, and offline golden tests.

No push or deploy was performed. Remote GitHub Actions status for these local commits is not verified.

## Evidence

- Phase 2 issue state: `gh issue list --state open --label phase-2` returned only `#43` before this record.
- Data model: `plan_facts` schema exists with `source_url`, `source_type`, `scraped_at`, `last_verified_at`, RLS, and deterministic `(insurer, plan_slug, field_name)` upsert key.
- Fact contract: `src/lib/plan_facts_contract.json` defines qualitative fields and explicitly forbids premium amounts, deductibles, coinsurance, projections, advice, recommendations, and unsourced panel membership.
- Brochure flow: brochure capture writes `brochure_metadata`; brochure parsing writes qualitative `plan_facts` for panel hospitals, exclusions, waiting periods, claim deadlines, and claim SLA.
- Frontend: `App.vue` loads `plan_facts`; `PlanCard.vue` and `ComparisonTable.vue` render qualitative fact groups only.
- Provenance: `FactProvenance.vue` displays source URL, source type, scraped date, verified date, stale status, and incomplete-source state for visible fact groups.
- README/compliance: README positions the app as an IFA qualitative research tool complementing compareFIRST; `docs/COMPLIANCE.md` documents PDPA, MAS FAA, scraping ethics, takedown handling, and lawyer-review launch gate.
- Golden tests: `tests/scrapers/test_aia_golden.py` uses offline AIA HTML fixtures; `.github/workflows/ci.yml` runs `python -m unittest discover -s tests -p "test_*.py"` under the `Run unit and offline golden tests` step.
- Cost/advice search: runtime search for removed calculator/cost fields found no active frontend or scraper usage; remaining hits are schema legacy drops, docs, or tests that assert absence.

## Local Gates

- `/tmp/be-sure-ance-venv/bin/black --check src tests`
- `/tmp/be-sure-ance-venv/bin/ruff check src tests`
- `/tmp/be-sure-ance-venv/bin/python -m unittest discover -s tests -p 'test_*.py'` passed 93 tests.
- `npm --prefix src/be-sure-ance-app run lint`
- `npm --prefix src/be-sure-ance-app run format:check`
- `(cd src/be-sure-ance-app && VITE_STATIC_DATA_PATH=/data/app-data.json npm run build)`
- `PATH=/tmp/be-sure-ance-venv/bin:$PATH /tmp/be-sure-ance-venv/bin/pre-commit run --all-files`
- `git diff --check`

## Validation Differ

Command run:

```sh
/tmp/be-sure-ance-venv/bin/python -m src.validation.differ --output-dir /tmp/be-sure-ance-phase2-validation-60s --max-urls-per-insurer 1 --request-timeout 60
```

Result:

```json
{
  "errors": 1,
  "failed": 0,
  "no_baseline": 9,
  "passed": 0,
  "total_targets": 10
}
```

Details:

- `aia::aia.com.sg` timed out at 60 seconds.
- The remaining 9 supported targets generated snapshots but had no committed baselines to compare against.

This means the validation differ was run, but it is not green. Do not treat this as Phase 5 release evidence until baselines exist and the AIA timeout is resolved or explicitly excluded.

## Residual Release Blockers

- Remote CI is not verified until these local commits are pushed.
- Validation differ baselines are missing.
- AIA validation fetch times out from this environment.
- Public deployment remains blocked until Phase 5.
