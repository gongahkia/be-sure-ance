# WORKON-PIVOT-ASAP

Synthesis of the full review → fix → pivot → adoption → portfolio plan for `be-sure-ance`. Written 2026-05-15.

Execute phases sequentially. Do **not** redeploy until Phase 5.

---

## 0. Current state diagnosis

**Repo shape**
- Frontend: Vue 3 + Vue CLI (EOL) + Supabase JS client. Netlify deploy currently down (per README, since 2025-04-07).
- Backend: Python Playwright scrapers, scheduled weekly Mon 00:00 SGT via GH Actions.
- DB: Supabase Postgres. 26 per-insurer tables + `specialist_resources` + `plan_comparison_facts`.
- Validation: `src/validation/differ.py` snapshots scraped page DOM and diffs against baseline.
- Tests: 1 file (`tests/test_validation_differ.py`). No frontend or scraper field tests.

**Killing flaws**
1. **Regex-derived premium/deductible/coinsurance** in `src/scrapers/comparison_facts.py:23-24, 76-124` → fed to `ScenarioCalculator.vue:100-125` → renders dollar projections from narrative-blurb regex. Liability-grade misleading. Cannot be shown to clients.
2. **`execute_sql(query text)` RPC** in `src/lib/create.sql:1-6` granted broadly + **`GRANT ALL ON ALL TABLES … TO anon`** at `src/lib/create.sql:22-23`. Combined with no RLS, this is a SQL-injection blast door and unrestricted-write surface for anyone with the anon key.
3. **Per-insurer table fan-out** — `App.vue:151-159` does `Promise.all` over 26 tables on every page load.
4. **17/28 scrapers are stubs** — fwd, prudential, manulife, etc. just instantiate `GenericScraperConfig` and produce nothing. README marks them ❌ but they ship.
5. **Audience repivot half-done** — copy says "for insurance agents" (commit 677bcf6) but no auth, no client-brief export, no CRM hook, no CPD compliance.
6. **Deployment dead** — Netlify badge shows down. README warns it.
7. **Vue CLI EOL** — `@vue/cli-service` 5.x archived; build toolchain is rot.
8. **`pypdf` declared but unused** — brochures never parsed; deps lie about scope.

**Audience decision**
- Tied agents: unreachable (carrier intranets are authoritative).
- IFAs/FAs: reachable, but only with compliance-safe data.
- Direct consumers: unreachable (compareFIRST + MoneySmart own this).
- **Target = IFAs doing pre-meeting research.** Realistic, defensible.

**Positioning**
- compareFIRST (MAS+CASE+LIA+MoneySENSE) owns regulated quant comparison for Direct Purchase Insurance.
- MoneySmart / SingSaver / Seedly own lead-gen aggregation.
- **Unowned white space:** structured *qualitative* carrier metadata at plan grain (panel hospitals, exclusions, claim SLA, brochure versioning).
- be-sure-ance pitch: "compareFIRST handles regulated quant; we handle the qualitative metadata gov doesn't publish."

---

## Phase 1 — Stabilize (Week 1–2)

Goal: stop the bleeding. Repo is currently dangerous to redeploy. Lock down DB, kill misleading numbers, modernize toolchain.

### 1.1 Kill the liability surface
- [ ] **Remove regex-derived premium/deductible/coinsurance** from `src/scrapers/comparison_facts.py` (delete `derive_premium_facts`, `derive_cost_sharing`, `build_scenario_assumptions`, `AMOUNT_PATTERN`, `PERCENT_PATTERN`).
- [ ] **Delete `ScenarioCalculator.vue`** from `src/be-sure-ance-app/src/components/` and its import in `App.vue:113, 126`.
- [ ] **Replace** with a qualitative-only `plan_comparison_facts` schema: `panel_network_size INT`, `claim_sla_days INT`, `exclusions TEXT[]`, `waiting_period_days INT`, `coverage_tags TEXT[]`, `brochure_hash TEXT`, `brochure_last_changed_at TIMESTAMPTZ`.
- [ ] Rewrite `comparison_facts.py` to populate the new schema (no dollar math).

