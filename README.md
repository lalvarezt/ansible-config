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

- **yq** - Required for `list-modules.sh` utility (installed during bootstrap)

## Quick Start

### 1. Install Ansible

```bash
./scripts/bootstrap.sh
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

## Playbook Tags

Use `--tags` or `--skip-tags` to control which playbooks run:

| Tag | Playbook | Description |
|-----|----------|-------------|
| `setup` | 00-setup.yml | System prerequisites, 1Password, SSH, Homebrew, language managers |
| `packages` | 01-packages.yml | All tool packages (shell, files, dev, git, data, search, misc, fonts) |
| `pentesting` | 02-pentesting.yml | Pentesting and security tools |
| `config` | 03-config.yml | Chezmoi dotfiles and post-configuration |

```bash
# Full bootstrap
ansible-playbook playbooks/bootstrap.yml

# Skip pentesting tools
ansible-playbook playbooks/bootstrap.yml --skip-tags pentesting

# Only install packages (skip setup and config)
ansible-playbook playbooks/bootstrap.yml --tags packages,pentesting

# Only run setup
ansible-playbook playbooks/bootstrap.yml --tags setup
```

## Filtering Packages

Use `--extra-vars "modules=[...]"` to filter which packages are installed by tag or installer type.

### By Package Tag

```bash
# Only core packages
ansible-playbook playbooks/bootstrap.yml --extra-vars "modules=['core']"

# Only shell tools
ansible-playbook playbooks/bootstrap.yml --extra-vars "modules=['shell']"

# Only pentesting tools
ansible-playbook playbooks/bootstrap.yml --extra-vars "modules=['pentesting']"
```

Available tags: `core`, `shell`, `files`, `development`, `git`, `pentesting`, `data`, `search`, `package-managers`, `misc`, `fonts`

List all available modules:

```bash
./scripts/list-modules.sh           # List modules
./scripts/list-modules.sh --verbose # Show packages per module
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
# Core development tools
ansible-playbook playbooks/bootstrap.yml --extra-vars "modules=['development','core']"

# Pentesting tools installed via go
ansible-playbook playbooks/bootstrap.yml --extra-vars "modules=['pentesting','go']"

# Multiple categories (OR logic)
ansible-playbook playbooks/bootstrap.yml --extra-vars "modules=['shell','files']"
```

### Dry Run

```bash
ansible-playbook playbooks/bootstrap.yml --check
```

## Project Structure

```
ansible-config/
├── scripts/
│   ├── bootstrap.sh          # Initial Ansible installation
│   └── list-modules.sh       # Package module discovery utility
├── ansible/
│   ├── playbooks/
│   │   ├── bootstrap.yml     # Main orchestrator
│   │   ├── 00-setup.yml      # System prerequisites, 1Password, SSH, Homebrew
│   │   ├── 01-packages.yml   # All tool packages
│   │   ├── 02-pentesting.yml # Pentesting and security tools
│   │   └── 03-config.yml     # Chezmoi dotfiles and post-configuration
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
  description: Brief description of the package
  tags:
    - development
    - core
```

Available tags: `core` (essential), `shell`, `files`, `development`, `git`, `pentesting`, `data`, `search`, `package-managers`, `misc`, `fonts`

### Changing Chezmoi Repository

Edit `ansible/roles/chezmoi/defaults/main.yml` and update the `chezmoi_repo_url` variable.

### Host-specific Overrides

Edit `ansible/inventory/host_vars/localhost.yml` for machine-specific settings.

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.
