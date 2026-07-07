# Search Indexing Runbook

Current submission status as of 2026-07-07: ready for owner submission.

Reason: `https://besureance.netlify.app` returns HTTP 200 for `/`, `/sitemap.xml`, `/robots.txt`, `/status`, `/matrix/panel-hospitals`, and a representative `/share` route as of 2026-07-07. Search-indexing preflight now passes after static plan JSON-LD gained fallback `subjectOf` source links. Google and Bing submission still require verified site-owner access.

## Source Guidance

- Google Search Central: submit a sitemap through the Search Console Sitemaps report, the Search Console API, or a `Sitemap:` line in `robots.txt`.
- Google Search Console Help: owner permissions are required to submit through the Sitemaps report; without owner permissions, list the sitemap in `robots.txt`.
- Bing Webmaster Tools: add and verify the site, create/upload the sitemap, then submit it through Bing Webmaster Tools.

References:

- https://developers.google.com/search/docs/crawling-indexing/sitemaps/build-sitemap
- https://support.google.com/webmasters/answer/7451001
- https://www.bing.com/webmasters/help/getting-started-checklist-66a806de

## Pre-Submission Gate

After production deploy works, run:

```sh
python scripts/search_indexing_preflight.py \
  --origin "$LIVE_ORIGIN" \
  --output output/search-indexing/preflight.json
```

The gate verifies:

- `/sitemap.xml` exists, parses as XML, has at least one URL, and uses the live origin.
- `/robots.txt` references `Sitemap: <origin>/sitemap.xml`.
- Representative `/plan/<insurer>/<plan-slug>/` pages render a canonical link matching the sitemap URL.
- Representative plan pages include JSON-LD with `@type: FinancialProduct`, matching `url`, and `subjectOf` source links.
- JSON-LD avoids quantitative offer fields such as `offers`, `premium`, `deductible`, and `coinsurance`.

The `search-indexing-preflight` workflow runs the same gate against `LIVE_ORIGIN`.

## Submission Steps

Google Search Console:

1. Verify ownership of the production origin.
2. Confirm `https://<origin>/sitemap.xml` loads in a browser.
3. Open the Sitemaps report.
4. Submit `sitemap.xml`.
5. Record submitted date, property, status, and any processing errors.

Bing Webmaster Tools:

1. Add and verify the production site.
2. Open Sitemaps.
3. Submit `https://<origin>/sitemap.xml`.
4. Record submitted date, property, status, and any processing errors.

## Status Log

| Date | Origin | Google status | Bing status | Evidence |
| :-- | :-- | :-- | :-- | :-- |
| 2026-07-02 | `https://be-sure-ance.netlify.app` | Blocked - not submitted | Blocked - not submitted | Origin returned HTTP 404 for sitemap and app routes. |
| 2026-07-07 | `https://be-sure-ance.netlify.app` | Blocked - not submitted | Blocked - not submitted | `/`, `/sitemap.xml`, `/robots.txt`, and `/status` returned HTTP 404. |
| 2026-07-07 | `https://besureance.netlify.app` | Ready - not submitted | Ready - not submitted | Routes, sitemap, and robots returned HTTP 200; staging preflight passed; search-indexing preflight passed after JSON-LD `subjectOf` fallback deploy. |

## Launch Rule

Do not start outreach until:

- production routes pass `search-indexing-preflight`
- Google Search Console records the sitemap submission
- Bing Webmaster Tools records the sitemap submission
- README points to the same canonical live origin