### 1.2 Lock down Supabase
- [ ] **Drop `execute_sql` RPC** in `src/lib/create.sql`. Replace `overwrite_table_data` in `src/scrapers/aia.py:84-94` (and equivalents elsewhere) with `supabase.table(t).delete().neq("id", 0).execute()` via service role.
- [ ] **Revoke** `GRANT ALL ON ALL TABLES IN SCHEMA public TO anon`. Replace with explicit `GRANT SELECT` on read-only views.
- [ ] **Enable RLS** on every table. Policies: `anon` → `SELECT` only; writes via service role only.
- [ ] **Move service role key** off any client-readable surface. Keep only in GH Actions secrets + local `.env`.
- [ ] Add `.env.example` documenting required vars.

### 1.3 Collapse per-insurer tables
- [ ] Create single `plans` table: `id`, `insurer TEXT`, `plan_name`, `plan_slug`, `plan_benefits TEXT[]`, `plan_description`, `plan_overview`, `plan_url`, `product_brochure_url`, `scraped_at TIMESTAMPTZ`. Index on `(insurer, plan_slug)`.
- [ ] Migration script in `src/lib/migrations/0001_unify_plans.sql`.
- [ ] Update `src/backend/helper.py` `overwrite_generic_table_data` to filter by `insurer` rather than full-table delete.
- [ ] Rewrite `App.vue:143-185` to single query `supabase.from("plans").select("*")` then group by `insurer` client-side.

### 1.4 Modernize frontend
- [ ] **Vite migration**: replace `@vue/cli-service` with Vite 5.x. Update `package.json` scripts (`serve` → `dev`, `build` stays). Delete `babel.config.js`, `vue.config.js`, `.eslintrc.js` — replace with `vite.config.js` + `eslint.config.js` (flat config).
- [ ] Update `netlify.toml` `command = "npm run build"` still works; verify `publish = "dist"` matches Vite default.
- [ ] Env vars: `VUE_APP_*` → `VITE_*`. Update `src/be-sure-ance-app/src/App.vue:130-131`.

### 1.5 Clean up deps + housekeeping
- [ ] Drop `pypdf` from `requirements.txt` (or land brochure parsing now — see Phase 2).
- [ ] Add `ruff` + `eslint` + `prettier` to `.pre-commit-config.yaml` (currently only `black`).
- [ ] Add CI lint job to `.github/workflows/` running ruff + eslint + black `--check`.
- [ ] Remove the 17 stub scrapers from README matrix or replace with real implementations (decide per-carrier; if no shape data found in 1h timeboxed spike, drop from matrix).

**Phase 1 exit criteria:** No regex dollar values shown to user. No public-anon write access to DB. Single `plans` table. Vite builds clean. CI runs lint + the 1 existing test.

Phase 1 exit verification is recorded in `docs/PHASE1_EXIT_VERIFICATION.md`.

---

## Phase 2 — Pivot (Week 3–4)

Goal: rebuild the value proposition around qualitative carrier metadata. Source-of-truth fields with provenance, not inferred numbers.

### 2.1 New data model
- [ ] Schema (extends 1.1):
  ```
  CREATE TABLE plan_facts (
    id SERIAL PRIMARY KEY,
    insurer TEXT NOT NULL,
    plan_slug TEXT NOT NULL,
    field_name TEXT NOT NULL,
    field_value JSONB NOT NULL,
    source_url TEXT NOT NULL,
    source_type TEXT NOT NULL,  -- 'brochure_pdf', 'product_page', 'manual_entry'
    scraped_at TIMESTAMPTZ NOT NULL,
    last_verified_at TIMESTAMPTZ NOT NULL,
    UNIQUE (insurer, plan_slug, field_name)
  );
  ```
  Every field traceable to a URL + capture date.

