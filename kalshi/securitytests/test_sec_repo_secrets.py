"""No credentials anywhere in the repo: current files, untracked files, or git history.

The repo is public, so anything committed (even later deleted) is readable by
anyone. Failures report the file, line and pattern name, never the secret.
"""

import unittest

import sec_helpers as helpers


class SecretPatternSelfTests(unittest.TestCase):
    """The detectors must actually detect. Fake secrets are built at runtime, never stored."""

    def test_each_pattern_catches_a_fake_secret(self):
        fakes = {
            "PEM private key block": "-----BEGIN " + "RSA PRIVATE KEY" + "-----\nMIIEow...",
            "Kalshi key assigned a literal value": "KALSHI_PRIVATE_KEY=" + "abcd1234efgh5678",
            "UUID (Kalshi API key IDs and order IDs are UUIDs)": "-".join(["a1b2c3d4", "e5f6", "a7b8", "c9d0", "e1f2a3b4c5d6"]),
            "AWS access key": "AKIA" + "ABCDEFGHIJKLMNOP",
            "GitHub token": "ghp" + "_" + "a" * 36,
            "Google API key": "AIza" + "b" * 35,
            "OpenAI / Anthropic key": "sk-" + "ant-" + "c" * 30,
            "Slack token": "xox" + "b-" + "1234567890-abc",
            "Password with a literal value": "password = " + "'hunter22'",
        }
        self.assertEqual(set(fakes), set(helpers.SECRET_PATTERNS), "every pattern needs a fake here")
        for name, fake in fakes.items():
            with self.subTest(pattern=name):
                self.assertIn(name, [hit[0] for hit in helpers.find_secrets(fake)])

    def test_safe_lookalikes_are_not_flagged(self):
        safe = [
            "KALSHI_PRIVATE_KEY: ${{ secrets.KALSHI_PRIVATE_KEY }}",   # workflow reference, not a value
            "serialization.load_pem_private_key(pem_text, password=None)",
            "the full PEM private key (RSA or Ed25519)",
            "Romeo Doubs: 40+ receiving yards",
        ]
        for text in safe:
            with self.subTest(text=text):
                self.assertEqual(helpers.find_secrets(text), [])


class CurrentFilesTests(unittest.TestCase):
    def test_no_secrets_in_tracked_or_untracked_files(self):
        problems = []
        for rel_path in helpers.repo_files(include_untracked=True):
            text = helpers.read_text(rel_path)
            if text is None:
                continue
            for name, line in helpers.find_secrets(text):
                problems.append("{}:{} ({})".format(rel_path, line, name))
        self.assertEqual(problems, [], "possible secrets found:\n" + "\n".join(problems))

    def test_no_sensitive_file_names_tracked(self):
        tracked = helpers.repo_files(include_untracked=True)
        bad = [name for name in tracked
               if any(pattern.search(name) for pattern in helpers.SENSITIVE_NAME_PATTERNS)]
        self.assertEqual(bad, [], "sensitive files are tracked or about to be: {}".format(bad))


class HistoryTests(unittest.TestCase):
    """Deleted secrets stay in git history forever unless the history is rewritten.

    In CI the checkout is shallow (one commit), so this mostly protects local runs,
    which see the full history.
    """

    def test_no_private_key_or_token_ever_committed(self):
        regex = "|".join([
            "-----BEGIN " + "[A-Z ]*PRIVATE KEY",
            r"AKIA[0-9A-Z]{16}",
            r"gh[pousr]_[A-Za-z0-9]{30,}",
            r"github_pat_[A-Za-z0-9_]{30,}",
            r"sk-ant-[A-Za-z0-9_-]{20,}",
            r"AIza[0-9A-Za-z_-]{35}",
        ])
        commits = helpers.git("log", "--all", "--format=%h", "-G", regex).split()
        self.assertEqual(commits, [], "commits that added or removed a key/token: {}".format(commits))

    def test_no_uuid_ever_committed(self):
        regex = r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}"
        commits = helpers.git("log", "--all", "--format=%h", "-G", regex).split()
        self.assertEqual(commits, [], "commits containing a UUID (API key ID / order ID?): {}".format(commits))

    def test_no_sensitive_file_ever_committed(self):
        names = set(helpers.git("log", "--all", "--name-only", "--format=").split("\n"))
        bad = sorted(name for name in names if name and any(
            pattern.search(name) for pattern in helpers.SENSITIVE_NAME_PATTERNS))
        self.assertEqual(bad, [], "sensitive files appear in git history: {}".format(bad))


if __name__ == "__main__":
    unittest.main()
