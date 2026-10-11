"""Lint for the exactness rules (CLAUDE.md: "Exact money, non-negotiable").

Python (scripts/kalshi_*.py), checked on the AST so comments/docstrings don't count:
  - no float(...) or round(...) calls, no float literals
  - no fixed-precision format specs ({:.2f}, %.2f) anywhere
  - quantize(...) only inside kalshi_rules.py (Kalshi's own documented rounding)
Page (kalshi/index.html app script):
  - no arithmetic or <, > comparisons touching a money field
  - no Number()/parseFloat()/parseInt()/toFixed()/Math.*/.reduce() except on
    lines marked "plot-coordinate" (Chart.js positions), "date-part" (parsing
    "2026-10-11") or "layout" (pixel sizes)
"""

import ast
import glob
import os
import re
import unittest

import kalshi_paths

PY_FORMAT_SPEC = re.compile(r"\{[^{}]*:[^{}]*\.\d+[fFeEgG%][^{}]*\}|%[-+ 0#]*\d*\.\d+[fFeEgG]")
MONEY_FIELDS = (
    "cost|payout|profit|fee|value|pnl|day|amount|net_pnl|account_value|cash|open_value|deposited|credits|"
    "trading_fees|deposit_fees|total_fees|maker_fees|taker_fees|reported|rounding|rebates|realized_pnl|contracts"
)
FIELD = r"\.(?:{})\b(?!\s*\()".format(MONEY_FIELDS)
JS_RULES = [
    ("arithmetic/comparison after a money field", re.compile(FIELD + r"\s*(?:[-+*/%<>]|\+=)(?!=)")),
    ("arithmetic/comparison before a money field", re.compile(r"(?:[-+*/%<>]|\+=)\s*[\w$\]\[]*" + FIELD)),
    ("numeric conversion or math", re.compile(r"\b(?:Number|parseFloat|parseInt)\s*\(|\.toFixed\s*\(|\bMath\.|\.reduce\s*\(")),
]
ALLOWED_MARKERS = ("plot-coordinate", "date-part", "layout")


def python_violations(source, filename):
    problems = []
    tree = ast.parse(source)
    allow_quantize = os.path.basename(filename) == "kalshi_rules.py"
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            name = getattr(node.func, "id", None) or getattr(node.func, "attr", None)
            if name in ("float", "round"):
                problems.append("{}:{} calls {}()".format(filename, node.lineno, name))
            if name == "quantize" and not allow_quantize:
                problems.append("{}:{} calls quantize() outside kalshi_rules.py".format(filename, node.lineno))
        if isinstance(node, ast.Constant) and isinstance(node.value, float):
            problems.append("{}:{} has float literal {!r}".format(filename, node.lineno, node.value))
        if isinstance(node, ast.Constant) and isinstance(node.value, str) and PY_FORMAT_SPEC.search(node.value):
            problems.append("{}:{} has fixed-precision format spec in {!r}".format(filename, node.lineno, node.value[:60]))
        if isinstance(node, ast.FormattedValue) and node.format_spec is not None:
            problems.append("{}:{} has an f-string format spec".format(filename, node.lineno))
    return problems


def app_script(html):
    scripts = re.findall(r"<script>(.*?)</script>", html, re.S)
    return max(scripts, key=len)


def js_violations(script):
    problems = []
    for number, line in enumerate(script.splitlines(), 1):
        code = re.sub(r"//.*$", "", line) if "://" not in line else line
        code = re.sub(r"'(?:[^'\\]|\\.)*'|\"(?:[^\"\\]|\\.)*\"", "''", code)  # ignore string contents
        if any(marker in line for marker in ALLOWED_MARKERS):
            continue
        for label, pattern in JS_RULES:
            if pattern.search(code):
                problems.append("index.html script line {}: {}: {}".format(number, label, line.strip()[:90]))
    return problems


class LintTests(unittest.TestCase):
    def test_python_money_code(self):
        files = sorted(glob.glob(os.path.join(kalshi_paths.SCRIPTS, "kalshi_*.py")))
        self.assertGreaterEqual(len(files), 4)
        problems = []
        for path in files:
            with open(path, encoding="utf-8") as handle:
                problems += python_violations(handle.read(), os.path.basename(path))
        self.assertEqual(problems, [])

    def test_page_does_no_money_arithmetic(self):
        with open(os.path.join(kalshi_paths.REPO, "kalshi", "index.html"), encoding="utf-8") as handle:
            script = app_script(handle.read())
        self.assertEqual(js_violations(script), [])
        self.assertIn("plot-coordinate", script)

    # The lint itself must catch what it claims to.
    def test_lint_catches_python_offenses(self):
        bad = "x = float(text)\ny = round(x, 2)\nz = 0.5\nmsg = '{:.2f}'.format(y)\nw = f'{y:.2f}'\nq = y.quantize(1)\n"
        found = python_violations(bad, "kalshi_common.py")
        self.assertEqual(len(found), 6, found)
        self.assertEqual(python_violations("a = b.quantize(c)\n", "kalshi_rules.py"), [])

    def test_lint_catches_js_offenses(self):
        bad = "\n".join([
            "var diff = bet.payout - bet.cost;",
            "var label = '$' + s.cash;",
            "var n = Number(bet.profit);",
            "var total = rows.reduce(function (a, b) { return a; }, 0);",
            "if (bet.profit > 0) {}",
            "var t = x.toFixed(2);",
        ])
        flagged_lines = {problem.split(":")[0] for problem in js_violations(bad)}
        self.assertEqual(len(flagged_lines), 6, js_violations(bad))  # every bad line, some for two reasons
        fine = "\n".join([
            "setText('x', plain(s.cash) + ' cash');",
            "var y = Number(row.pnl); // plot-coordinate",
            "if (totals.value !== null) {}",
            "row.appendChild(moneyEl('td', 'num', bet.cost, 'plain', field + '.cost'));",
        ])
        self.assertEqual(js_violations(fine), [])


if __name__ == "__main__":
    unittest.main()