### 2.2 Brochure parsing (the long-promised `pypdf` use)
- [ ] Download brochure PDF for each plan during scrape, hash, store hash + raw bytes in object storage (Supabase Storage or R2).
- [ ] Parse with `pypdf` for: panel hospitals (regex against MOH institution list), exclusions section, waiting periods, claim deadlines.
- [ ] Output goes into `plan_facts` with `source_type='brochure_pdf'`.

### 2.3 Frontend rewrite
- [ ] Replace `PlanCard.vue` to render qualitative facts grouped: Coverage / Network / Process / Exclusions.
- [ ] Replace `ComparisonTable.vue` columns to qualitative fields only.
- [ ] Add provenance footer per fact: "scraped from <url> on <date>".

### 2.4 Audience layer (light)
- [ ] Decide: agent-facing or consumer-facing? **Default recommendation: agent-facing IFA tool**, since the qualitative metadata is what IFAs actually need.
- [ ] If agent: skip auth for v1 (no PII, no client data stored). Add it only when client-brief export ships in Phase 3.
- [ ] Rewrite README hero copy from `🤷‍♂️` consumer pitch to clinical: "Structured qualitative metadata for Singapore insurance plans. Source-traceable. Updated weekly."

### 2.5 Compliance posture
- [ ] Write `docs/COMPLIANCE.md`:
  - PDPA: no PII collected.
  - MAS FAA: no advice given, no transactions facilitated, no recommendations made. Links out to compareFIRST + carrier sites for quotes.
  - Scraping: robots.txt-respecting, identifies via `User-Agent: be-sure-ance-bot/1.0 (mailto:gabrielzmong@gmail.com)`, honors takedowns within 7 days.
- [ ] [Inference] This stance keeps the tool outside MAS FAA licensing. Not legal advice — recommend the user get a 1-hour consult with a SG fintech compliance lawyer before going live.

### 2.6 Scraper hardening
- [ ] Add retry + exponential backoff to Playwright `page.goto` calls (use `tenacity` or hand-rolled).
- [ ] Add `wait_until="networkidle"` where appropriate.
- [ ] Add per-scraper **golden-output tests**: `tests/scrapers/test_aia_golden.py` asserts that a known plan extracts the expected fields. Snapshot fixtures in `tests/fixtures/`.
- [ ] CI runs golden tests on every push; failures block merges.

**Phase 2 exit criteria:** All user-facing data has a source URL + capture date. No dollar projections anywhere. README reads clinical. `docs/COMPLIANCE.md` exists. Golden tests gate CI.

---

## Phase 3 — Data moats & workflow features (Weeks 5–10)

Goal: build the white-space niche. Start with the highest-leverage trio (1 + 6 + 14), then expand. Items numbered from the agreed adoption roadmap.

### 3.1 Starter combo (Weeks 5–7)

**(1) Panel hospital diff matrix**
- [ ] Pull MOH institution registry from data.gov.sg.
- [ ] Per-carrier: extract panel hospital list from brochure / panel page. Normalize names against MOH list using `rapidfuzz` (already in `requirements.txt`).
- [ ] New page `/matrix/panel-hospitals`: rows = hospitals, cols = carriers, cells = ✓/✗.
- [ ] Search box: "is Mt Elizabeth Novena on X's panel".

**(6) Client-brief PDF export**
- [ ] Pick up to 3 plans → one-click PDF.
- [ ] Use `reportlab` or `weasyprint` (server-side, via a Supabase Edge Function or a small FastAPI service — `fastapi` is already in `requirements.txt`).
- [ ] PDF auto-stamps MAS-required disclaimers (FAA-N03 boilerplate).
- [ ] Brand-able: agent uploads their name + MAS rep number → appears in PDF footer.

