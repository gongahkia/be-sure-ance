# ADR 0006: Defer Chrome MV3 Sidebar Extension

## Status

Accepted - defer implementation.

## Context

Issue #55 asks whether to build a Chrome MV3 extension that highlights plan names on carrier pages and opens a sidebar fact card.

The extension is feasible, but it is not required for Phase 3 exit. Phase 3 already prioritizes the starter combo and data/workflow moats: panel matrix, PDF brief export, static plan pages, saved shares, Telegram lookup, brochure history, claim evidence, taxonomy, and MAS feed.

Current Chrome extension references checked on 2026-07-02:

- Chrome `chrome.sidePanel` docs: https://developer.chrome.com/docs/extensions/reference/api/sidePanel
- Chrome permissions docs: https://developer.chrome.com/docs/extensions/develop/concepts/declare-permissions
- Chrome permissions reference: https://developer.chrome.com/docs/extensions/reference/permissions-list

## Feasibility

Chrome MV3 supports the intended UI:

- `side_panel.default_path` can load an extension sidebar page.
- `chrome.sidePanel.open()` can open the side panel from a user gesture.
- Content scripts can read and modify page DOM when host permissions allow it.
- Host permissions and API permissions must be explicitly declared and reviewed.

## Proposed MVP Scope

If restarted, the MVP should include:

- MV3 `manifest.json` with `sidePanel`, `action`, `scripting`, and narrow `host_permissions` for supported carrier domains only.
- Content script that scans visible page text for known plan names and adds non-destructive highlights.
- Click or toolbar gesture that opens a side panel for the detected plan.
- Sidebar fact card showing plan name, carrier, source-traceable facts, source URLs, verified dates, and no-advice copy.
- Read-only data access through a public API or Supabase anon read path. No service-role key, bot token, client data, or agent data in the extension.
- Local cache only for public plan/fact metadata, with clear expiry and no visitor tracking.

## Decision

Defer extension implementation until after Phase 3 exit verification.

Rationale:

- The extension is workflow-adjacent, not required for the demo-ready starter combo.
- It adds a new browser-permission review surface.
- It needs a stable deployed data endpoint and a clearer privacy policy before user testing.
- Building it now would compete with Phase 3 exit work and Phase 4 portfolio readiness.

## Rejected Approaches

- Build the extension during Phase 3. Rejected because the starter combo and data moats already satisfy Phase 3 exit.
- Add broad host permissions for all carrier pages. Rejected because it expands review and privacy risk.
- Ship an extension before a stable public endpoint exists. Rejected because stale-cache and no-advice behavior would be hard to verify.

## Blockers

- Production/staging endpoint for public read-only plan facts is not launch-approved yet.
- Extension privacy copy and Chrome Web Store disclosure are not drafted.
- Supported carrier-domain permission list is not finalized.
- DOM-highlighting QA across carrier sites is not done.
- No policy for cache expiry, stale fact display, or extension takedown handling exists yet.

## Restart Conditions

Restart only when all are true:

- Phase 3 exit criteria are met and documented.
- Phase 4 has capacity for browser-extension QA.
- Public data endpoint and no-advice copy are stable.
- Carrier-domain host permission list is explicit and minimal.
- A Chrome Web Store privacy/disclosure checklist exists.

## Follow-up Issues If Approved

Create these implementation issues only after the restart conditions are met:

- Build MV3 manifest, service worker, and side panel shell.
- Implement plan-name content-script highlighter for supported carrier domains.
- Implement sidebar fact card with provenance and no-advice copy.
- Add read-only data API/cache layer for extension use.
- Add extension permission/privacy QA and packaging checks.

## Consequences

- No extension work blocks Phase 3 exit.
- Future extension work has a bounded MVP and explicit privacy constraints.
- The repo avoids adding `src/extension` source until the build decision changes.
