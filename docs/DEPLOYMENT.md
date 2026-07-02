# Deployment Runbook

Current production URL status: not published from this repository.

No deploy, push, DNS change, or custom-domain change was performed in this session.

## Platform Decision

Restore Netlify first.

Rationale:

- `netlify.toml` already defines the Vite app base directory, build command, publish directory, SPA redirect, and security headers.
- Netlify restore is lower-risk than changing hosting providers during the launch gate.
- Cloudflare Pages remains a fallback if Netlify free-tier limits, domain requirements, or operational access block launch.

Do not claim a live URL in README until the production URL works and staging pre-flight evidence has been captured.

## Netlify Settings

Use the existing `netlify.toml`:

- Base directory: `src/be-sure-ance-app`
- Build command: `npm run build`
- Publish directory: `dist`
- SPA redirect: `/*` to `/index.html`
- Security headers: CSP, `X-Content-Type-Options`, `Referrer-Policy`, `Permissions-Policy`, and HSTS

## Frontend Environment Variables

Production frontend hosting may use only public `VITE_*` variables:

- `VITE_SUPABASE_URL`
- `VITE_SUPABASE_ANON_KEY`
- `VITE_SITE_ORIGIN`
- `VITE_PDF_BRIEF_ENDPOINT`
- `VITE_SHARE_ENDPOINT`
- optional `VITE_SENTRY_*`

Never configure these private values in Netlify frontend build settings:

- `SUPABASE_SECRET_KEY`
- `SUPABASE_SERVICE_ROLE_KEY`
- `SUPABASE_DB_URL`
- `R2_SECRET_ACCESS_KEY`
- `TELEGRAM_BOT_TOKEN`
- `SENTRY_DSN`

Set server-side scraper, backup, Telegram, and R2 secrets only in GitHub Actions, Supabase, or the relevant backend worker environment.

## Restore Procedure

1. Confirm Phase 4 exit verification and launch pre-flight runbook are current.
2. Restore or create the Netlify site from this repository.
3. Apply the Netlify settings from `netlify.toml`.
4. Configure only the allowed frontend public environment variables.
5. Set `VITE_SITE_ORIGIN` to the canonical production origin.
6. Deploy to a staging or deploy-preview URL first.
7. Run the `staging-preflight` workflow with `STAGING_ORIGIN` set to that URL.
8. Confirm no private variables appear in Netlify build logs or browser-exposed `import.meta.env` usage.
9. Obtain compliance sign-off recorded outside the repository.
10. Promote the deploy to production.
11. Verify the production URL routes, sitemap, robots file, security headers, and Lighthouse scores.
12. Update README with the live URL only after the production URL works.

## Required Route Checks

Verify:

- `/`
- `/matrix/panel-hospitals`
- `/status`
- `/share/11111111-2222-4333-8444-555555555555`
- `/sitemap.xml`
- `/robots.txt`

Use:

```sh
python scripts/staging_preflight.py --origin "$STAGING_ORIGIN" --output output/staging-preflight/preflight.json
```

## Cloudflare Pages Fallback

Use Cloudflare Pages only if Netlify restore is blocked.

Equivalent settings:

- Root directory: `src/be-sure-ance-app`
- Build command: `npm run build`
- Output directory: `dist`
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
