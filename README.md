# 🙈 My Ansible Bootstrapping Config

Ansible-based system bootstrapping for Linux workstations. Automates installation of 100+ development tools,
shell utilities, and system packages across multiple distributions.

## Features

- **Multi-distribution support**: `Ubuntu`, `Fedora`, `Arch Linux`, `EndeavourOS`, `WSL`
- **Modular package management**: Filter by category, installer type, or functionality
- **Multiple installers**: `Homebrew`, `apt`, `dnf`, `pacman`, `yay`, `uv`, `cargo`, `go`
- **Linux fonts**: Checksum-pinned JetBrains Mono Nerd Font and Maple Mono archives installed under `~/.local/share/fonts`
- **1Password integration**: Secure SSH key retrieval during bootstrap
- **Dotfiles via Chezmoi**: Ansible bootstraps and applies the [chezmoi repository](https://gitlab.com/lalvarezt/chezmoi), which remains the source of truth for persistent user configuration

## Prerequisites

Before bootstrapping, ensure you have:

### Required

1. **1Password account** with CLI access
2. **SSH keys stored in 1Password** at path: `op://Private/SSH Keys/id_ed25519`
3. **Network access** to clone the `chezmoi` repository
4. **ansible-core 2.18 or newer**, with `community.general` 13.5.0

### Optional

- **yq** - Required for `list-modules.sh` utility (installed during bootstrap)

## Quick Start

### 1. Install Ansible

```bash
./scripts/bootstrap.sh
```

The script also installs the pinned collection requirements. If Ansible is
already installed, you can install them with `ansible-galaxy collection install -r requirements.yml`.

### 2. Sign in to 1Password

```bash
eval $(op signin)
```

### 3. Run the bootstrap playbook

```bash
cd ansible
ansible-playbook playbooks/bootstrap.yml -l <hostname>
```

Available profiles: `pentest-laptop`, `work-wsl`, `work-laptop`, `home-desktop`,
and `work-desktop`. `work-wsl` uses Fedora. The Windows host itself is outside
this Linux playbook's scope.

All profiles use a local connection. Run the playbook on the target machine and
select exactly one profile with `-l`. Selecting a hostname does not connect to it remotely.

Real hostnames belong in the private chezmoi repository. Set `ansible_profile`
on each entry in its `.chezmoidata.yaml` to one of the generic profiles above.
For example, a private host entry can contain `ansible_profile: pentest-laptop`.
The inventory reads `chezmoi data --format json` at runtime and sets `ansible_host`
for the current machine's profile. No private inventory is written into this repo.
Before chezmoi is installed, generic profiles still work for the initial bootstrap.
Use `-i inventory/hosts.yml` to load only the public profiles, including in CI.

You will be prompted for your sudo password (become password).

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
ansible-playbook playbooks/bootstrap.yml -l <hostname>

# Skip pentesting tools
ansible-playbook playbooks/bootstrap.yml -l <hostname> --skip-tags pentesting

# Only install packages (skip setup and config)
ansible-playbook playbooks/bootstrap.yml -l <hostname> --tags packages,pentesting

# Only run setup
ansible-playbook playbooks/bootstrap.yml -l <hostname> --tags setup
```

## Filtering Packages

Use `--extra-vars "modules=[...]"` to filter which packages are installed by tag or installer type.

### By Package Tag

```bash
# Only core packages
ansible-playbook playbooks/bootstrap.yml -l <hostname> --extra-vars "modules=['core']"

# Only shell tools
ansible-playbook playbooks/bootstrap.yml -l <hostname> --extra-vars "modules=['shell']"

# Only pentesting tools
ansible-playbook playbooks/bootstrap.yml -l <hostname> --tags pentesting --extra-vars "modules=['pentesting']"
```

Available tags: `core`, `optional`, `ai`, `shell`, `files`, `development`, `git`, `pentesting`, `data`, `search`, `package-managers`, `misc`, `fonts`

Packages tagged `ai` or `optional` require that tag explicitly in `modules`, even
when another tag such as `development` matches. Category and installer filters
otherwise use OR logic. An empty `modules` list selects all packages except these opt-in packages.

List all available modules:

```bash
./scripts/list-modules.sh           # List modules
./scripts/list-modules.sh --verbose # Show packages per module
```

### By Installer Type

```bash
# Only brew packages
ansible-playbook playbooks/bootstrap.yml -l <hostname> --extra-vars "modules=['brew']"

# Only uv-installed packages
ansible-playbook playbooks/bootstrap.yml -l <hostname> --extra-vars "modules=['uv']"

# Only go packages
ansible-playbook playbooks/bootstrap.yml -l <hostname> --extra-vars "modules=['go']"

# Only cargo packages
ansible-playbook playbooks/bootstrap.yml -l <hostname> --extra-vars "modules=['cargo']"

# Only native packages (apt/dnf/pacman)
ansible-playbook playbooks/bootstrap.yml -l <hostname> --extra-vars "modules=['native']"
```

### Combined Filtering

```bash
# Development or core tools
ansible-playbook playbooks/bootstrap.yml -l <hostname> --extra-vars "modules=['development','core']"

# Pentesting or Go tools, including the pentesting playbook
ansible-playbook playbooks/bootstrap.yml -l <hostname> --tags packages,pentesting --extra-vars "modules=['pentesting','go']"

# Multiple categories (OR logic)
ansible-playbook playbooks/bootstrap.yml -l <hostname> --extra-vars "modules=['shell','files']"
```

### Dry Run

```bash
ansible-playbook playbooks/bootstrap.yml -l <hostname> --check
```

Check mode validates only the tasks that support it. Command-based installers
and the chezmoi apply command are skipped, so this does not prove a fresh install succeeds.

## Repository Boundaries

- `ansible-config` owns machine bootstrap: OS prerequisites, package managers, package installation, secrets retrieval, and service enablement
- `chezmoi` owns persistent user configuration: shell startup files, dotfiles, templates, and external dotfile assets
- The `config` playbook should be safe to rerun because it reapplies `chezmoi` instead of treating dotfiles as a first-boot-only step

### OpenSSH and GnuPG-agent forwarding

The client-side forwarding configuration lives in chezmoi. On Linux hosts, run the
configuration playbook once after pulling this change so `sshd` can replace a
stale `/run/user/1000/gnupg/S.gpg-agent` socket:

```bash
ansible-playbook playbooks/03-config.yml -l <hostname> --tags config
```

After the playbook reloads `sshd`, an `ssh -A user@target-host`
session can carry both the SSH agent and the restricted OpenPGP agent socket.

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
│       ├── chezmoi.py        # Runtime private hostname lookup
│       └── group_vars/
│           ├── all/          # vars.yml and packages_a_f.yml, packages_g_n.yml, packages_o_z.yml
│           ├── ubuntu.yml
│           ├── fedora.yml
│           ├── arch.yml
│           └── wsl.yml
```

## Customization

### Adding Packages

Add the package under the matching `packages_a_f`, `packages_g_n`, or `packages_o_z`
key in `ansible/inventory/group_vars/all/packages_*.yml`. Example entry:

```yaml
package_name:
  brew:
    name: package-name
  description: Brief description of the package
  tags:
    - development
    - core
```

Available tags: `core` (essential), `optional`, `ai`, `shell`, `files`, `development`, `git`, `pentesting`, `data`, `search`, `package-managers`, `misc`, `fonts`

### Post-Install Commands

Some packages need additional setup after installation. Use `post_install` to run commands automatically:

```yaml
secator:
  uv:
    ansible.builtin.command: tool install git+https://github.com/freelabz/secator --with pip
  description: The pentester's swiss knife
  tags:
    - pentesting
  post_install:
    - secator install addons worker
    - secator install addons redis
    - secator config set celery.broker_url redis://127.0.0.1:6379/0
```

### Changing Chezmoi Repository

Edit `ansible/roles/chezmoi/defaults/main.yml` and update the `chezmoi_repo_url` variable.

### Host-specific Overrides

Create `ansible/inventory/host_vars/<inventory-hostname>.yml` for machine-specific settings.

## Validation

Install uv and Mike Farah's yq v4 on PATH. Enable the pre-push hook once per clone:

```bash
git config core.hooksPath .githooks
./scripts/check.sh
```

Every push runs the same script as CI. Commit or stash tracked changes before
pushing. The script uses Python 3.13 and the tool versions in
`requirements-check.txt`, installs the required Ansible collections, then runs
YAML lint, bootstrap regression tests, Ansible lint, and playbook syntax checks.
The first run needs network access to download Python, tools, and collections.

The regression tests exercise the real aggregation and installer tasks against
temporary inputs. They do not install workstation packages or apply dotfiles.
CI installs uv 0.13.7 from PyPI to avoid the GitHub release download that returned
HTTP 504 in the failed run. Local checks cannot prevent CI network outages.

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.
