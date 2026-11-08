#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

for tool in uv yq; do
  if ! command -v "$tool" >/dev/null 2>&1; then
    echo "Error: $tool is required. See README.md, Validation." >&2
    exit 1
  fi
done
if [[ "$(yq --version)" != *"mikefarah/yq/"*"version v4."* ]]; then
  echo "Error: Mike Farah's yq v4 is required." >&2
  exit 1
fi

run() {
  uv run --no-project --python 3.13 --with-requirements "$ROOT/requirements-check.txt" "$@"
}

run ansible-galaxy collection install -r requirements.yml
run yamllint -d relaxed ansible/ .github/workflows/
run python -m unittest discover -s tests -v
cd ansible
run ansible-lint playbooks/*.yml
run ansible-playbook playbooks/*.yml --syntax-check -i inventory/hosts.yml
