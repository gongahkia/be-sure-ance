# Deployment Runbook

Current production URL status: `https://besureance.netlify.app/` is live.

No DNS change or custom-domain change was performed in this session.

## Platform Decision

Restore Netlify first.

Rationale:

- `netlify.toml` defines the root build command, publish directory, function directory, SPA redirect, and security headers.
- Netlify restore is lower-risk than changing hosting providers during the launch gate.
- Cloudflare Pages remains a fallback if Netlify free-tier limits, domain requirements, or operational access block launch.

README may claim `https://besureance.netlify.app/` after the 2026-07-07 route and pre-flight checks.

## Netlify Settings

Use the existing `netlify.toml`:

- Base directory: blank / repository root
- Build command: from `netlify.toml`
- Publish directory: `src/be-sure-ance-app/dist`
- Functions directory: `netlify/functions`
- Data source: committed `src/be-sure-ance-app/public/data/app-data.json`
- SPA redirect: `/*` to `/index.html`
- Security headers: CSP, `X-Content-Type-Options`, `Referrer-Policy`, `Permissions-Policy`, and HSTS

## Frontend Environment Variables

Production frontend hosting may use only public `VITE_*` variables:

- `VITE_SITE_ORIGIN`
- `VITE_STATIC_DATA_PATH`
- `VITE_PDF_BRIEF_ENDPOINT`
- optional `VITE_SENTRY_*`

Never configure these private values in Netlify frontend build settings:

- `TELEGRAM_BOT_TOKEN`
- `SENTRY_DSN`

Set `NETLIFY_BUILD_HOOK_URL` only in GitHub Actions secrets. Scheduled scraping runs in GitHub Actions, commits validated static app data, then calls the build hook. Set Telegram and backend observability secrets only in the relevant backend worker environment.

## Restore Procedure

1. Confirm Phase 4 exit verification and launch pre-flight runbook are current.
2. Restore or create the Netlify site from this repository. Done: `https://besureance.netlify.app/`.
3. Apply the Netlify settings from `netlify.toml`.
4. Configure only the allowed frontend public environment variables.
5. Store `NETLIFY_BUILD_HOOK_URL` in GitHub Actions secrets for scheduled refresh.
6. Set `VITE_SITE_ORIGIN` to `https://besureance.netlify.app`.
7. Confirm `src/be-sure-ance-app/public/data/app-data.json` is present in the deployed commit.
8. Deploy to a staging or deploy-preview URL first.
9. Run the `staging-preflight` workflow with `STAGING_ORIGIN` set to that URL.
10. Confirm no private variables appear in Netlify build logs or browser-exposed `import.meta.env` usage.
11. Obtain compliance sign-off recorded outside the repository.
12. Promote the deploy to production.
13. Verify the production URL routes, sitemap, robots file, security headers, and Lighthouse scores.
14. Update README with the live URL only after the production URL works.

## Required Route Checks

Verify:

- `/`
- `/matrix/panel-hospitals`
- `/status`
- `/share?plans=aia:sample-shield`
- `/sitemap.xml`
- `/robots.txt`

Use:

```sh
python3 scripts/staging_preflight.py --origin "$STAGING_ORIGIN" --output output/staging-preflight/preflight.json
```

2026-07-07 production check:

```sh
python3 scripts/staging_preflight.py --origin https://besureance.netlify.app --output /tmp/bsa-staging-preflight.json --load-requests 6 --load-concurrency 2 --max-p95-ms 2500
```

Result: `overall_status=passed`.

## Cloudflare Pages Fallback

Use Cloudflare Pages only if Netlify restore is blocked.

Equivalent settings:

- Root directory: repository root
- Build command: mirror `netlify.toml`
- Output directory: `src/be-sure-ance-app/dist`
- Environment allowlist: same public `VITE_*` variables only
- Headers/redirects: must preserve SPA fallback and the same security-header policy before launch

If migrating, add the Cloudflare-specific config in the same commit that documents the final production URL.

## Domain And Contact

Default contact email: `gabrielzmong@gmail.com`.

Custom domain is optional and budget-dependent. If a custom domain is configured, update:

- `VITE_SITE_ORIGIN`
- README live URL
- sitemap submission docs
- contact and takedown references if the contact address changes
