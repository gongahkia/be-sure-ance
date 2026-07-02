# Contributing

`Be-sure-ance` accepts contributions that preserve its qualitative-only, source-traceable, no-advice posture.

## Local setup

Docker demo:

```sh
docker compose up --build
```

Open `http://localhost:5173`. The compose stack uses seeded local demo data and fake local keys only; it does not need production Supabase credentials.

Manual setup:

```sh
pip install -r requirements.txt
playwright install chromium
npm --prefix src/be-sure-ance-app ci
cp .env.example .env
```

Use placeholder public frontend values for offline frontend builds:

```sh
VITE_SUPABASE_URL=https://example.supabase.co
VITE_SUPABASE_ANON_KEY=anon
VITE_SITE_ORIGIN=https://example.com
```

Never put `SUPABASE_SECRET_KEY`, `SUPABASE_SERVICE_ROLE_KEY`, or `TELEGRAM_BOT_TOKEN` in frontend `VITE_*` variables.

## Test gates

Run the narrowest relevant checks first, then the full local gate before opening a PR:

```sh
black --check src tests
ruff check src tests
python -m unittest discover -s tests
npm --prefix src/be-sure-ance-app run lint
npm --prefix src/be-sure-ance-app run format:check
(cd src/be-sure-ance-app && VITE_SUPABASE_URL=https://example.supabase.co VITE_SUPABASE_ANON_KEY=anon VITE_SITE_ORIGIN=https://example.com npm run build)
pre-commit run --all-files
git diff --check
```

## Issue workflow

- Use GitHub issues for scoped work.
- Keep each PR tied to one issue or one clearly bounded fix.
- State whether the change affects compliance, scraping, data model, frontend display, or deployment.
- Do not redeploy while Phase 1-4 work is in progress; Phase 5 is the launch gate.

## Data quality

- Every user-facing plan fact must carry `source_url`, `source_type`, `scraped_at`, and `last_verified_at`.
- Do not infer premiums, dollar projections, suitability rankings, or recommendations from carrier narrative text.
- Use the MOH, LIA, MAS, carrier, or brochure source that produced the fact.
- Mark missing, stale, or unverifiable facts as unavailable instead of filling gaps.
- Keep scraper changes robots-aware and use the documented `User-Agent`.
- If a source owner asks for takedown or correction, follow `docs/COMPLIANCE.md`.

## Documentation

Update the README, `docs/DATA_MODEL.md`, `docs/COMPLIANCE.md`, or an ADR when behavior, data contracts, compliance posture, or deployment assumptions change.
