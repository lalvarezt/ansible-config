#!/usr/bin/env python3
"""Read the current machine's hostname from private chezmoi data at runtime."""

import argparse
import json
import shutil
import subprocess
import sys


PROFILES = {"pentest-laptop", "work-wsl", "work-laptop", "home-desktop", "work-desktop"}


def inventory(data):
    result = {"_meta": {"hostvars": {}}}
    hostname = data.get("chezmoi", {}).get("hostname")
    host = data.get("hosts", {}).get(hostname, {})
    profile = host.get("ansible_profile")
    if profile is None:
        return result
    if profile not in PROFILES:
        raise ValueError("Private ansible_profile must name a supported generic profile")
    result["_meta"]["hostvars"][profile] = {"ansible_host": hostname}
    result["all"] = {"hosts": [profile]}
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    options = parser.add_mutually_exclusive_group(required=True)
    options.add_argument("--list", action="store_true")
    options.add_argument("--host")
    args = parser.parse_args()
    if args.host or not shutil.which("chezmoi"):
        print("{}" if args.host else '{"_meta": {"hostvars": {}}}')
        return 0
    try:
        process = subprocess.run(
            ["chezmoi", "data", "--format", "json"],
            capture_output=True, text=True, timeout=15, check=True,
        )
        print(json.dumps(inventory(json.loads(process.stdout))))
        return 0
    except (OSError, subprocess.SubprocessError, ValueError, TypeError, AttributeError):
        print("Cannot read private chezmoi inventory data; check ansible_profile configuration.", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
