"""Verify that Git's pre-push hook gates the commit being pushed."""

from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


class PrePushTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.repo = Path(self.directory.name)
        self.git("init", "-b", "main")
        self.git("config", "user.name", "Test")
        self.git("config", "user.email", "test@example.invalid")
        self.git("config", "core.hooksPath", ".githooks")
        (self.repo / ".githooks").mkdir()
        shutil.copy2(ROOT / ".githooks/pre-push", self.repo / ".githooks/pre-push")
        (self.repo / "scripts").mkdir()
        self.check = self.repo / "scripts/check.sh"
        self.check.write_text("#!/bin/sh\necho checks-ran\nexit 0\n")
        self.check.chmod(0o755)
        self.git("add", ".")
        self.git("commit", "-m", "Fixture")
        self.head = self.git("rev-parse", "HEAD").strip()

    def git(self, *args):
        return subprocess.run(
            ["git", *args], cwd=self.repo, check=True,
            text=True, capture_output=True,
        ).stdout

    def hook(self, sha=None):
        return subprocess.run(
            [str(self.repo / ".githooks/pre-push"), "origin", "unused"],
            cwd=self.repo, text=True, capture_output=True,
            input=f"refs/heads/main {sha or self.head} refs/heads/main {'0' * 40}\n",
            timeout=10,
        )

    def test_clean_commit_runs_checks(self):
        result = self.hook()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("checks-ran", result.stdout)

    def test_check_failure_blocks_push(self):
        self.check.write_text("#!/bin/sh\necho checks-failed\nexit 42\n")
        self.git("add", ".")
        self.git("commit", "-m", "Fail checks")
        result = self.hook(self.git("rev-parse", "HEAD").strip())
        self.assertEqual(result.returncode, 42, result.stderr)
        self.assertIn("checks-failed", result.stdout)

    def test_uncommitted_changes_block_push(self):
        self.check.write_text("#!/bin/sh\nexit 0\n")
        result = self.hook()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("commit or stash", result.stderr)

    def test_other_commit_blocks_push(self):
        result = self.hook("1" * 40)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("check out refs/heads/main", result.stderr)

    def test_deletion_skips_checks(self):
        result = self.hook("0" * 40)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("checks-ran", result.stdout)
