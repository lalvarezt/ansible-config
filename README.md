# 🙈 My Ansible Bootstrapping Config

Ansible-based system bootstrapping for Linux workstations. Automates installation of 100+ development tools,
shell utilities, and system packages across multiple distributions.

## Features

- **Multi-distribution support**: `Ubuntu`, `Fedora`, `Arch Linux`, `WSL`
- **Modular package management**: Filter by category, installer type, or functionality
- **Multiple installers**: `Homebrew`, `apt`, `dnf`, `pacman`, `yay`, `paru`, `uv`, `cargo`, `go`
- **1Password integration**: Secure SSH key retrieval during bootstrap
- **Dotfiles via Chezmoi**: Final configuration applied from [chezmoi repository](https://gitlab.com/lalvarezt/chezmoi)

## Prerequisites

Before bootstrapping, ensure you have:

### Required

1. **1Password account** with CLI access
2. **SSH keys stored in 1Password** at path: `op://Private/SSH Keys/id_ed25519`
3. **Network access** to clone the `chezmoi` repository

### Optional

- **yq** - Required for `list-tags.sh` utility (installed during bootstrap)

## Quick Start

### 1. Install Ansible

```bash
./bootstrap.sh
```

### 2. Sign in to 1Password

```bash
eval $(op signin)
```

### 3. Run the bootstrap playbook

```bash
cd ansible
ansible-playbook playbooks/bootstrap.yml
```

This will:

- Install system prerequisites
- Set up `1Password` CLI
- Retrieve SSH keys from `1Password`
- Install `Homebrew` and language managers (`uv`, `go`, `rust`)
- Install all configured packages
- Apply dotfiles via `chezmoi`

### 4. Restart your shell

Log out and back in, or start a new terminal session.

## Filtering Packages

Use `--tags` to select playbooks and `--extra-vars "modules=[...]"` to filter packages.

### By Playbook Tag

```bash
# Run specific playbooks
ansible-playbook playbooks/bootstrap.yml --tags pentesting
ansible-playbook playbooks/bootstrap.yml --tags development,git
ansible-playbook playbooks/bootstrap.yml --tags shell,files,search
```

Available tags: `prereqs`, `core`, `shell`, `terminals`, `files`, `development`, `package-managers`, `git`, `pentesting`, `data`, `search`, `misc`, `fonts`, `config`, `chezmoi`

### By Package Tag

```bash
# Only core packages
ansible-playbook playbooks/bootstrap.yml --extra-vars "modules=['core']"

# Only standard packages
ansible-playbook playbooks/bootstrap.yml --extra-vars "modules=['standard']"

# Filter by functional tags
ansible-playbook playbooks/bootstrap.yml --extra-vars "modules=['fuzzer']"
ansible-playbook playbooks/bootstrap.yml --extra-vars "modules=['scanner']"
```

List all available package tags:

```bash
./list-tags.sh           # List tags
./list-tags.sh --verbose # Show packages per tag
```

### By Installer Type

```bash
# Only brew packages
ansible-playbook playbooks/bootstrap.yml --extra-vars "modules=['brew']"

# Only uv-installed packages
ansible-playbook playbooks/bootstrap.yml --extra-vars "modules=['uv']"

# Only go packages
ansible-playbook playbooks/bootstrap.yml --extra-vars "modules=['go']"

# Only cargo packages
ansible-playbook playbooks/bootstrap.yml --extra-vars "modules=['cargo']"

# Only native packages (apt/dnf/pacman)
ansible-playbook playbooks/bootstrap.yml --extra-vars "modules=['native']"
```

### Combined Filtering

```bash
# Pentesting tools installed via go
ansible-playbook playbooks/bootstrap.yml --tags pentesting --extra-vars "modules=['go']"

# Core development tools
ansible-playbook playbooks/bootstrap.yml --tags development --extra-vars "modules=['core']"

# Multiple filters (OR logic)
ansible-playbook playbooks/bootstrap.yml --extra-vars "modules=['core','scanner']"
```

### Dry Run

```bash
ansible-playbook playbooks/bootstrap.yml --check
```

## Project Structure

```
ansible-config/
├── bootstrap.sh              # Initial Ansible installation
├── list-tags.sh              # Package tag discovery utility
├── ansible/
│   ├── playbooks/            # 20 numbered playbooks
│   │   ├── bootstrap.yml     # Main orchestrator
│   │   ├── 00-prereqs.yml    # System prerequisites
│   │   ├── 01-onepassword.yml
│   │   ├── 02-ssh.yml
│   │   ├── ...
│   │   └── 19-post-config.yml
│   ├── roles/                # Reusable role modules
│   │   ├── system_prereqs/
│   │   ├── onepassword/
│   │   ├── ssh_keys/
│   │   ├── homebrew/
│   │   ├── lang_managers/
│   │   ├── package_installer/
│   │   ├── chezmoi/
│   │   └── ...
│   └── inventory/
│       ├── hosts.yml
│       ├── host_vars/localhost.yml
│       └── group_vars/
│           ├── all.yml       # Global package definitions
│           ├── ubuntu.yml
│           ├── fedora.yml
│           ├── arch.yml
│           └── wsl.yml
```

## Customization

### Adding Packages

Edit `ansible/inventory/group_vars/all.yml`, sample `brew` package:

```yaml
package_name:
  brew:
    name: package-name
  tags:
    - core
    - development
```

### Changing Chezmoi Repository

Edit `ansible/roles/chezmoi/defaults/main.yml` and update the `chezmoi_repo_url` variable.

### Host-specific Overrides

Edit `ansible/inventory/host_vars/localhost.yml` for machine-specific settings.

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.
