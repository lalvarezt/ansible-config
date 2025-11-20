# ansible-config
🙈 My Ansible Bootstrapping Config

Dotfiles managed with chezmoi, automated with Ansible.

## Quick Start

1. **Install Ansible**

```bash
./bootstrap.sh
```

2. **Run the bootstrap playbook**

```bash
cd ansible
ansible-playbook playbooks/bootstrap.yml
  ```

This installs all packages, configures 1Password CLI, sets up SSH keys, and applies chezmoi.

## Filtering Packages

Use `--tags` to select playbooks and `--extra-vars "modules=[...]"` to filter packages within them.

### By Playbook Tag

```bash
# Run specific playbooks
ansible-playbook playbooks/bootstrap.yml --tags pentesting
ansible-playbook playbooks/bootstrap.yml --tags development,git
ansible-playbook playbooks/bootstrap.yml --tags shell,files,search
```

Available tags: `shell`, `files`, `development`, `package-managers`, `git`, `pentesting`, `data`, `search`, `misc`, `fonts`

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

List all packages by tag:

```bash
./list-tags.sh
```

### By Installer Type

Filter by how packages are installed (auto-detected):

```bash
# Only uv-installed packages
ansible-playbook playbooks/bootstrap.yml --extra-vars "modules=['uv']"

# Only brew packages
ansible-playbook playbooks/bootstrap.yml --extra-vars "modules=['brew']"

# Only go packages
ansible-playbook playbooks/bootstrap.yml --extra-vars "modules=['go']"
```

Available: `brew`, `uv`, `go`, `cargo`, `native`

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

## WSL Configuration

### .wslconfig (Windows side)

```text
[wsl2]
memory=16GB
guiApplications=true
gpuSupport=true
swapFile="D:\\Docker\\wsl\\swap\\swap.vhdx"
localhostforwarding=true
kernelCommandLine = cgroup_no_v1=all systemd.unified_cgroup_hierarchy=1 sysctl.vm.max_map_count=262144

[experimental]
sparseVhd=true
autoMemoryReclaim=gradual
```

### /etc/wsl.conf (inside distro)

```text
[boot]
systemd=true

[interop]
enabled=false
appendWindowsPath=false

[network]
hostname=<NAME>
generateHosts=false

[user]
default = "lalvarezt"
```

### Zscaler Certificate

```bash
# Ubuntu
sudo openssl x509 -inform DER -in ~/zscaler.cer -out /usr/local/share/ca-certificates/zscaler.crt && sudo update-ca-certificates -f

# Fedora
sudo dnf install openssl --setopt=sslverify=false
sudo openssl x509 -inform DER -in ~/zscaler.cer -out /etc/pki/ca-trust/source/anchors/zscaler.crt && sudo update-ca-trust extract
```

### Display Issues

```bash
sudo rm -r /tmp/.X11-unix
ln -s /mnt/wslg/.X11-unix /tmp/.X11-unix
```
