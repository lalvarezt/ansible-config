"""Exercise package selection and installer results without installing software."""

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import hashlib
import zipfile
import importlib.util
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
ANSIBLE = ROOT / "ansible"


class PrivateInventoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location(
            "chezmoi_inventory", ANSIBLE / "inventory/chezmoi.py")
        cls.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.module)

    def test_only_current_private_hostname_is_imported(self):
        data = {
            "chezmoi": {"hostname": "current.example.invalid"},
            "hosts": {
                "current.example.invalid": {"ansible_profile": "pentest-laptop"},
                "other.example.invalid": {"ansible_profile": "work-wsl"},
            },
        }
        result = self.module.inventory(data)
        self.assertEqual(result["all"]["hosts"], ["pentest-laptop"])
        self.assertEqual(result["_meta"]["hostvars"], {
            "pentest-laptop": {"ansible_host": "current.example.invalid"},
        })

    def test_unconfigured_machine_does_not_import_other_hosts(self):
        self.assertEqual(self.module.inventory({}), {"_meta": {"hostvars": {}}})

    def test_unknown_private_profile_is_rejected(self):
        with self.assertRaises(ValueError):
            self.module.inventory({
                "chezmoi": {"hostname": "current.example.invalid"},
                "hosts": {"current.example.invalid": {"ansible_profile": "invalid"}},
            })

    def test_initial_bootstrap_does_not_require_chezmoi(self):
        with patch.object(self.module.shutil, "which", return_value=None), \
                patch.object(sys, "argv", ["chezmoi.py", "--list"]), \
                patch("builtins.print") as output:
            self.assertEqual(self.module.main(), 0)
        self.assertEqual(json.loads(output.call_args.args[0]), {"_meta": {"hostvars": {}}})


