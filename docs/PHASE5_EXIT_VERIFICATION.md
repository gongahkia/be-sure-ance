# Phase 5 Exit Verification

Date: 2026-07-07
Branch: `main`

## Status

Phase 5 exit is blocked.

Do not publicly launch yet.

## Verified Blockers

Production URL:

- GitHub repository homepage is `https://be-sure-ance.netlify.app`.
- `https://be-sure-ance.netlify.app` returned HTTP 404 for `/`, `/matrix/panel-hospitals`, `/status`, `/share?plans=aia:healthshield-gold-max-demo`, `/sitemap.xml`, and `/robots.txt` on 2026-07-02.
- `https://be-sure-ance.netlify.app` returned HTTP 404 for `/`, `/status`, `/sitemap.xml`, and `/robots.txt` on 2026-07-07.
- `scripts/staging_preflight.py` against `https://be-sure-ance.netlify.app` returned `overall_status=failed`.
- `scripts/search_indexing_preflight.py` against `https://be-sure-ance.netlify.app` returned `overall_status=failed` with `HTTP Error 404: Not Found`.

Open Phase 5 blockers:

- `#72`: production deployment is not restored; README must not claim a live URL.
- `#73`: Google Search Console and Bing Webmaster Tools sitemap submission is not complete.

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
- `docs/OPERATIONS.md`: weekly, monthly, and quarterly post-launch cadence with owner and issue templates.

## Required To Pass

1. Restore or migrate production deployment.
2. Verify production routes, security headers, sitemap, robots file, and Lighthouse scores.
3. Update README with the verified live URL only after it works.
4. Confirm frontend env contains only anon/public `VITE_*` values and no service-role key.
5. Run staging and search-indexing pre-flight against the live origin.
6. Submit sitemap in Google Search Console and Bing Webmaster Tools and record status.
7. Obtain and privately file compliance lawyer outcome; update public status only.
8. Confirm usage metrics are recording or keep metrics unavailable without launch claims.
9. Record at least one IFA who has tried or agreed to try weekly PDF export.
10. Open the first post-launch operations review issue with a concrete review date.

## Conclusion

Production app is not live, Phase 5 P0 blockers remain, and launch exit criteria are not met.
