# Accessibility Audit

Audit date: 2026-07-02.

Target standard: WCAG 2.1 AA.

References:

- W3C WCAG 2.1: https://www.w3.org/TR/WCAG21/
- Chrome Lighthouse accessibility scoring: https://developer.chrome.com/docs/lighthouse/accessibility/scoring
- axe-core rule tags: https://www.deque.com/axe/core-documentation/api-documentation/

## Scope

Local demo stack:

- Frontend: `http://127.0.0.1:5173`
- Demo Supabase API: `http://127.0.0.1:54321`

Routes audited:

| Route | Axe WCAG 2.1 A/AA violations | Lighthouse accessibility |
| :-- | :-- | :-- |
| `/` | 0 | 100 |
| `/matrix/panel-hospitals` | 0 | 100 |
| `/status` | 0 | 100 |
| `/share/11111111-2222-4333-8444-555555555555` | 0 | 100 |

Raw local artifacts:

- `output/playwright/accessibility/axe-results-after.json`
- `output/playwright/accessibility/lighthouse-workspace.json`
- `output/playwright/accessibility/lighthouse-matrix.json`
- `output/playwright/accessibility/lighthouse-status.json`
- `output/playwright/accessibility/lighthouse-share.json`

## Fixes

- Changed the panel matrix and scraper status route wrappers to `main` landmarks so every route has a main landmark.
- Made the horizontally scrollable scraper-status table focusable with a named scroll region.
- Added a visible focus outline for the scraper-status scroll region.

## Keyboard Coverage

Primary keyboard-only workflows covered by current markup:

- Hero navigation exposes real links for plan workspace, panel matrix, and scraper status.
- Provider rail carrier selection uses native buttons.
- Search inputs are native labeled-by-context controls with visible focus.
- Plan shortlist actions use native buttons.
- Share-link creation uses a native button and the generated link is a real anchor.
- The status table scroll region is keyboard-focusable for horizontal scroll access.

## Exceptions

No automated WCAG 2.1 A/AA violations remain in the audited routes.

Manual screen-reader testing is still required before Phase 5 public relaunch because automated tools cannot prove full WCAG conformance.
