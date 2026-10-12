"""Files that hold credentials or private exports must be ignored by git.

`git check-ignore --no-index` answers "would git ignore this path?" even when
the file doesn't exist, so these tests check the rules, not the disk.
"""

import subprocess
import unittest

import sec_helpers as helpers

MUST_BE_IGNORED = [
    ".env",
    ".env.local",
    "scripts/.env",
    "kalshi/.env",
    "kalshi_private_key.pem",
    "scripts/kalshi.pem",
    "kalshi.key",
    "id_rsa",
    "id_ed25519",
    "Kalshi-Transactions.csv",
    "kalshi/Kalshi-Trades-2026.csv",
    ".claude/settings.local.json",
]

# Public files that must stay publishable (guards against an over-broad ignore rule).
MUST_NOT_BE_IGNORED = [
    "kalshi/data.json",
    "kalshi/index.html",
    "scripts/kalshi_fetch.py",
    ".github/workflows/kalshi.yml",
]


def is_ignored(rel_path):
    helpers.git("--version")  # skips the test cleanly when git/.git is missing
    result = subprocess.run(["git", "-C", helpers.REPO, "check-ignore", "--no-index", "-q", rel_path],
                            capture_output=True, text=True)
    if result.returncode not in (0, 1):
        raise RuntimeError("git check-ignore failed for {}".format(rel_path))
    return result.returncode == 0


class GitignoreTests(unittest.TestCase):
    def test_sensitive_paths_are_ignored(self):
        missing = [path for path in MUST_BE_IGNORED if not is_ignored(path)]
        self.assertEqual(missing, [], "add ignore rules for: {}".format(missing))

    def test_public_files_are_not_ignored(self):
        hidden = [path for path in MUST_NOT_BE_IGNORED if is_ignored(path)]
        self.assertEqual(hidden, [], "these must stay publishable: {}".format(hidden))

    def test_every_must_ignore_example_is_a_sensitive_name(self):
        # Keeps this list and SENSITIVE_NAME_PATTERNS in step with each other.
        for path in MUST_BE_IGNORED:
            with self.subTest(path=path):
                self.assertTrue(any(pattern.search(path) for pattern in helpers.SENSITIVE_NAME_PATTERNS))


if __name__ == "__main__":
    unittest.main()
