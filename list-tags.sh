#!/usr/bin/env bash
# List all packages grouped by tag

set -euo pipefail

# Check required tools
missing=()
for cmd in yq sed sort; do
  command -v "$cmd" &>/dev/null || missing+=("$cmd")
done

if [[ ${#missing[@]} -gt 0 ]]; then
  echo "Error: missing required tools: ${missing[*]}" >&2
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ALL_YML="$SCRIPT_DIR/ansible/inventory/group_vars/all.yml"

if [[ ! -f "$ALL_YML" ]]; then
  echo "Error: $ALL_YML not found" >&2
  exit 1
fi

for tag in $(yq '.. | select(has("tags")) | .tags[]' "$ALL_YML" | sort -u); do
  echo "$tag:"
  yq ".. | select(has(\"tags\") and .tags[] == \"$tag\") | path | .[-1]" "$ALL_YML" | sort | sed 's/^/  - /'
done
