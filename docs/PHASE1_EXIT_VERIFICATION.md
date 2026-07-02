# Phase 1 Exit Verification

Date: 2026-07-02
Branch: `main`
Head: `4d7dd51507adf7e1bd4bba55b95b02169755e2f6`

## Status

Phase 1 local stabilization checks pass. Remote GitHub CI is not verified for these local commits because the branch has not been pushed, avoiding a possible deployment trigger before Phase 5.

## Evidence

- Other Phase 1 issues: `gh issue list --state open --label phase-1` returned only `#32` before this record.
- Cost-math search: `rg 'AMOUNT_PATTERN|PERCENT_PATTERN|derive_premium|derive_cost|build_scenario|ScenarioCalculator|premium_facts|cost_sharing|scenario_assumptions|S\$|\$[0-9]' ...` found only legacy-column drops and tests proving qualitative behavior.
- SQL/RPC search: `rg 'execute_sql|rpc\(|GRANT ALL .* TO anon|GRANT ALL .* TO authenticated|FOR (INSERT|UPDATE|DELETE|ALL) TO anon|FOR (INSERT|UPDATE|DELETE|ALL) TO authenticated' ...` found only `DROP FUNCTION IF EXISTS public.execute_sql(TEXT);`.
- Frontend env/tooling search: `rg '@vue/cli-service|vue-cli-service|VUE_APP_|process\.env' ...` found only the negative `VUE_APP_` test assertion.
- Plans query: `App.vue` contains one `supabase.from('plans').select('*')`.
- Scraper runtime: default `run_all` list is `aia`, `china_life`, `chubb`, `great_eastern`, `hsbc`, `iii`, `singlife`, `sunlife`, `tokio_marine`, `uoi`; experimental scrapers require `--include-experimental`.
- Deployment/CI trigger check: `gh run list` showed no runs created on 2026-07-02; no local `git push` was run for the stabilization commits.

## Local Gates

- `black --check src tests`
- `ruff check src tests`
- `python -m unittest discover -s tests -p 'test_*.py'` passed 41 tests.
- `npm --prefix src/be-sure-ance-app run lint`
- `npm --prefix src/be-sure-ance-app run format:check`
- `(cd src/be-sure-ance-app && VITE_SUPABASE_URL=https://example.supabase.co VITE_SUPABASE_ANON_KEY=anon npm run build)`
- `pre-commit run --all-files`
- `git diff --check`

## Blocker

Remote CI pass/fail cannot be verified until a push is allowed. Keep deployment disabled until Phase 5.
