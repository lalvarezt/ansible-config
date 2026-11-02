#!/bin/bash
# Dotfiles Bootstrap Script
# Installs Ansible to prepare for running the bootstrap playbook

set -e

# Help menu
show_help() {
  cat <<EOF
Usage: ./bootstrap.sh [OPTIONS]

Installs Ansible on your system to prepare for running the dotfiles playbook.

Options:
  --help          Show this help message and exit

This script installs Ansible and its collections. After installation, run the
playbook manually using the suggested commands.
EOF
  exit 0
}

# Parse arguments
for arg in "$@"; do
  case $arg in
  --help)
    show_help
    ;;
  *)
    echo "Error: Unknown argument: $arg"
    echo "Run ./bootstrap.sh --help for usage information"
    exit 1
    ;;
  esac
done

echo "=== Dotfiles Bootstrap with Ansible ==="
echo ""

# Detect OS
if [ -f /etc/os-release ]; then
  # shellcheck source=/dev/null
  . /etc/os-release
  OS=$ID
else
  echo "Error: Cannot detect OS"
  exit 1
fi

echo "Detected OS: $OS"
echo ""

# Check if Ansible is already installed
if command -v ansible-playbook >/dev/null 2>&1; then
  echo "Ansible is already installed: $(ansible --version | head -n1)"
else
  # Install Ansible based on OS
  echo "Installing Ansible for $OS..."
  case $OS in
  ubuntu | debian)
    sudo apt update
    sudo apt install -y ansible
    ;;
  fedora)
    sudo dnf install -y ansible
    ;;
  arch | archlinux | endeavouros)
    sudo pacman -S --noconfirm ansible
    ;;
  *)
    echo "Error: Unsupported OS: $OS"
    echo "Please install Ansible manually and re-run this script"
    exit 1
    ;;
  esac
  echo "Ansible installed successfully"
fi

ANSIBLE_CORE_VERSION=$(ansible-playbook --version | sed -n '1s/.*core \([0-9.]*\).*/\1/p')
if [[ -z "$ANSIBLE_CORE_VERSION" ]] ||
  [[ "$(printf '%s\n' 2.18 "$ANSIBLE_CORE_VERSION" | sort -V | head -n1)" != 2.18 ]]; then
  echo "Error: ansible-core 2.18 or newer is required by community.general."
  echo "Upgrade Ansible and re-run this script."
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ansible-galaxy collection install -r "$SCRIPT_DIR/../requirements.yml"

echo ""
echo "=== Ansible Installation Complete ==="
echo ""
echo "Next steps:"
echo ""
echo "1. Run the bootstrap playbook:"
echo "   cd ansible"
echo "   ansible-playbook playbooks/bootstrap.yml -l <hostname> -K"
echo ""
echo "   Available profiles: pentest-laptop, work-wsl, work-laptop, home-desktop, work-desktop"
echo ""
echo "2. Optional flags you can use:"
echo "   --check           Dry run (see what would change without making changes)"
echo "   --tags TAG        Run only specific playbooks (e.g., --tags packages)"
echo "   --skip-tags TAG   Skip specific tagged tasks"
echo "   -v, -vv, -vvv     Verbose output (more v's = more verbose)"
echo "   --ask-become-pass Prompt for sudo password if needed"
echo ""
echo "3. Example commands:"
echo "   ansible-playbook playbooks/bootstrap.yml -l <hostname> --check"
echo "   ansible-playbook playbooks/bootstrap.yml -l <hostname> --tags packages --extra-vars \"modules=['shell']\""
echo "   ansible-playbook playbooks/bootstrap.yml -l <hostname> -v"
