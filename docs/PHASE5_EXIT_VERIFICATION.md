# Phase 5 Exit Verification

Date: 2026-07-07
Branch: `main`

## Status

Phase 5 exit is blocked.

Production deployment is restored, but launch exit criteria are not met.

Do not publicly launch yet.

## Verified Blockers

Production URL:

- GitHub repository homepage is `https://besureance.netlify.app/`.
- Historical inactive Netlify origin: `https://be-sure-ance.netlify.app`.
- `https://be-sure-ance.netlify.app` returned HTTP 404 for `/`, `/matrix/panel-hospitals`, `/status`, `/share?plans=aia:healthshield-gold-max-demo`, `/sitemap.xml`, and `/robots.txt` on 2026-07-02.
- `https://be-sure-ance.netlify.app` returned HTTP 404 for `/`, `/status`, `/sitemap.xml`, and `/robots.txt` on 2026-07-07.
- `scripts/staging_preflight.py` against `https://be-sure-ance.netlify.app` returned `overall_status=failed`.
- `scripts/search_indexing_preflight.py` against `https://be-sure-ance.netlify.app` returned `overall_status=failed` with `HTTP Error 404: Not Found`.
- Confirmed active Netlify origin is `https://besureance.netlify.app`.
- `https://besureance.netlify.app` returned HTTP 200 for `/`, `/matrix/panel-hospitals`, `/status`, `/share?plans=aia:healthshield-gold-max-demo`, `/sitemap.xml`, and `/robots.txt` on 2026-07-07.
- `scripts/staging_preflight.py` against `https://besureance.netlify.app` returned `overall_status=passed`.
- `scripts/search_indexing_preflight.py` against `https://besureance.netlify.app` returned `overall_status=failed` because representative plan JSON-LD lacked `subjectOf` source links.
- Commit `f1d10eb` deployed a static plan JSON-LD `subjectOf` fallback, and `scripts/search_indexing_preflight.py` against `https://besureance.netlify.app` then returned `overall_status=passed`.
- Live JS bundle check found no `SERVICE_ROLE`, `service_role`, `SUPABASE`, `TELEGRAM_BOT_TOKEN`, `SENTRY_DSN`, `NETLIFY_BUILD_HOOK_URL`, `PASSWORD`, or `SECRET` strings.

Open Phase 5 blockers:

- `#73`: Google Search Console and Bing Webmaster Tools sitemap submission is not complete.
- Phase 5 P0 blockers remain for compliance, metrics, and IFA trial.

Closed Phase 5 prep:

- `#74`: outreach drafts are complete and issue-closed, but no outreach should be posted until production URL, indexing, pre-flight, and compliance sign-off are complete.

Compliance:

- Compliance lawyer sign-off is not obtained as of 2026-07-07.
- `docs/LAUNCH_PREFLIGHT.md` records compliance sign-off status as blocked.
- Private legal/compliance notes must stay outside this repository.

Usage metrics:

- No production Plausible, Umami, or privacy-safe analytics deployment is claimed.
- README still records 30-day lookups as unavailable.

IFA trial:

- No IFA weekly PDF export trial is recorded in this repository.
- `docs/OUTREACH.md` includes an SG IFA Telegram/WhatsApp draft, but it is blocked until the live URL and compliance gates pass.

## Completed Phase 5 Prep

- `docs/DEPLOYMENT.md`: Netlify restore path, frontend env allowlist, route checks, and Cloudflare Pages fallback.
- `docs/LAUNCH_PREFLIGHT.md`: staging smoke/load/security/Lighthouse/compliance gate.
- `docs/SEARCH_INDEXING.md`: Google/Bing sitemap submission runbook and indexing pre-flight.
- `docs/OUTREACH.md`: Seedly, SG IFA, Reddit, Show HN, and MAS/OGP/GovTech drafts with no-advice limitations.
- `docs/OPERATIONS.md`: weekly, monthly, and quarterly post-launch cadence with owner, issue templates, and first scheduled review issue [#99](https://github.com/gongahkia/be-sure-ance/issues/99) for 2026-07-14.

## Required To Pass

1. Submit sitemap in Google Search Console and Bing Webmaster Tools and record status.
2. Obtain and privately file compliance lawyer outcome; update public status only.
3. Confirm usage metrics are recording or keep metrics unavailable without launch claims.
4. Record at least one IFA who has tried or agreed to try weekly PDF export.

## Conclusion

Production app and pre-submission indexing gates are live on Netlify, but search-console submission, compliance, metrics, and IFA trial gates are not complete.
