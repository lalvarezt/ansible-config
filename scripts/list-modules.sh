#!/usr/bin/env bash
# List all modules or packages grouped by module

set -euo pipefail

usage() {
  cat <<EOF
Usage: $(basename "$0") [OPTIONS]

List all available package modules from the Ansible configuration.
These modules can be used with --extra-vars "modules=[...]" to filter packages.

Options:
    -v, --verbose    Show packages grouped by each module (YAML format)
    -h, --help       Show this help message

Examples:
    $(basename "$0")              # List all modules
    $(basename "$0") --verbose    # Show packages for each module
EOF
}

VERBOSE=false

while [[ $# -gt 0 ]]; do
  case $1 in
  -v | --verbose)
    VERBOSE=true
    shift
    ;;
  -h | --help)
    usage
    exit 0
    ;;
  *)
    echo "Error: unknown option '$1'" >&2
    usage >&2
    exit 1
    ;;
  esac
done

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
CATALOG_DIR="$SCRIPT_DIR/../ansible/inventory/group_vars/all"
CATALOG_FILES=("$CATALOG_DIR"/packages_*.yml)

if [[ ! -f "${CATALOG_FILES[0]}" ]]; then
  echo "Error: no package catalogs found in $CATALOG_DIR" >&2
  exit 1
fi

if [[ "$VERBOSE" == true ]]; then
  for tag in $(yq --no-doc '.. | select(has("tags")) | .tags[]' "${CATALOG_FILES[@]}" | sort -u); do
    echo "$tag:"
    yq --no-doc ".. | select(has(\"tags\") and .tags[] == \"$tag\") | path | .[-1]" "${CATALOG_FILES[@]}" | sort -u | sed 's/^/  - /'
  done
else
  yq --no-doc '.. | select(has("tags")) | .tags[]' "${CATALOG_FILES[@]}" | sort -u
fi