**(14) Per-plan static pages with JSON-LD**
- [ ] SSG: pre-render `/plan/<insurer>/<plan-slug>` for every plan as static HTML at build time.
- [ ] Embed `<script type="application/ld+json">` with `FinancialProduct` schema.
- [ ] Sitemap.xml auto-generated and submitted to Google Search Console.
- [ ] Verify SPA→SSG transition doesn't break the matrix view.

### 3.2 Expand data moats (Weeks 8–9)

- [ ] **(2) Claim turnaround leaderboard** from LIA annual claims-paid reports. PDF → table → carrier ranking.
- [ ] **(3) Exclusions/waiting-period normalizer** — tag taxonomy from brochure parses.
- [ ] **(4) MAS regulatory feed** — RSS/scrape MAS enforcement page, tag by carrier, surface on carrier card.
- [ ] **(5) Brochure version history** — diff each week's PDF hash; on change, generate redline view; alert subscribers.

### 3.3 Workflow features (Week 10)

- [ ] **(7) Telegram bot**: `/be-sure aia panel novena` → instant lookup. Use Telegraf or python-telegram-bot.
- [ ] **(8) Saved comparison sets** — shareable `/share/<uuid>` URL; light view counter; no PII.
- [ ] **(9) CKA/CPD disclaimer auto-stamp** — already in (6) PDF export; replicate for shared links.
- [ ] **(10) Browser extension** — Chrome MV3 manifest; content script highlights plan names on carrier sites; opens sidebar fact card. Defer to Phase 4 if time-pressed.

**Phase 3 exit criteria:** Panel matrix live, PDF export working, per-plan SEO pages indexed, at least 3 of the data-moat items shipped, Telegram bot in beta.

---

## Phase 4 — OGP / GovTech portfolio readiness (Weeks 11–14)

Goal: make this repo legible as a "tech for public good" portfolio project. Optimize for an OGP/GovTech application reviewer scanning your GitHub.

### 4.1 Hard requirements
- [ ] Position copy: README rewritten to frame as **complement** to compareFIRST. Explicitly call this out in the first paragraph.
- [ ] **Usage metrics on README**: self-hosted Plausible or Umami. Add a daily-updating shields.io badge or simple stat block: "X carriers tracked, Y lookups/30d, Z brochure alerts fired".
- [ ] **WCAG 2.1 AA pass**. Run Lighthouse + Axe; fix violations; document score in README.
- [ ] **License**: add `LICENSE` (MIT or Apache-2.0). Add `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`.
- [ ] **ADR folder** `docs/adr/`:
  - ADR-001: Removed regex-derived premiums (the pivot).
  - ADR-002: Single `plans` table over per-insurer tables.
  - ADR-003: Qualitative-only positioning vs compareFIRST.
  - ADR-004: Migrated Vue CLI → Vite.
  - ADR-005: Source-of-truth `plan_facts` model with provenance.
- [ ] **`docker-compose.yml`**: one-command local stack — `supabase-local`, `frontend`, `scrapers`, `bot`.

### 4.2 Civic-tech differentiators
- [ ] **Consume data.gov.sg APIs** — already needed for panel matrix (MOH institution registry). Add MAS regulated-entity register cross-check. LIA member directory for canonicalization.
- [ ] **Publish own open dataset**: GH Actions commits `data/be-sure-ance-snapshot-YYYY-MM-DD.csv` weekly. License: CC-BY-4.0. Document in `data/README.md`.
- [ ] **Bilingual**: EN + 中文 (zh-SG). Use vue-i18n. Translate at minimum: hero copy, comparison field labels, disclaimers. Tamil + Malay are stretch goals.
- [ ] **OGP tooling integration**:
  - Postman.gov.sg for brochure-change email alerts.
  - FormSG endpoint for "report stale data" submissions.
  - Go.gov.sg short links for shared comparisons.
- [ ] **Public scraper health dashboard**: surface `src/validation/differ.py` output at `/status` with per-carrier last-success timestamp + SLA badges.
- [ ] **Error observability**: Sentry free tier or self-hosted GlitchTip wired into frontend + scrapers. `/status` shows error rate.

