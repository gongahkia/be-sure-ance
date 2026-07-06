#!/usr/bin/env bash
set -euo pipefail

data_path="src/be-sure-ance-app/public/data/app-data.json"

if [ -z "${COMMIT_REF:-}" ] || [ -z "${CACHED_COMMIT_REF:-}" ]; then
  exit 1
fi

if ! changed_files="$(git diff --name-only "$CACHED_COMMIT_REF" "$COMMIT_REF")"; then
  exit 1
fi

if [ -z "$changed_files" ]; then
  exit 0
fi

non_data_changes="$(printf '%s\n' "$changed_files" | grep -v -x "$data_path" || true)"
subject="$(git log -1 --pretty=%s "$COMMIT_REF")"

if [ -z "$non_data_changes" ] && [[ "$subject" == "chore(data): refresh static app data"* ]]; then
  echo "Skipping automatic Netlify build for scheduled data refresh commit."
  exit 0
fi

exit 1
