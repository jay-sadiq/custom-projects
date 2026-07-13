#!/usr/bin/env bash
set -euo pipefail

FLAVOR="${1:-dev}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

CONFIG="config/${FLAVOR}.json"
if [[ ! -f "$CONFIG" ]]; then
  echo "Unknown flavor: $FLAVOR (expected dev, staging, or prod)" >&2
  exit 1
fi

echo "Building Android app bundle for flavor: $FLAVOR"
flutter pub get
flutter build appbundle --release --flavor "$FLAVOR" --dart-define-from-file="$CONFIG"
echo "Output: build/app/outputs/bundle/${FLAVOR}Release/app-${FLAVOR}-release.aab"
