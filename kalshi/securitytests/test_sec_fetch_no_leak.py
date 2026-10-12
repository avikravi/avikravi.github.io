"""The fetch script must never print the API key ID, the private key, signatures or response bodies.

The repo is public, so GitHub Actions logs are public too. GitHub masks the
exact secret strings, but not reformatted pieces of them (a PEM split across
lines, a key echoed inside an error body), so the script must not print them
at all. Every test here uses a throwaway key generated at runtime.
"""

import ast
import base64
import contextlib
import io
import os
import subprocess
import sys
import unittest
import uuid

import sec_helpers as helpers

try:
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import ed25519
    import kalshi_fetch
except ImportError as exc:  # requirements.txt not installed
    raise unittest.SkipTest("needs requests + cryptography: {}".format(exc))


def throwaway_key():
    """A fresh Ed25519 key ID + PEM that exist only for this test run."""
    private = ed25519.Ed25519PrivateKey.generate()
    pem = private.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
                                serialization.NoEncryption()).decode()
    return str(uuid.uuid4()), pem


def pem_body_lines(pem):
    """The base64 lines of a PEM: the parts GitHub's masking would miss if printed piecemeal."""
    return [line for line in pem.splitlines() if line and not line.startswith("-----")]


class FakeResponse:
    def __init__(self, status, body):
        self.status_code = status
        self.text = body
        self.content = body.encode()

    def json(self):
        raise ValueError("not json")


class FakeSession:
    """Records requests and answers every GET with a fixed status and a body full of 'secrets'."""

    def __init__(self, status, body):
        self.status = status
        self.body = body
        self.calls = []

    def get(self, url, headers=None, params=None, timeout=None):
        self.calls.append({"url": url, "headers": dict(headers or {}), "params": params})
        return FakeResponse(self.status, self.body)


class ErrorPathTests(unittest.TestCase):
    def setUp(self):
        self.key_id, self.pem = throwaway_key()
        self.client = kalshi_fetch.KalshiClient(self.key_id, self.pem)
        self.body_secret = "BODY-SECRET-" + uuid.uuid4().hex

    def call_and_capture(self, status):
        self.client.session = FakeSession(status, '{"error": "%s", "key": "%s"}' % (self.body_secret, self.key_id))
        out_buf, err_buf = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out_buf), contextlib.redirect_stderr(err_buf):
            with self.assertRaises(SystemExit) as caught:
                self.client.get("/portfolio/balance")
        return str(caught.exception.code) + out_buf.getvalue() + err_buf.getvalue()

    def assert_clean(self, output):
        leaks = []
        if self.key_id in output:
            leaks.append("key ID")
        if self.body_secret in output:
            leaks.append("response body")
        if any(line in output for line in pem_body_lines(self.pem)):
            leaks.append("private key")
        for call in self.client.session.calls:
            signature = call["headers"].get("KALSHI-ACCESS-SIGNATURE", "")
            if signature and signature in output:
                leaks.append("signature")
        self.assertEqual(leaks, [], "printed: {}\noutput was: {!r}".format(leaks, output[:300]))

    def test_http_errors_print_status_and_path_only(self):
        for status in (400, 401, 403, 404, 500, 503):
            with self.subTest(status=status):
                output = self.call_and_capture(status)
                self.assert_clean(output)
                self.assertIn(str(status), output)

    def test_requests_go_to_kalshi_over_https_and_never_carry_the_private_key(self):
        self.call_and_capture(500)
        for call in self.client.session.calls:
            self.assertTrue(call["url"].startswith("https://"), call["url"])
            sent = " ".join(str(value) for value in call["headers"].values()) + str(call["params"])
            self.assertFalse(any(line in sent for line in pem_body_lines(self.pem)))
            # The signature is real base64 (64 bytes for Ed25519), not the key.
            self.assertEqual(len(base64.b64decode(call["headers"]["KALSHI-ACCESS-SIGNATURE"])), 64)

    def test_default_api_host_is_kalshi_https(self):
        if "KALSHI_API_HOST" in os.environ:
            self.skipTest("KALSHI_API_HOST is overridden in this environment")
        self.assertEqual(kalshi_fetch.API_HOST, "https://external-api.kalshi.com")