class BootstrapTests(unittest.TestCase):
    def run_play(self, tasks, variables=None, vars_files=None):
        with tempfile.TemporaryDirectory() as directory:
            play = Path(directory) / "play.json"
            play.write_text(json.dumps([{
                "name": "Bootstrap regression checks",
                "hosts": "localhost",
                "gather_facts": False,
                "vars": {
                    "ansible_python_interpreter": "{{ ansible_playbook_python }}",
                    **(variables or {}),
                },
                "vars_files": vars_files or [],
                "tasks": tasks,
                "handlers": [{
                    "name": "Refresh font cache",
                    "ansible.builtin.debug": {"msg": "Font extraction requested a cache refresh"},
                }],
            }]))
            return subprocess.run(
                ["ansible-playbook", "-i", "localhost,", "-c", "local", str(play)],
                cwd=ANSIBLE, text=True, capture_output=True,
                env={**os.environ, "ANSIBLE_BECOME_ASK_PASS": "False"},
                timeout=60,
            )

    def test_default_selection_excludes_opt_in_packages(self):
        self.check_selection(["development", "core", "shell"], False)

    def test_ai_selection_includes_ai_packages(self):
        self.check_selection(["ai"], True)

    def check_selection(self, modules, ai_expected):
        result = self.run_play([
            {"ansible.builtin.include_tasks": str(
                ANSIBLE / "roles/package_installer/tasks/aggregate.yml")},
            {"ansible.builtin.assert": {"that": [
                f"('claude-code' in (post_install_tasks | map(attribute='name') | list)) == {str(ai_expected).lower()}",
                f"('ollama' in brew_packages) == {str(ai_expected).lower()}",
                "'qemu' not in brew_packages",
            ]}},
        ], {
            "package_dict": "{{ packages_a_f | combine(packages_g_n) | combine(packages_o_z) }}",
            "modules_filter": modules,
        }, [str(p) for p in sorted(
            (ANSIBLE / "inventory/group_vars/all").glob("packages_*.yml"))])
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_uv_results(self):
        for message, exit_code, changed in [
            ("Installed 1 executable: example", 0, True),
            ("Tool `example` is already installed", 0, False),
            ("Executable already exists: example", 1, False),
        ]:
            with self.subTest(message=message), tempfile.TemporaryDirectory() as directory:
                mock = Path(directory) / "uv"
                mock.write_text(
                    f"#!{sys.executable}\nimport sys\n"
                    f"print({message!r}, file=sys.stderr)\nsys.exit({exit_code})\n")
                mock.chmod(0o755)
                result = self.run_play([{
                    "ansible.builtin.include_tasks": str(
                        ANSIBLE / "roles/package_installer/tasks/uv.yml"),
                }], {
                    "uv_bin": str(mock), "ansible_path": os.environ["PATH"],
                    "uv_packages": [{"name": "example", "command": "tool install example"}],
                })
                if exit_code:
                    self.assertNotEqual(result.returncode, 0, result.stdout)
                else:
                    self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertRegex(result.stdout, rf"changed={int(changed)}\s")

    def test_font_archive_is_verified_and_extracted_once(self):
        with tempfile.TemporaryDirectory() as directory:
            archive = Path(directory) / "fixture.zip"
            with zipfile.ZipFile(archive, "w") as zipped:
                zipped.writestr("fixture.ttf", "fixture font bytes")
            checksum = "sha256:" + hashlib.sha256(archive.read_bytes()).hexdigest()
            variables = {
                "ansible_facts": {"user_dir": directory},
                "font_package": {
                    "name": "fixture", "url": archive.as_uri(), "checksum": checksum,
                },
            }
            tasks = [{"ansible.builtin.include_tasks": str(
                ANSIBLE / "roles/package_installer/tasks/font.yml")}]
            for attempt in range(2):
                result = self.run_play(tasks, variables)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                if attempt:
                    self.assertRegex(result.stdout, r"changed=0\s")
            self.assertEqual(
                (Path(directory) / ".local/share/fonts/fixture/fixture.ttf").read_text(),
                "fixture font bytes",
            )
            variables["font_package"]["checksum"] = "sha256:" + "0" * 64
            result = self.run_play(tasks, variables)
            self.assertNotEqual(result.returncode, 0, result.stdout)
            self.assertIn("checksum", result.stdout.lower())

    def test_module_listing_reads_all_catalogs(self):
        result = subprocess.run(
            [str(ROOT / "scripts/list-modules.sh"), "--verbose"],
            text=True, capture_output=True, timeout=30,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        for package in ["fish", "neovim", "zoxide"]:
            self.assertIn(f"  - {package}\n", result.stdout)
        self.assertNotIn("---", result.stdout)

    def test_wsl_clone_uses_temporary_agent_and_cleans_up(self):
        for exit_code in [0, 42]:
            with self.subTest(exit_code=exit_code), tempfile.TemporaryDirectory() as directory:
                base = Path(directory)
                marker = base / "agent-path"
                socat = base / "socat"
                socat.write_text(
                    f"#!{sys.executable}\nimport socket, sys, time\n"
                    "path = sys.argv[1].split(':', 1)[1].split(',')[0]\n"
                    "sock = socket.socket(socket.AF_UNIX)\n"
                    "sock.bind(path)\nsock.listen()\ntime.sleep(60)\n")
                socat.chmod(0o755)
                chezmoi = base / "chezmoi"
                chezmoi.write_text(
                    f"#!{sys.executable}\nimport os, pathlib, socket, sys\n"
                    "if sys.argv[1] == 'init':\n"
                    "    path = os.environ['SSH_AUTH_SOCK']\n"
                    "    sock = socket.socket(socket.AF_UNIX)\n"
                    "    sock.connect(path)\n"
                    f"    pathlib.Path({str(marker)!r}).write_text(path)\n"
                    f"    sys.exit({exit_code})\n")
                chezmoi.chmod(0o755)
                result = self.run_play([
                    {"ansible.builtin.include_role": {"name": "chezmoi"}},
                ], {
                    "ansible_facts": {"user_dir": directory},
                    "is_wsl": True,
                    "npiperelay_path": "/mnt/c/Users/Fake User/go/bin/npiperelay.exe",
                    "ansible_path": directory + os.pathsep + os.environ["PATH"],
                })
                if exit_code:
                    self.assertNotEqual(result.returncode, 0, result.stdout)
                else:
                    self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertTrue(marker.exists(), result.stdout + result.stderr)
                self.assertFalse(Path(marker.read_text()).parent.exists())

    def test_tagged_bootstrap_requires_single_host(self):
        result = subprocess.run(
            ["ansible-playbook", "-i", "inventory/hosts.yml", "playbooks/bootstrap.yml", "--tags", "config", "--check"],
            cwd=ANSIBLE, text=True, capture_output=True, timeout=60,
            env={**os.environ, "ANSIBLE_BECOME_ASK_PASS": "False"},
        )
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertIn("Select exactly one local inventory profile", result.stdout)
        self.assertNotIn("TASK [chezmoi", result.stdout)


if __name__ == "__main__":
    unittest.main()
