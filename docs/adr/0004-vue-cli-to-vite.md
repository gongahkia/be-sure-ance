# ADR 0004: Migrate Frontend From Vue CLI To Vite

## Status

Accepted.

## Context

The frontend had been built around Vue CLI conventions. The pivot requires a maintainable static app with fast local builds, current tooling, and predictable environment-variable behavior.

The repository now uses Vite, `import.meta.env`, `VITE_*` public variables, flat ESLint config, and Vite static output under `dist`.

## Decision

Use Vite as the frontend build tool. Keep the app as Vue 3, keep Netlify or Cloudflare Pages as static-host candidates, and run static page generation after the Vite build.

Frontend configuration must use only public `VITE_*` values. Private Supabase service keys and bot tokens stay in scraper/backend environments.

## Rejected Approaches

- Stay on Vue CLI. Rejected because it increases maintenance drag and keeps older conventions.
- Migrate to Nuxt or another SSR framework. Rejected because the current need is static output plus a small app shell, not a new application architecture.
- Put backend secrets into the frontend build for convenience. Rejected because it would expose write credentials.

## Consequences

- Local frontend commands are `npm run dev`, `npm run build`, `npm run lint`, and `npm run format:check` inside `src/be-sure-ance-app`.
- Static plan-page generation runs after Vite build and needs real public Supabase env only for full plan output.
- Deployment remains blocked until Phase 5 even though local static builds work.