class WholeScriptTests(unittest.TestCase):
    """Run scripts/kalshi_fetch.py as CI does and read everything it prints."""

    def run_script(self, key_id, pem, host):
        env = dict(os.environ, KALSHI_API_KEY_ID=key_id, KALSHI_PRIVATE_KEY=pem, KALSHI_API_HOST=host)
        result = subprocess.run([sys.executable, os.path.join(helpers.SCRIPTS, "kalshi_fetch.py")],
                                env=env, capture_output=True, text=True, timeout=60, cwd=helpers.REPO)
        return result.returncode, result.stdout + result.stderr

    def test_network_failure_prints_no_secrets(self):
        key_id, pem = throwaway_key()
        # Port 9 on localhost refuses connections immediately: a guaranteed network error.
        code, output = self.run_script(key_id, pem, "https://127.0.0.1:9")
        self.assertNotEqual(code, 0)
        self.assertNotIn(key_id, output)
        self.assertFalse(any(line in output for line in pem_body_lines(pem)), output[:300])
        self.assertNotIn("Traceback", output, "an uncaught traceback could show local values")

    def test_malformed_private_key_is_not_echoed(self):
        key_id = str(uuid.uuid4())
        marker = "NOTAKEY" + uuid.uuid4().hex
        broken_pem = "-----BEGIN " + "PRIVATE KEY-----\n" + marker + "\n-----END " + "PRIVATE KEY-----"
        code, output = self.run_script(key_id, broken_pem, "https://127.0.0.1:9")
        self.assertNotEqual(code, 0)
        self.assertNotIn(marker, output)
        self.assertNotIn(key_id, output)

    def test_missing_secrets_fail_with_a_plain_message(self):
        code, output = self.run_script("", "", "https://127.0.0.1:9")
        self.assertNotEqual(code, 0)
        self.assertIn("must be set", output)


class StaticPrintTests(unittest.TestCase):
    """No print / exit / log call in scripts/kalshi_*.py may mention credential-bearing values."""

    FORBIDDEN_NAMES = {"key_id", "private_key", "private_key_pem", "pem_text", "headers", "signature", "environ"}
    FORBIDDEN_ATTRS = {"text", "content", "headers", "private_key", "key_id", "request", "environ", "json"}
    OUTPUT_CALLS = {"print", "exit", "SystemExit", "write", "debug", "info", "warning", "error",
                    "exception", "critical", "log", "pprint"}

    def call_name(self, node):
        func = node.func
        if isinstance(func, ast.Name):
            return func.id
        if isinstance(func, ast.Attribute):
            return func.attr
        return ""

    def test_output_calls_never_reference_credentials(self):
        problems = []
        script_names = sorted(name for name in os.listdir(helpers.SCRIPTS)
                              if name.startswith("kalshi_") and name.endswith(".py"))
        self.assertIn("kalshi_fetch.py", script_names)
        for script in script_names:
            path = os.path.join(helpers.SCRIPTS, script)
            with open(path, encoding="utf-8") as handle:
                tree = ast.parse(handle.read(), filename=script)
            for node in ast.walk(tree):
                if not (isinstance(node, ast.Call) and self.call_name(node) in self.OUTPUT_CALLS):
                    continue
                for arg in list(node.args) + [kw.value for kw in node.keywords]:
                    for inner in ast.walk(arg):
                        name = inner.id if isinstance(inner, ast.Name) else None
                        attr = inner.attr if isinstance(inner, ast.Attribute) else None
                        if name in self.FORBIDDEN_NAMES or attr in self.FORBIDDEN_ATTRS:
                            problems.append("{}:{} {}() uses {}".format(
                                script, node.lineno, self.call_name(node), name or attr))
        self.assertEqual(problems, [], "\n".join(problems))

    def test_static_check_catches_a_planted_leak(self):
        tree = ast.parse("print('debug', resp.text)\nraise SystemExit(headers)")
        hits = 0
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and self.call_name(node) in self.OUTPUT_CALLS:
                for arg in node.args:
                    for inner in ast.walk(arg):
                        if (isinstance(inner, ast.Name) and inner.id in self.FORBIDDEN_NAMES) or \
                           (isinstance(inner, ast.Attribute) and inner.attr in self.FORBIDDEN_ATTRS):
                            hits += 1
        self.assertEqual(hits, 2)


if __name__ == "__main__":
    unittest.main()