### 4.3 Storytelling artifacts
- [ ] **Post-mortem blog post**: "Why we ripped out regex-derived premiums." Published on personal site or dev.to; linked from README. Single highest-value artifact for OGP application.
- [ ] **Real-IFA case study**: find one independent FA, ship the panel matrix, get named testimonial. Publish in `docs/case-studies/`.
- [ ] **`docs/DATA_MODEL.md`**: explain every field, its provenance, its limitations. Brutal honesty.
- [ ] **Talk submission**: 15-min talk for FOSSASIA / SG Hacks / Engineers.sg titled "Scraping 28 SG insurer sites without lying to anyone." Slides in `docs/talks/`.
- [ ] **`docs/SUCCESSION.md`**: handover plan — credentials inventory, runbook, where keys live, who to email. Built-to-outlast posture.

### 4.4 Risk + frugality posture
- [ ] **Cost transparency** in README: "$0/mo on Supabase free + Netlify free + GH Actions free + Cloudflare R2 free tier."
- [ ] **Nightly Supabase logical dump** to GH Actions artifact + R2 bucket. 30-day retention.
- [ ] **Scraping ethics**: `User-Agent: be-sure-ance-bot/1.0 (mailto:gabrielzmong@gmail.com)`. Honor robots.txt. Document takedown SLA in README.
- [ ] **Compliance review**: 1-hour consult with a SG fintech compliance lawyer before public relaunch. Note outcome in `docs/COMPLIANCE.md`.

**Phase 4 exit criteria:** README rewritten for portfolio readability. ADR folder populated. Usage metrics live. WCAG AA passing. Open dataset published weekly. Post-mortem written. At least 1 IFA case study.

---

## Phase 5 — Deployment & launch (Week 15)

Goal: ship. Only enter Phase 5 after Phases 1–4 land.

### 5.1 Pre-flight
- [ ] **Smoke test** every page in staging Netlify deploy.
- [ ] **Load test** the API surface (Supabase free tier limits are tight — check connection pool).
- [ ] **Lighthouse audit** ≥ 90 on Performance, Accessibility, Best Practices, SEO.
- [ ] **Security review**: rerun the lockdown checklist from Phase 1 — confirm RLS active, `execute_sql` dropped, no anon write grants.
- [ ] **Compliance lawyer sign-off** captured in writing.

### 5.2 Deploy
- [ ] **Restore Netlify deployment** OR migrate to Cloudflare Pages (faster builds, better SG latency).
- [ ] Update README: remove "deployment down" warning. Add live URL. Update badges.
- [ ] **Custom domain** (e.g. `be-sure-ance.sg` if budget; otherwise `.netlify.app` is fine for portfolio).
- [ ] **Submit sitemap.xml** to Google Search Console + Bing Webmaster Tools.
- [ ] **DNS + email**: set up `hello@be-sure-ance.sg` (or equivalent) for takedown requests; document in README.

### 5.3 Launch outreach
- [ ] **Seedly thread**: post the panel-hospital matrix as a free tool. Be honest about limitations.
- [ ] **SG IFA Telegram/WhatsApp groups**: introduce the agent-facing PDF brief feature. Get feedback.
- [ ] **Reddit r/singaporefi / r/personalfinance** post highlighting the open dataset.
- [ ] **HackerNews Show HN**: optional, frame as "structured qualitative data layer for an opaque vertical."
- [ ] **MAS / OGP / GovTech**: send a low-key note to OGP via their contact form. Not asking for anything; sharing as a "tech for public good" build. Goes into your application portfolio either way.

