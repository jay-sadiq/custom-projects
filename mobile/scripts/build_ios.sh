#!/usr/bin/env bash
set -euo pipefail

FLAVOR="${1:-prod}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

CONFIG="config/${FLAVOR}.json"
if [[ ! -f "$CONFIG" ]]; then
  echo "Unknown flavor: $FLAVOR (expected dev, staging, or prod)" >&2
  exit 1
fi

echo "Building iOS archive for flavor: $FLAVOR"
flutter pub get
flutter build ipa --release --flavor "$FLAVOR" --dart-define-from-file="$CONFIG"
echo "Output: build/ios/ipa/*.ipa"
