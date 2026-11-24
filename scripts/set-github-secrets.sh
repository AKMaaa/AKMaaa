#!/usr/bin/env bash
# 本番ビルド用 GitHub Actions Secrets を .env から登録する
set -euo pipefail
cd "$(dirname "$0")/.."

if ! gh auth status >/dev/null 2>&1; then
  echo "先に: gh auth login"
  exit 1
fi

set -a
# shellcheck disable=SC1091
source .env
set +a

for key in \
  MICROCMS_SERVICE_DOMAIN \
  MICROCMS_API_KEY \
  PUBLIC_TURNSTILE_SITE_KEY \
  PUBLIC_CONTACT_API_URL
do
  val="${!key-}"
  if [[ -z "$val" ]]; then
    echo "skip empty: $key"
    continue
  fi
  printf '%s' "$val" | gh secret set "$key" -R AKMaaa/AKMaaa
  echo "set $key"
done

echo "done. Re-run Deploy to GitHub Pages if the last build lacked these secrets."