### 5.4 Post-launch ops
- [ ] **Weekly check**: scraper health dashboard, validation differ output, error rate.
- [ ] **Monthly check**: brochure-version-diff alerts triaged, open dataset commits clean, usage metrics summarized in a public monthly post.
- [ ] **Quarterly**: licensed-advisor reviewer sign-off on qualitative entries (item #19 from adoption roadmap).

**Phase 5 exit criteria:** Live URL working. Usage metrics climbing. At least one IFA actively using the PDF export weekly. Sitemap indexed. Compliance lawyer letter on file.

---

## Risk register

| Risk | Likelihood | Impact | Mitigation |
| :-- | :-- | :-- | :-- |
| MAS deems this regulated FA activity | Low–Med | Project killer | Compliance lawyer review pre-launch; qualitative-only stance; no advice/transactions |
| Carrier sends takedown notice | Med | Forced data removal per carrier | Honor robots.txt; published User-Agent + email; documented 7-day takedown SLA; fallback to manual data entry |
| Supabase free-tier limits hit | Low (qualitative data is small) | Brief outage | R2/object-storage offload for brochures; logical dump backups |
| Scraper drift breaks weekly job | High | Stale data | Validation differ already catches this; golden tests at the field level; per-carrier status badges expose to users |
| Single-maintainer bus factor | High | Slow rot | `docs/SUCCESSION.md`; clean reproducibility; open license invites contributors |
| Looks like compareFIRST competitor | Med | Political/PR friction | Explicit "complement" framing in README + first sentence everywhere |

---

## Out of scope (deliberately)

Items considered and explicitly **not** doing for v1:
- Freemium / paid tiers (adoption roadmap items 20–22). Defer until usage proven.
- Revenue from carrier "verified entries." Trust risk > revenue.
- Affiliate links. Conflicts with positioning vs MoneySmart/SingSaver.
- Mobile app. Web responsive is enough; mobile app adds maintenance with no clear ROI for the IFA workflow.
- General-purpose CRM. Not the niche; refers to dedicated tools (PlanHub, etc.).

---

## Quick reference — file map for Phase 1 changes

| Concern | File(s) |
| :-- | :-- |
| Remove regex premiums | `src/scrapers/comparison_facts.py`, `src/be-sure-ance-app/src/components/ScenarioCalculator.vue`, `src/be-sure-ance-app/src/App.vue:113,126` |
| Drop `execute_sql` RPC | `src/lib/create.sql:1-6`, `src/scrapers/aia.py:84-94` (and equivalents per scraper) |
| Lock down grants | `src/lib/create.sql:22-23`, add RLS policies |
| Unify tables | new `src/lib/migrations/0001_unify_plans.sql`, `src/backend/helper.py`, `src/be-sure-ance-app/src/App.vue:143-185`, `src/be-sure-ance-app/src/lib/providers.js` |
| Vite migration | `src/be-sure-ance-app/package.json`, delete `babel.config.js` + `vue.config.js` + `.eslintrc.js`, new `vite.config.js` + `eslint.config.js`, `netlify.toml` |
| Env vars | `src/be-sure-ance-app/src/App.vue:130-131` (`VUE_APP_*` → `VITE_*`), add `.env.example` |
| Dep cleanup | `requirements.txt` (drop `pypdf` unless Phase 2 brochure parsing landed), `.pre-commit-config.yaml` |
| Scraper retries | every `src/scrapers/<carrier>.py` `page.goto` call |
| Tests | new `tests/scrapers/test_<carrier>_golden.py` + `tests/fixtures/` |

---

## Sequencing summary

```
Phase 1: Stabilize        → Weeks 1–2   (no user-visible change; foundation only)
Phase 2: Pivot            → Weeks 3–4   (qualitative-only data, compliance posture)
Phase 3: Data moats       → Weeks 5–10  (panel matrix, PDF brief, SEO pages, bot)
Phase 4: OGP readiness    → Weeks 11–14 (ADRs, accessibility, open data, storytelling)
Phase 5: Deploy + launch  → Week 15     (live URL, outreach, ops cadence)
```

Total: ~15 weeks of disciplined work. Compressible to ~8 if Phase 3 is trimmed to the starter combo (1 + 6 + 14) only.

Next action: start Phase 1.1. Confirm before I begin removing the regex premium fields.
