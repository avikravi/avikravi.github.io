"""Mutation check: reintroduce the two classic money bugs and prove the suite catches them.

For each mutation, scripts/ is copied to a temp folder, one line is broken,
and the behavioral suite (golden + identity + round-trip tests) and the lint
are run against the broken copy in a subprocess (KALSHI_SCRIPTS_DIR). Both
must fail. The real scripts are never touched.
"""

import os
import shutil
import subprocess
import sys
import tempfile
import unittest

import kalshi_paths

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))

MUTATIONS = {
    # 1. Parse money through float instead of straight from the string.
    "float() on parse": (
        "kalshi_common.py",
        'return Decimal(value) if isinstance(value, int) else Decimal(str(value).strip())',
        'return Decimal(value) if isinstance(value, int) else Decimal(float(str(value).strip()))',
    ),
    # 2. Round stored amounts to 2 decimals.
    "2-decimal rounding on store": (
        "kalshi_common.py",
        'text = format(value, "f")',
        'text = format(value.quantize(Decimal("0.01")), "f")',
    ),
}


def run_suite(scripts_dir, module):
    env = dict(os.environ, KALSHI_SCRIPTS_DIR=scripts_dir, PYTHONDONTWRITEBYTECODE="1")
    return subprocess.run([sys.executable, "-m", "unittest", module], cwd=TESTS_DIR, env=env,
                          capture_output=True, text=True, timeout=300)


class MutationTests(unittest.TestCase):
    def check_caught(self, name):
        filename, original, broken = MUTATIONS[name]
        folder = tempfile.mkdtemp(prefix="kalshi-mutant-")
        try:
            copy = os.path.join(folder, "scripts")
            shutil.copytree(kalshi_paths.SCRIPTS, copy, ignore=shutil.ignore_patterns("__pycache__"))
            path = os.path.join(copy, filename)
            with open(path, encoding="utf-8") as handle:
                source = handle.read()
            self.assertEqual(source.count(original), 1, "mutation target moved: update MUTATIONS[{!r}]".format(name))
            with open(path, "w", encoding="utf-8") as handle:
                handle.write(source.replace(original, broken))

            behavior = run_suite(copy, "test_kalshi_exact")
            lint = run_suite(copy, "test_kalshi_lint")
            self.assertNotEqual(behavior.returncode, 0, name + ": behavioral tests did NOT catch it")
            self.assertNotEqual(lint.returncode, 0, name + ": lint did NOT catch it")
            return behavior.stderr.strip().splitlines()[-1], lint.stderr.strip().splitlines()[-1]
        finally:
            shutil.rmtree(folder, ignore_errors=True)

    def test_float_parse_is_caught(self):
        self.check_caught("float() on parse")

    def test_two_decimal_rounding_is_caught(self):
        self.check_caught("2-decimal rounding on store")

    def test_unmutated_copy_passes(self):
        # Control: the same harness on an untouched copy must pass, so the
        # failures above really come from the mutations.
        folder = tempfile.mkdtemp(prefix="kalshi-control-")
        try:
            copy = os.path.join(folder, "scripts")
            shutil.copytree(kalshi_paths.SCRIPTS, copy, ignore=shutil.ignore_patterns("__pycache__"))
            self.assertEqual(run_suite(copy, "test_kalshi_exact").returncode, 0)
            self.assertEqual(run_suite(copy, "test_kalshi_lint").returncode, 0)
        finally:
            shutil.rmtree(folder, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
