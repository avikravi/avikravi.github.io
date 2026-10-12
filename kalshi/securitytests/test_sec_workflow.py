"""GitHub Actions hygiene for .github/workflows/kalshi.yml and scripts/commit_data.sh.

Read as plain text (no YAML library needed). Checks that secrets reach only the
fetch step, through env vars, that nothing untrusted can trigger a run that
has secrets, and that the bot can only ever commit data.json.
"""

import os
import re
import unittest

import sec_helpers as helpers

SECRET_REF = re.compile(r"secrets\.([A-Za-z0-9_]+)")
ALLOWED_SECRETS = {"KALSHI_API_KEY_ID", "KALSHI_PRIVATE_KEY"}


def split_steps(text):
    """Return the workflow's steps as text blocks (each starts at a '- ' list item under steps:)."""
    after = text.split("steps:", 1)[1]
    blocks, current = [], []
    for line in after.splitlines():
        if re.match(r"^\s{6}- ", line) and current:
            blocks.append("\n".join(current))
            current = []
        current.append(line)
    if current:
        blocks.append("\n".join(current))
    # Drop the empty remainder of the "steps:" line itself.
    return [block for block in blocks if block.strip()]


def step_name(block):
    found = re.search(r"name:\s*(.+)", block)
    return found.group(1).strip() if found else block.strip().splitlines()[0]


class WorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(helpers.WORKFLOW, encoding="utf-8") as handle:
            cls.text = handle.read()
        cls.steps = split_steps(cls.text)

    def test_only_schedule_and_manual_triggers(self):
        trigger_block = self.text.split("on:", 1)[1].split("permissions:", 1)[0]
        for risky in ("pull_request", "pull_request_target", "issue_comment", "workflow_run", "push"):
            with self.subTest(trigger=risky):
                self.assertNotRegex(trigger_block, r"\b{}\b".format(risky))

    def test_secrets_only_in_the_fetch_step(self):
        with_secrets = [step_name(block) for block in self.steps if SECRET_REF.search(block)]
        self.assertEqual(with_secrets, ["Fetch from Kalshi API"])

    def test_only_the_two_kalshi_secrets_are_used(self):
        self.assertEqual(set(SECRET_REF.findall(self.text)), ALLOWED_SECRETS)

    def test_secrets_passed_as_env_never_inlined_in_run(self):
        for block in self.steps:
            run_part = block.split("run:", 1)[1] if "run:" in block else ""
            with self.subTest(step=step_name(block)):
                self.assertNotIn("secrets.", run_part)
                self.assertNotRegex(run_part, r"\becho\b.*KALSHI")

    def test_no_debug_logging_switches(self):
        for flag in ("ACTIONS_STEP_DEBUG", "ACTIONS_RUNNER_DEBUG", "set -x", "--verbose-secrets"):
            with self.subTest(flag=flag):
                self.assertNotIn(flag, self.text)

    def test_api_host_not_overridden(self):
        self.assertNotIn("KALSHI_API_HOST", self.text, "signed requests must go to Kalshi's default host")

    def test_permissions_are_minimal(self):
        perms = self.text.split("permissions:", 1)[1].split("\n\n", 1)[0]
        lines = [line.strip() for line in perms.splitlines() if line.strip() and not line.strip().startswith("#")]
        self.assertEqual(lines, ["contents: write"])
        self.assertNotIn("write-all", self.text)

    def test_tests_run_before_secrets_are_used(self):
        names = [step_name(block) for block in self.steps]
        fetch_at = names.index("Fetch from Kalshi API")
        self.assertIn("Run tests", names[:fetch_at])
        self.assertIn("Run security tests", names[:fetch_at])

    def test_checkout_does_not_persist_extra_tokens(self):
        # No personal access token is wired in; the job uses the built-in GITHUB_TOKEN only.
        self.assertNotRegex(self.text, r"token:\s*\$\{\{\s*secrets\.")


class CommitScriptTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(os.path.join(helpers.SCRIPTS, "commit_data.sh"), encoding="utf-8") as handle:
            cls.text = handle.read()

    def test_bot_can_only_commit_data_json(self):
        self.assertIn('DATA_FILE="kalshi/data.json"', self.text)
        add_lines = [line.strip() for line in self.text.splitlines() if re.search(r"\bgit add\b", line)]
        self.assertEqual(add_lines, ['git add "$DATA_FILE"'])
        for broad in ("git add -A", "git add .", "git add --all", "git commit -a", "git commit -am"):
            with self.subTest(command=broad):
                self.assertNotIn(broad, self.text)

    def test_no_shell_tracing(self):
        self.assertNotIn("set -x", self.text)
        self.assertNotRegex(self.text, r"set -[a-z]*x")


if __name__ == "__main__":
    unittest.main()
